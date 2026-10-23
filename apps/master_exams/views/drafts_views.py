# backend/apps/master_exams/views/drafts_views.py
"""
Draft-question library for master-exam authors.

Draft questions are private to their author (or visible to admins
via 'manage_any'). They only become public bank content when the
exam is either deleted with delete_mode='publish_drafts' or
completed and published to the bank.
"""
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView

from apps.core.utils import api_success, api_error
from apps.core.permissions import HasCapability
from apps.core.revisions import expected_revision, check_revision
from apps.core.exceptions import RevisionConflict
from apps.questions.hierarchy import lock_tag_hierarchy
from apps.questions.models import Question
from apps.users.models import User

from ..models import MasterExam, MasterExamQuestion
from ..serializers import (
    MasterExamDraftSerializer,
    MasterExamDraftUpdateSerializer,
)


class MasterExamDraftsLibraryView(APIView):
    """
    List the caller's draft questions, filterable by search term and
    by whether the draft is currently attached to any non-cancelled
    exam.

    Requires 'master_exams.drafts_library'. Admins see every draft;
    everyone else sees only their own.
    """
    permission_classes = [HasCapability]
    required_capability = 'master_exams.drafts_library'

    def get(self, request):
        # An admin (through 'manage_any') sees every draft. Any other
        # holder of 'drafts_library' sees only their own.
        if request.user.has_capability('master_exams.manage_any'):
            qs = Question.objects.filter(is_draft=True)
        else:
            qs = Question.objects.filter(is_draft=True, draft_owner=request.user)

        search = (request.query_params.get('search') or '').strip()
        if len(search) >= 2:
            qs = qs.filter(
                Q(question__icontains=search) |
                Q(explanation__icontains=search) |
                Q(source__icontains=search)
            ).distinct()

        usage = request.query_params.get('usage')
        if usage in ('orphan', 'attached'):
            # One pass over every exam's through-relation question ids.
            # `MasterExam.question_ids` is a Python property now, so
            # iterate the relation directly: values_list on a
            # non-existent JSONField column would raise FieldError.
            all_ids = set()
            for qid in (
                MasterExam.objects
                .exclude(stored_status='cancelled')
                .values_list('exam_questions__question_id', flat=True)
            ):
                if qid is not None:
                    all_ids.add(qid)

            if usage == 'orphan':
                qs = qs.exclude(id__in=all_ids)
            else:
                qs = qs.filter(id__in=all_ids)

        qs = qs.select_related('case', 'category').prefetch_related('tags').order_by('-created_at')
        serializer = MasterExamDraftSerializer(qs, many=True)
        return api_success(data={
            'items': serializer.data,
            'total': qs.count(),
        })


