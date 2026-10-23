"""Signed offline study packs and exactly-once, caller-owned completion upload.

Rollout requires prepared source_session_id and OfflineCompletion schema migrations.
Offline practice never creates or completes a timed/master examination.
"""
import base64
import json
import uuid
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.views import APIView

from apps.core.permissions import HasCapability
from apps.core.fingerprints import json_fingerprint
from apps.questions.answer_visibility import closed_book_question_ids, require_answers_available
from .offline_observability import OfflineOperationLoggingMixin
from apps.core.utils import api_error, api_success, parse_csv_param
from apps.learning.evidence import question_learning_fingerprint, with_locked_learning_content
from apps.questions.models import Question
from apps.questions.filters import filter_questions
from apps.questions.payloads import build_grading_snapshot
from apps.users.models import User
from ..models import TestHistory, ExamSession, OfflineCompletion
from ..services import ExamService

SALT = 'mukhtabir.offline-study.v1'
MAX_PACK_BYTES = 4 * 1024 * 1024
MAX_IMAGE_BYTES = 1024 * 1024


class PackRequest(serializers.Serializer):
    full_bank = serializers.BooleanField(default=False)
    include_images = serializers.BooleanField(default=True)
    question_ids = serializers.ListField(child=serializers.IntegerField(min_value=1, max_value=2**63 - 1), allow_empty=False)

    def validate_question_ids(self, value):
        maximum = min(getattr(settings, 'MAX_QUIZ_QUESTIONS', 200), 200)
        if len(value) > maximum or len(set(value)) != len(value):
            raise serializers.ValidationError('عدد أسئلة غير صالح أو معرّفات مكررة')
        return value


class OfflineAnswer(serializers.Serializer):
    question_id = serializers.IntegerField(min_value=1)
    answer = serializers.IntegerField(min_value=1)
    confidence = serializers.IntegerField(min_value=1, max_value=3)
    answered_at = serializers.DateTimeField(required=False)


class CompletionRequest(serializers.Serializer):
    completion_id = serializers.UUIDField()
    token = serializers.CharField(max_length=MAX_PACK_BYTES * 2, trim_whitespace=False)
    answers = OfflineAnswer(many=True, allow_empty=False)
    time_spent = serializers.IntegerField(min_value=0, max_value=7 * 24 * 60 * 60)
    occurred_at = serializers.DateTimeField(required=False)

    def validate_answers(self, value):
        if len(value) > 200 or len({row['question_id'] for row in value}) != len(value):
            raise serializers.ValidationError('إجابات غير صالحة أو مكررة')
        return value


def _error(request, message, status, reason, *, details=None):
    request._offline_reason = reason
    return api_error(message, status, details=details, reason=reason)


def _closed(request, rows, *, user=None, fresh=False):
    hidden = closed_book_question_ids(user or request.user, request=None if fresh else request)
    return any(row.pk in hidden for row in rows)


def _pack_snapshot_locked(request, ids, full_bank):
    """Caller holds atomic; lock user/content consistently, but do no storage IO."""
    user = User.objects.select_for_update().filter(pk=request.user.pk).first()
    if user is None or not user.is_active or user.is_expired:
        return None, None, _error(request, 'ليس لديك صلاحية لهذا الإجراء.', 403, 'ACCOUNT_UNAVAILABLE')
    bank_allowed = user.has_capability('tests.download_full_bank')
    if not user.has_capability('tests.start') or (full_bank and not bank_allowed):
        return None, None, _error(request, 'ليس لديك صلاحية لهذا الإجراء.', 403, 'PERMISSION_DENIED')
    from apps.learning.models import OfflineQuestionGrant
    grants = OfflineQuestionGrant.objects.filter(user=user)
    existing = set(grants.filter(question_id_snapshot__in=ids).values_list('question_id_snapshot', flat=True))
    maximum_selected = max(1, int(getattr(settings, 'OFFLINE_SELECTED_QUESTION_LIMIT', 200)))
    if not bank_allowed and grants.count() + len(set(ids) - existing) > maximum_selected:
        return None, None, _error(request, 'وصلت إلى حد الأسئلة المنزلة. اطلب صلاحية تنزيل البنك كاملًا.', 403,
                                 'DOWNLOAD_LIMIT', details={'reason': 'OFFLINE_DOWNLOAD_LIMIT', 'limit': maximum_selected})
    rows = list(with_locked_learning_content(Question.objects.visible_to(user)
        .select_for_update().filter(id__in=ids).order_by('pk')).prefetch_related('category', 'tags'))
    if len(rows) != len(ids):
        return None, None, _error(request, 'بعض الأسئلة غير متاحة', 404, 'QUESTION_UNAVAILABLE')
    if _closed(request, rows, user=user, fresh=True):
        return None, None, _error(request, 'لا يمكن تنزيل إجابات أسئلة امتحان غير مكتمل', 409, 'ANSWERS_WITHHELD')
    return build_grading_snapshot(ids, questions=rows), existing, None


