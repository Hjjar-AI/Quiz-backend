import hashlib
import json
from django.db import transaction
from django.http import Http404
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import ContentWriteReceipt
from .utils import api_success
from .exceptions import RevisionConflict


@transaction.atomic
def create_with_receipt(request, action, model, create):
    raw = request.data.get('operation_id')
    if raw is None:
        return create()
    identity = serializers.UUIDField().run_validation(raw)
    body = {key: value for key, value in request.data.items() if key != 'operation_id'}
    fingerprint = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    # A unique receipt row serializes this identity; avoid locking User before
    # taxonomy rows and introducing an audit/FK lock inversion.
    receipt, _ = ContentWriteReceipt.objects.get_or_create(user=request.user, operation_id=identity,
        defaults={'action': action, 'request_fingerprint': fingerprint})
    receipt = ContentWriteReceipt.objects.select_for_update().get(pk=receipt.pk)
    if receipt.action != action or receipt.request_fingerprint != fingerprint:
        raise RevisionConflict('تعارض معرّف العملية.')
    if receipt.target_id is not None:
        result = model.objects.filter(pk=receipt.target_id).first()
        if result is None:
            raise Http404
        return result
    result = create()
    receipt.target_id = result.pk
    receipt.save(update_fields=['target_id'])
    return result


class ContentReceiptView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, operation_id):
        receipt = ContentWriteReceipt.objects.filter(user=request.user, operation_id=operation_id, target_id__isnull=False).first()
        if receipt is None:
            raise Http404
        # Only the caller's operation identity; content uses its ordinary
        # independent visibility/ownership gates when subsequently fetched.
        return api_success(data={'action': receipt.action, 'target_id': receipt.target_id})
