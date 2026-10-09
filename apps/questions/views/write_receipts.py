"""Caller-scoped creation receipts and read-only uncertain-write reconciliation."""
import hashlib
import json
from django.db import transaction
from rest_framework import serializers
from apps.core.models import QuestionWriteReceipt
from apps.core.utils import api_success, api_error
from apps.users.models import User
from ..models import Question
from ..serializers import QuestionSerializer
from ..services import QuestionService


def _identity(value):
    return serializers.UUIDField().run_validation(value)


def _result(request, receipt):
    question = Question.objects.visible_to(request.user).filter(pk=receipt.question_id).first()
    if question is None:
        return api_error('تم تنفيذ العملية لكن السؤال لم يعد متاحًا.', 410)
    return api_success(data=QuestionSerializer(question, context={'request': request}).data)


def read_receipt(request, action, source_id=None):
    identity = _identity(request.query_params.get('operation_id'))
    receipt = QuestionWriteReceipt.objects.filter(
        user=request.user, operation_id=identity, action=action, source_question_id=source_id).first()
    if receipt is None:
        return api_error('لا يوجد سجل لهذه العملية.', 404)
    return _result(request, receipt)


@transaction.atomic
def write_question(request, action, source_id=None):
    User.objects.select_for_update().only('id').get(pk=request.user.pk)
    raw_identity = request.data.get('operation_id')
    identity = _identity(raw_identity) if raw_identity is not None else None
    data = dict(request.data)
    data.pop('operation_id', None)
    fingerprint = hashlib.sha256(json.dumps(
        {'action': action, 'source_id': source_id, 'data': data},
        sort_keys=True, ensure_ascii=False, separators=(',', ':'),
    ).encode()).hexdigest()
    if identity:
        prior = QuestionWriteReceipt.objects.filter(user=request.user, operation_id=identity).first()
        if prior:
            if prior.request_fingerprint != fingerprint:
                return api_error('تعارض معرّف العملية.', 409)
            return _result(request, prior)
    if action == 'create':
        question = QuestionService.create_question(data, request.user)
    else:
        from django.shortcuts import get_object_or_404
        original = get_object_or_404(Question.objects.visible_to(request.user).select_related('case'), pk=source_id)
        question = QuestionService.duplicate_question(original, request.user)
    if identity:
        QuestionWriteReceipt.objects.create(user=request.user, operation_id=identity, action=action,
            source_question_id=source_id, request_fingerprint=fingerprint, question=question)
    return api_success(data=QuestionSerializer(question, context={'request': request}).data,
                       message='تم إنشاء السؤال' if action == 'create' else 'تم نسخ السؤال', code=201)
