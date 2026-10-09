"""Signed offline study packs and exactly-once, caller-owned completion upload.

Rollout requires prepared source_session_id and OfflineCompletion schema migrations.
Offline practice never creates or completes a timed/master examination.
"""
import base64
import hashlib
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
from apps.core.utils import api_error, api_success
from apps.learning.evidence import question_learning_fingerprint, with_locked_learning_content
from apps.questions.models import Question
from apps.questions.payloads import build_grading_snapshot
from apps.questions.serializers import QuestionSerializer
from apps.users.models import User
from ..models import TestHistory, ExamSession, OfflineCompletion
from ..services import ExamService

SALT = 'mukhtabir.offline-study.v1'
MAX_PACK_BYTES = 4 * 1024 * 1024
MAX_IMAGE_BYTES = 1024 * 1024


class PackRequest(serializers.Serializer):
    full_bank = serializers.BooleanField(default=False)
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


def _closed(request, rows):
    serializer = QuestionSerializer(context={'request': request})
    return any(serializer.get_answers_hidden(row) for row in rows)


class OfflineCatalogQuery(serializers.Serializer):
    after = serializers.IntegerField(min_value=0, default=0)
    upper_bound = serializers.IntegerField(min_value=0, required=False)


class OfflineCatalogView(APIView):
    """Caller-visible IDs, keyset-paged for explicit full-bank offline download.

    The fixed upper ID bounds additions, not edits/deletions or a database snapshot.
    Pack generation rechecks access, grading readiness and closed-book restrictions.
    """
    permission_classes = [HasCapability]
    required_capability = 'tests.download_full_bank'

    def get(self, request):
        if not request.user.has_capability('tests.start'):
            return api_error('ليس لديك صلاحية لهذا الإجراء.', 403)
        query = OfflineCatalogQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        values = query.validated_data
        visible = Question.objects.visible_to(request.user)
        upper = values.get('upper_bound')
        if upper is None:
            upper = visible.order_by('-pk').values_list('pk', flat=True).first() or 0
        maximum = max(1, min(getattr(settings, 'MAX_QUIZ_QUESTIONS', 200), 200))
        bounded = visible.filter(pk__lte=upper)
        rows = list(bounded.filter(pk__gt=values['after']).order_by('pk').only('pk')[:maximum + 1])
        page = rows[:maximum]
        serializer = QuestionSerializer(context={'request': request})
        ids = [row.pk for row in page if not serializer.get_answers_hidden(row)]
        return api_success(data={
            'question_ids': ids,
            'upper_bound': upper,
            'next_after': page[-1].pk if len(rows) > maximum else None,
            'total': bounded.count(),
            'excluded': len(page) - len(ids),
        })


class OfflinePackView(APIView):
    permission_classes = [HasCapability]
    required_capability = 'tests.start'

    def post(self, request):
        body = PackRequest(data=request.data)
        body.is_valid(raise_exception=True)
        if body.validated_data['full_bank'] and not request.user.has_capability('tests.download_full_bank'):
            return api_error('ليس لديك صلاحية لتنزيل بنك الأسئلة كاملًا.', 403)
        ids = body.validated_data['question_ids']
        with transaction.atomic():
            User.objects.select_for_update().only('id').get(pk=request.user.pk)
            from apps.learning.models import OfflineQuestionGrant
            grants = OfflineQuestionGrant.objects.filter(user=request.user)
            existing = set(grants.filter(question_id_snapshot__in=ids).values_list('question_id_snapshot', flat=True))
            maximum_selected = max(1, int(getattr(settings, 'OFFLINE_SELECTED_QUESTION_LIMIT', 200)))
            if not request.user.has_capability('tests.download_full_bank') and grants.count() + len(set(ids) - existing) > maximum_selected:
                return api_error('وصلت إلى حد الأسئلة المنزلة. اطلب صلاحية تنزيل البنك كاملًا.', 403,
                                 details={'reason': 'OFFLINE_DOWNLOAD_LIMIT', 'limit': maximum_selected})
            rows = list(with_locked_learning_content(Question.objects.visible_to(request.user)
                .select_for_update().filter(id__in=ids).order_by('pk')).prefetch_related('category', 'tags'))
            if len(rows) != len(ids):
                return api_error('بعض الأسئلة غير متاحة', 404)
            if _closed(request, rows):
                return api_error('لا يمكن تنزيل إجابات أسئلة امتحان غير مكتمل', 409)
            snapshots = build_grading_snapshot(ids)
            questions = []
            images = {}
            material_bytes = 0
            try:
                for qid in ids:
                    snap = snapshots[str(qid)]
                    if snap['correct_answer'] not in range(1, len(snap.get('choices') or []) + 1):
                        return api_error('السؤال غير جاهز للتدريب دون اتصال', 409)
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
                        storage = Question._meta.get_field('image').storage
                        with storage.open(snap['image_name'], 'rb') as image:
                            content = image.read(MAX_IMAGE_BYTES + 1)
                        if len(content) > MAX_IMAGE_BYTES:
                            return api_error('صورة كبيرة للتنزيل دون اتصال', 400)
                        images[str(qid)] = base64.b64encode(content).decode('ascii')
                        material_bytes += len(images[str(qid)])
                    if material_bytes > MAX_PACK_BYTES:
                        return api_error('التنزيل كبير جدًا، اختر أسئلة أقل', 400)
            except (OSError, ValueError, KeyError):
                return api_error('تعذّر تجهيز المواد دون اتصال', 409)
            issued_at = timezone.now().isoformat()
            payload = {'schema': 1, 'issued_at': issued_at, 'user_id': request.user.pk, 'pack_id': str(uuid.uuid4()),
                       'question_ids': ids, 'snapshots': snapshots}
            token = signing.dumps(payload, salt=SALT, compress=True)
            data = {'id': payload['pack_id'], 'issued_at': issued_at, 'token': token, 'questions': questions, 'images': images}
            if len(json.dumps(data, ensure_ascii=False).encode('utf-8')) > MAX_PACK_BYTES:
                return api_error('التنزيل كبير جدًا، اختر أسئلة أقل', 400)
            OfflineQuestionGrant.objects.bulk_create([
                OfflineQuestionGrant(user=request.user, question_id_snapshot=qid) for qid in ids if qid not in existing
            ])
        return api_success(data=data)