class MasterExamDraftDetailView(APIView):
    """
    Read / update / delete a single draft.

    Authors can only touch their own drafts; holders of
    'master_exams.manage_any' (admins) can touch any draft. A draft
    cannot be deleted while attached to a non-cancelled exam — it
    must be removed from the exam first, so the deletion cannot
    silently break a live exam.

    Deletion checks the current draft owner, revision and attached exam
    states under ordered locks. Newly discovered attachments require review.
    Cancelled/archived links may be detached, while frozen attempt pages remain
    readable even after the live question is removed.

    CASE_ORDER ON UPDATE (fixed)
    ----------------------------
    The PUT handler now assigns `draft.case_order` from the payload
    when the caller supplied the field. Previously the field was
    accepted by `MasterExamDraftCreateSerializer` and then silently
    discarded, so the stored ordering never matched the accepted
    input. Sending `case_order: null` explicitly clears the value,
    which matches the model's nullable semantics.
    """
    permission_classes = [HasCapability]
    required_capability = 'master_exams.drafts_library'

    def _can_edit(self, user, draft):
        if user.has_capability('master_exams.manage_any'):
            return True
        return draft.draft_owner_id == user.id

    def get(self, request, draft_id):
        draft = get_object_or_404(
            Question.objects.select_related('case', 'category').prefetch_related('tags'),
            id=draft_id,
            is_draft=True,
        )
        if not self._can_edit(request.user, draft):
            return api_error('غير مصرح لك', 403, reason='PERMISSION_DENIED')
        return api_success(data=MasterExamDraftSerializer(draft).data)

    @transaction.atomic
    def put(self, request, draft_id):
        User.objects.select_for_update().get(pk=request.user.pk)
        lock_tag_hierarchy()
        draft = get_object_or_404(
            Question.objects.select_for_update(),
            id=draft_id,
            is_draft=True,
        )
        if not self._can_edit(request.user, draft):
            return api_error('غير مصرح لك', 403, reason='PERMISSION_DENIED')

        serializer = MasterExamDraftUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error('بيانات غير صالحة', 400, details=serializer.errors, reason='INVALID_DATA')

        payload = dict(serializer.validated_data)
        check_revision(draft.version, payload.pop('expected_version'))
        category_id = payload.pop('category', None)
        category = None
        if category_id:
            from apps.questions.models import Category
            category = Category.objects.filter(id=category_id).first()

        # Case linkage.
        #
        # The serializer declares both `case_key` and `case_stem`. We
        # only touch the FK when `case_key` was actually present in
        # the request body — an edit that omits the field must not
        # detach an existing case. Passing `case_key: null` or
        # `case_key: ""` explicitly detaches.
        #
        # Stem hints initialize new cases only. Existing shared stems use
        # the authorized revisioned case editor, including blank stems.
        case_key_present = 'case_key' in request.data
        case_key = payload.pop('case_key', None)
        case_stem = payload.pop('case_stem', None)
        # `case_order` is a plain scalar on the Question row — pull
        # it out of the payload and apply it below. We distinguish
        # "not provided" from "provided as null" so an edit that
        # omits the key does not accidentally clear the ordering.
        case_order_present = 'case_order' in request.data
        case_order = payload.pop('case_order', None)

        if case_key_present:
            from apps.questions.serializers import _resolve_case
            draft.case = _resolve_case(
                case_key,
                request.user,
                stem=case_stem,
                existing_case=draft.case,
            )

        draft.question = payload['question']
        draft.choices = payload['choices']
        draft.correct_answer = payload['correct_answer']
        draft.explanation = payload.get('explanation') or ''
        draft.source = payload.get('source') or None
        draft.difficulty = payload.get('difficulty', 'medium')
        draft.category = category

        if case_order_present:
            draft.case_order = case_order

        # Retained translations must still match a changed base choice list.
        # Reject at the API boundary rather than allowing a model ValueError/500.
        from apps.questions.translation_validation import normalize_translations
        from rest_framework.exceptions import ValidationError
        try:
            normalize_translations(draft.translations, base_choice_count=len(draft.choices))
        except ValueError as exc:
            raise ValidationError({'choices': [str(exc)]}) from exc
        draft.last_revised_at = timezone.localdate()
        draft.save()
        return api_success(data=MasterExamDraftSerializer(draft).data)

    @transaction.atomic
    def delete(self, request, draft_id):
        User.objects.select_for_update().only('id').get(pk=request.user.pk)
        # Exam writers acquire exam before structural gate/question. Discover
        # participants first, then refuse a newly discovered exam rather than
        # taking it in reverse order while holding the gate.
        exam_ids = set(MasterExamQuestion.objects.filter(question_id=draft_id)
                       .values_list('master_exam_id', flat=True))
        exams = list(MasterExam.objects.select_for_update().filter(pk__in=exam_ids).order_by('pk'))
        lock_tag_hierarchy()
        draft = get_object_or_404(Question.objects.select_for_update(), id=draft_id, is_draft=True)
        if not self._can_edit(request.user, draft):
            return api_error('غير مصرح لك', 403, reason='PERMISSION_DENIED')
        check_revision(draft.version, expected_revision(request))
        links = list(MasterExamQuestion.objects.select_for_update().filter(question_id=draft.pk))
        if not {link.master_exam_id for link in links}.issubset({exam.pk for exam in exams}):
            raise RevisionConflict()

        # A draft is "in use" if any through-row references it AND the
        # exam is in a state where the question is part of a live
        # experience. Cancelled and published_to_bank exams are
        # terminal — their through-rows are historical artefacts, not
        # active attachments, so the draft can be cleaned up.
        attached_ids = {link.master_exam_id for link in links}
        blocking = any(exam.pk in attached_ids and exam.stored_status not in ('cancelled', 'published_to_bank') for exam in exams)
        if blocking:
            return api_error(
                'الموضوع مرتبط بامتحان قائم — احذفه من الامتحان أولاً',
                409,
                reason='TOPIC_IN_EXAM',
            )

        MasterExamQuestion.objects.filter(question_id=draft.id).delete()
        draft.delete()

        return api_success(message='تم حذف المسودة')