class OfflineCatalogQuery(serializers.Serializer):
    after = serializers.IntegerField(min_value=0, default=0)
    upper_bound = serializers.IntegerField(min_value=0, required=False)
    source_document = serializers.CharField(required=False, max_length=1000, trim_whitespace=False)
    category_ids = serializers.CharField(required=False, allow_blank=True, default=list, max_length=4400)
    tags_filter = serializers.CharField(required=False, default=list, max_length=16000)

    def validate_category_ids(self, value):
        try:
            ids = [int(part) for part in parse_csv_param(value)]
        except ValueError:
            raise serializers.ValidationError('تصنيفات غير صالحة')
        if len(ids) > 200 or len(ids) != len(set(ids)) or any(item <= 0 or item > 2**63 - 1 for item in ids):
            raise serializers.ValidationError('تصنيفات غير صالحة')
        return ids

    def validate_tags_filter(self, value):
        if value == []:
            return []  # The optional field's parsed default; no tag restriction.
        try:
            tags = json.loads(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError('وسوم غير صالحة')
        if not isinstance(tags, list) or len(tags) > 200 or any(not isinstance(tag, str) or not tag.strip() for tag in tags):
            raise serializers.ValidationError('وسوم غير صالحة')
        return tags


class OfflineCatalogView(OfflineOperationLoggingMixin, APIView):
    """Caller-visible IDs, keyset-paged for explicit full-bank offline download.

    The fixed upper ID bounds additions, not edits/deletions or a database snapshot.
    Pack generation rechecks access, grading readiness and closed-book restrictions.
    """
    permission_classes = [HasCapability]
    required_capability = 'tests.download_full_bank'

    def get(self, request):
        if not request.user.has_capability('tests.start'):
            return _error(request, 'ليس لديك صلاحية لهذا الإجراء.', 403, 'PERMISSION_DENIED')
        query = OfflineCatalogQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        values = query.validated_data
        visible = filter_questions(Question.objects.visible_to(request.user), values,
                                   hidden_answer_ids=closed_book_question_ids(request.user, request=request))
        upper = values.get('upper_bound')
        if upper is None:
            upper = visible.order_by('-pk').values_list('pk', flat=True).first() or 0
        maximum = max(1, min(getattr(settings, 'MAX_QUIZ_QUESTIONS', 200), 200))
        bounded = visible.filter(pk__lte=upper)
        rows = list(bounded.filter(pk__gt=values['after']).order_by('pk').only('pk')[:maximum + 1])
        page = rows[:maximum]
        hidden = closed_book_question_ids(request.user, request=request)
        ids = [row.pk for row in page if row.pk not in hidden]
        return api_success(data={
            'question_ids': ids,
            'upper_bound': upper,
            'next_after': page[-1].pk if len(rows) > maximum else None,
            'total': bounded.count(),
            'excluded': len(page) - len(ids),
            'selection': {'book': values.get('source_document'),
                          'categories': values['category_ids'], 'tags': values['tags_filter']},
        })


class OfflinePackView(OfflineOperationLoggingMixin, APIView):
    permission_classes = [HasCapability]
    required_capability = 'tests.start'

    def post(self, request):
        body = PackRequest(data=request.data)
        body.is_valid(raise_exception=True)
        full_bank = body.validated_data['full_bank']
        ids = body.validated_data['question_ids']
        # Freeze assessed relations under short locks, then release before IO.
        with transaction.atomic():
            snapshots, _, rejection = _pack_snapshot_locked(request, ids, full_bank)
            if rejection is not None:
                return rejection

        questions = []
        images = {}
        image_ids = []
        material_bytes = 0
        try:
            for qid in ids:
                snap = snapshots[str(qid)]
                if snap['correct_answer'] not in range(1, len(snap.get('choices') or []) + 1):
                    return _error(request, 'السؤال غير جاهز للتدريب دون اتصال', 409, 'QUESTION_NOT_READY')
                questions.append({
                    'id': qid, 'question': snap['question'], 'choices': snap['choices'],
                    'correct_answer': snap['correct_answer'], 'explanation': snap['explanation'],
                    'translations': snap['translations'], 'case': snap['case'],
                    'category': snap['category_id'], 'category_name': snap['category_name'],
                    'category_color': snap['category_color'], 'difficulty': snap['difficulty'],
                    'tags': snap['tag_names'],
                })
                material_bytes += len(json.dumps(questions[-1], ensure_ascii=False).encode('utf-8'))
                if snap.get('image_name'):
                    image_ids.append(qid)
                if snap.get('image_name') and body.validated_data['include_images']:
                    storage = Question._meta.get_field('image').storage
                    with storage.open(snap['image_name'], 'rb') as image:
                        content = image.read(MAX_IMAGE_BYTES + 1)
                    if len(content) > MAX_IMAGE_BYTES:
                        return _error(request, 'صورة كبيرة للتنزيل دون اتصال', 400, 'IMAGE_TOO_LARGE')
                    images[str(qid)] = base64.b64encode(content).decode('ascii')
                    material_bytes += len(images[str(qid)])
                if material_bytes > MAX_PACK_BYTES:
                    return _error(request, 'التنزيل كبير جدًا، اختر أسئلة أقل', 400, 'PACK_TOO_LARGE')
        except (OSError, ValueError, KeyError) as failure:
            request._offline_failure_type = type(failure).__name__
            return _error(request, 'تعذّر تجهيز المواد دون اتصال', 409, 'MATERIAL_PREPARATION_FAILED')
        issued_at = timezone.now().isoformat()
        payload = {'schema': 1, 'issued_at': issued_at, 'user_id': request.user.pk, 'pack_id': str(uuid.uuid4()),
                   'question_ids': ids, 'snapshots': snapshots}
        token = signing.dumps(payload, salt=SALT, compress=True)
        revision = json_fingerprint(snapshots, ensure_ascii=False)
        data = {'id': payload['pack_id'], 'issued_at': issued_at, 'token': token, 'questions': questions, 'images': images,
                'image_question_ids': image_ids, 'images_included': body.validated_data['include_images'],
                'content_revision': revision}
        if len(json.dumps(data, ensure_ascii=False).encode('utf-8')) > MAX_PACK_BYTES:
            return _error(request, 'التنزيل كبير جدًا، اختر أسئلة أقل', 400, 'PACK_TOO_LARGE')

        # Recheck all authority/content/quota after preparation; grants commit
        # only for the material actually returned. No file work under these locks.
        with transaction.atomic():
            current, existing, rejection = _pack_snapshot_locked(request, ids, full_bank)
            if rejection is not None:
                return rejection
            if current != snapshots:
                return _error(request, 'تغيّرت المواد أثناء تجهيز التنزيل، أعد المحاولة.', 409, 'PACK_CONTENT_CHANGED')
            from apps.learning.models import OfflineQuestionGrant
            OfflineQuestionGrant.objects.bulk_create([
                OfflineQuestionGrant(user=request.user, question_id_snapshot=qid) for qid in ids if qid not in existing
            ])
        return api_success(data=data)


class OfflineCompletionView(OfflineOperationLoggingMixin, APIView):
    permission_classes = [HasCapability]
    required_capability = 'tests.start'

    def post(self, request):
        body = CompletionRequest(data=request.data)
        body.is_valid(raise_exception=True)
        values = body.validated_data
        request._offline_completion_reference = json_fingerprint(str(values['completion_id']))[:16]
        try:
            # No expiry: a persisted completion remains recoverable after a lost response.
            # Content/access are rechecked before the first commit; secret rotation invalidates packs.
            pack = signing.loads(values['token'], salt=SALT)
        except signing.BadSignature:
            return _error(request, 'حزمة التدريب غير صالحة، أعد التنزيل', 400, 'INVALID_PACK_SIGNATURE')
        if pack.get('schema') != 1 or pack.get('user_id') != request.user.pk:
            return _error(request, 'حزمة التدريب غير متاحة', 404, 'PACK_NOT_OWNED')
        ids = pack['question_ids']
        answers = values['answers']
        if len(answers) != len(ids) or {row['question_id'] for row in answers} != set(ids):
            return _error(request, 'يجب إنهاء كل أسئلة التدريب قبل المزامنة', 400, 'INCOMPLETE_ANSWERS')
        if any(row['answer'] > len(pack['snapshots'][str(row['question_id'])]['choices']) for row in answers):
            return _error(request, 'إجابة غير صالحة', 400, 'INVALID_ANSWER')
        if any(row.get('answered_at') for row in answers) and 'occurred_at' not in values:
            return _error(request, 'وقت إكمال التدريب مطلوب.', 400, 'COMPLETION_TIME_REQUIRED')
        identity = str(values['completion_id'])
        receipt_body = {
            'pack_id': pack['pack_id'], 'answers': sorted([{key: value.isoformat() if key == 'answered_at' else value for key, value in row.items()} for row in answers], key=lambda row: row['question_id']),
            'time_spent': values['time_spent'],
        }
        if 'occurred_at' in values:
            receipt_body['occurred_at'] = values['occurred_at'].isoformat()
        fingerprint = json_fingerprint(receipt_body, separators=(',', ':'))
        try:
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=request.user.pk)
                prior = OfflineCompletion.objects.filter(completion_id=identity).first()
                if prior:
                    if prior.user_id != user.pk or prior.request_fingerprint != fingerprint:
                        return _error(request, 'تعارض معرّف المزامنة', 409, 'RECEIPT_CONFLICT')
                    require_answers_available(user, ids)
                    request._offline_reason = 'RECEIPT_REPLAY'
                    return api_success(data=prior.response)
                received_now = timezone.now()
                occurred_at = values.get('occurred_at', received_now)
                if 'occurred_at' in values:
                    from django.utils.dateparse import parse_datetime
                    issued = parse_datetime(pack.get('issued_at', ''))
                    if issued is None or issued > received_now or occurred_at < issued or occurred_at > received_now + timedelta(minutes=5):
                        return _error(request, 'وقت التدريب خارج حدود الحزمة. تحقق من ساعة الجهاز.', 400, 'INVALID_COMPLETION_TIME',
                                         details={'occurred_at': ['Invalid offline learning time.']})
                    if any(row.get('answered_at') and (row['answered_at'] < issued or row['answered_at'] > occurred_at) for row in answers):
                        return _error(request, 'أوقات الإجابات غير صالحة.', 400, 'INVALID_ANSWER_TIME')
                    occurred_at = min(occurred_at, received_now)
                if TestHistory.objects.filter(source_session_id=identity).exists() or ExamSession.objects.filter(session_id=identity).exists():
                    return _error(request, 'تعارض معرّف المزامنة', 409, 'SESSION_ID_CONFLICT')
                rows = list(with_locked_learning_content(Question.objects.visible_to(user)
                    .select_for_update().filter(id__in=ids).order_by('pk')).prefetch_related('category', 'tags'))
                if len(rows) != len(ids):
                    return _error(request, 'بعض الأسئلة لم تعد متاحة، احتفظ بالنتائج محليًا', 409, 'QUESTION_UNAVAILABLE')
                if _closed(request, rows, user=user, fresh=True):
                    return _error(request, 'أكمل الامتحان الجاري قبل مزامنة هذه الأسئلة', 409, 'ANSWERS_WITHHELD')
                if any(question_learning_fingerprint(row) != pack['snapshots'][str(row.pk)]['learning_fingerprint'] for row in rows):
                    return _error(request, 'تغيّرت الأسئلة، احتفظ بالنتائج محليًا وأعد التنزيل للتدريب الجديد', 409, 'LEARNING_CONTENT_CHANGED')
                indexed = {row['question_id']: row for row in answers}
                slots = {str(index): {'answer': indexed[qid]['answer'], 'confidence': indexed[qid]['confidence'],
                    'answered_at': min(indexed[qid]['answered_at'], occurred_at).isoformat() if indexed[qid].get('answered_at') and pack.get('issued_at') else None}
                    for index, qid in enumerate(ids)}
                graded = ExamService.grade_exam(ids, slots, question_snapshots=pack['snapshots'])
                ExamService.record_completion_side_effects(user, graded['questions'],
                    source_key=f'offline:{identity}', occurred_at=occurred_at)
                history = ExamService.save_history(user, 'study', 'Offline practice',
                    graded['total_questions'], graded['answered_count'], graded['correct_count'],
                    graded['accuracy'], values['time_spent'], occurred_at - timedelta(seconds=values['time_spent']), graded['questions'],
                    source_session_id=identity, completed_at=occurred_at)
                result = ExamService.completed_result(history)
                OfflineCompletion.objects.create(completion_id=identity, user=user,
                    request_fingerprint=fingerprint, response=result)
        except IntegrityError:
            # The failed atomic block has rolled back. Only observed identity
            # collisions are conflicts; other constraint failures must propagate.
            prior = OfflineCompletion.objects.filter(completion_id=identity).first()
            if prior is not None:
                if prior.user_id == request.user.pk and prior.request_fingerprint == fingerprint:
                    require_answers_available(request.user, ids)
                    request._offline_reason = 'RECEIPT_REPLAY'
                    return api_success(data=prior.response)
                return _error(request, 'تعارض معرّف المزامنة', 409, 'RECEIPT_CONFLICT')
            if (TestHistory.objects.filter(source_session_id=identity).exists()
                    or ExamSession.objects.filter(session_id=identity).exists()):
                return _error(request, 'تعارض معرّف المزامنة', 409, 'SESSION_ID_CONFLICT')
            raise
        return api_success(data=result)