class OfflineCompletionView(APIView):
    permission_classes = [HasCapability]
    required_capability = 'tests.start'

    def post(self, request):
        body = CompletionRequest(data=request.data)
        body.is_valid(raise_exception=True)
        values = body.validated_data
        try:
            # No expiry: a persisted completion remains recoverable after a lost response.
            # Content/access are rechecked before the first commit; secret rotation invalidates packs.
            pack = signing.loads(values['token'], salt=SALT)
        except signing.BadSignature:
            return api_error('حزمة التدريب غير صالحة، أعد التنزيل', 400)
        if pack.get('schema') != 1 or pack.get('user_id') != request.user.pk:
            return api_error('حزمة التدريب غير متاحة', 404)
        ids = pack['question_ids']
        answers = values['answers']
        if len(answers) != len(ids) or {row['question_id'] for row in answers} != set(ids):
            return api_error('يجب إنهاء كل أسئلة التدريب قبل المزامنة', 400)
        if any(row['answer'] > len(pack['snapshots'][str(row['question_id'])]['choices']) for row in answers):
            return api_error('إجابة غير صالحة', 400)
        if any(row.get('answered_at') for row in answers) and 'occurred_at' not in values:
            return api_error('وقت إكمال التدريب مطلوب.', 400)
        identity = str(values['completion_id'])
        receipt_body = {
            'pack_id': pack['pack_id'], 'answers': sorted([{key: value.isoformat() if key == 'answered_at' else value for key, value in row.items()} for row in answers], key=lambda row: row['question_id']),
            'time_spent': values['time_spent'],
        }
        if 'occurred_at' in values:
            receipt_body['occurred_at'] = values['occurred_at'].isoformat()
        fingerprint = hashlib.sha256(json.dumps(receipt_body, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        try:
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=request.user.pk)
                prior = OfflineCompletion.objects.filter(completion_id=identity).first()
                if prior:
                    if prior.user_id != user.pk or prior.request_fingerprint != fingerprint:
                        return api_error('تعارض معرّف المزامنة', 409)
                    return api_success(data=prior.response)
                received_now = timezone.now()
                occurred_at = values.get('occurred_at', received_now)
                if 'occurred_at' in values:
                    from django.utils.dateparse import parse_datetime
                    issued = parse_datetime(pack.get('issued_at', ''))
                    if issued is None or issued > received_now or occurred_at < issued or occurred_at > received_now + timedelta(minutes=5):
                        return api_error('وقت التدريب خارج حدود الحزمة. تحقق من ساعة الجهاز.', 400,
                                         details={'occurred_at': ['Invalid offline learning time.']})
                    if any(row.get('answered_at') and (row['answered_at'] < issued or row['answered_at'] > occurred_at) for row in answers):
                        return api_error('أوقات الإجابات غير صالحة.', 400)
                    occurred_at = min(occurred_at, received_now)
                if TestHistory.objects.filter(source_session_id=identity).exists() or ExamSession.objects.filter(session_id=identity).exists():
                    return api_error('تعارض معرّف المزامنة', 409)
                rows = list(with_locked_learning_content(Question.objects.visible_to(user)
                    .select_for_update().filter(id__in=ids).order_by('pk')).prefetch_related('category', 'tags'))
                if len(rows) != len(ids):
                    return api_error('بعض الأسئلة لم تعد متاحة، احتفظ بالنتائج محليًا', 409)
                if _closed(request, rows):
                    return api_error('أكمل الامتحان الجاري قبل مزامنة هذه الأسئلة', 409)
                if any(question_learning_fingerprint(row) != pack['snapshots'][str(row.pk)]['learning_fingerprint'] for row in rows):
                    return api_error('تغيّرت الأسئلة، احتفظ بالنتائج محليًا وأعد التنزيل للتدريب الجديد', 409)
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
            return api_error('تعارض معرّف المزامنة', 409)
        return api_success(data=result)
