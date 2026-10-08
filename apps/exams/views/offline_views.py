"""Signed offline study packs and exactly-once, caller-owned completion upload.

Rollout requires prepared source_session_id and OfflineCompletion schema migrations.
Offline practice never creates or completes a timed/master examination.
"""
import base64
import hashlib
import json
import uuid

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


class CompletionRequest(serializers.Serializer):
    completion_id = serializers.UUIDField()
    token = serializers.CharField(max_length=MAX_PACK_BYTES * 2, trim_whitespace=False)
    answers = OfflineAnswer(many=True, allow_empty=False)
    time_spent = serializers.IntegerField(min_value=0, max_value=7 * 24 * 60 * 60)

    def validate_answers(self, value):
        if len(value) > 200 or len({row['question_id'] for row in value}) != len(value):
            raise serializers.ValidationError('إجابات غير صالحة أو مكررة')
        return value


def _closed(request, rows):
    serializer = QuestionSerializer(context={'request': request})
    return any(serializer.get_answers_hidden(row) for row in rows)


class OfflinePackView(APIView):
    permission_classes = [HasCapability]
    required_capability = 'tests.start'

    def post(self, request):
        body = PackRequest(data=request.data)
        body.is_valid(raise_exception=True)
        ids = body.validated_data['question_ids']
        with transaction.atomic():
            User.objects.select_for_update().only('id').get(pk=request.user.pk)
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
            payload = {'schema': 1, 'user_id': request.user.pk, 'pack_id': str(uuid.uuid4()),
                       'question_ids': ids, 'snapshots': snapshots}
            token = signing.dumps(payload, salt=SALT, compress=True)
            data = {'id': payload['pack_id'], 'token': token, 'questions': questions, 'images': images}
            if len(json.dumps(data, ensure_ascii=False).encode('utf-8')) > MAX_PACK_BYTES:
                return api_error('التنزيل كبير جدًا، اختر أسئلة أقل', 400)
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
        identity = str(values['completion_id'])
        fingerprint = hashlib.sha256(json.dumps({
            'pack_id': pack['pack_id'], 'answers': sorted(answers, key=lambda row: row['question_id']),
            'time_spent': values['time_spent'],
        }, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        try:
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=request.user.pk)
                prior = OfflineCompletion.objects.filter(completion_id=identity).first()
                if prior:
                    if prior.user_id != user.pk or prior.request_fingerprint != fingerprint:
                        return api_error('تعارض معرّف المزامنة', 409)
                    return api_success(data=prior.response)
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
                slots = {str(index): {'answer': indexed[qid]['answer'], 'confidence': indexed[qid]['confidence']}
                         for index, qid in enumerate(ids)}
                graded = ExamService.grade_exam(ids, slots, question_snapshots=pack['snapshots'])
                ExamService.record_completion_side_effects(user, graded['questions'])
                history = ExamService.save_history(user, 'study', 'Offline practice',
                    graded['total_questions'], graded['answered_count'], graded['correct_count'],
                    graded['accuracy'], values['time_spent'], timezone.now(), graded['questions'],
                    source_session_id=identity)
                result = ExamService.completed_result(history)
                OfflineCompletion.objects.create(completion_id=identity, user=user,
                    request_fingerprint=fingerprint, response=result)
        except IntegrityError:
            return api_error('تعارض معرّف المزامنة', 409)
        return api_success(data=result)
