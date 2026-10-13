from django.db import transaction
from apps.core.revisions import expected_revision, check_revision
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.write_receipts import create_with_receipt
from apps.core.utils import api_error, api_success, paginate

from ..models import KnowledgeObject, Question
from ..serializers import KnowledgeObjectSerializer, QuestionSerializer


def _knowledge_queryset(user):
    return (
        KnowledgeObject.objects
        .select_related('category', 'created_by')
        .prefetch_related('tags')
        .annotate(question_count=Count(
            'questions', distinct=True,
            filter=Q(questions__in=Question.objects.visible_to(user)),
        ))
    )


def _may_manage(user, instance=None):
    if user.has_capability('questions.edit_any'):
        return True
    if instance is None:
        return user.has_capability('questions.create')
    return (
        user.has_capability('questions.edit_own')
        and instance.created_by_id == user.id
    )


class KnowledgeObjectListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = _knowledge_queryset(request.user)
        search = (request.query_params.get('search') or '').strip()
        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(learning_objective__icontains=search)
                | Q(canonical_answer__icontains=search)
            )
        status = request.query_params.get('status')
        if status in dict(KnowledgeObject.STATUS_CHOICES):
            qs = qs.filter(status=status)
        category = request.query_params.get('category')
        if category:
            qs = qs.filter(category_id=category)
        qs = qs.order_by('title', 'pk')
        if 'page' in request.query_params or 'per_page' in request.query_params:
            items, meta = paginate(qs, request)
            return api_success(data={
                'items': KnowledgeObjectSerializer(items, many=True).data,
                'count': meta['total'], **meta,
            })
        # Existing autocomplete callers retain their bounded response contract.
        return api_success(data={
            'items': KnowledgeObjectSerializer(qs[:500], many=True).data,
            'count': qs.count(),
        })

    def post(self, request):
        if not _may_manage(request.user):
            return api_error('غير مصرح لك بإنشاء أهداف معرفية', 403)
        serializer = KnowledgeObjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = create_with_receipt(request, 'knowledge.create', KnowledgeObject, lambda: serializer.save(created_by=request.user))
        instance.question_count = 0
        return api_success(
            data=KnowledgeObjectSerializer(instance).data,
            message='تم إنشاء الهدف المعرفي',
            code=201,
        )


class KnowledgeObjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(_knowledge_queryset(self.request.user), pk=pk)

    def get(self, request, pk):
        return api_success(data=KnowledgeObjectSerializer(self.get_object(pk)).data)

    @transaction.atomic
    def put(self, request, pk):
        from apps.users.models import User
        from apps.questions.hierarchy import lock_tag_hierarchy
        User.objects.select_for_update().get(pk=request.user.pk)
        lock_tag_hierarchy()
        instance = self.get_object(pk)
        if not _may_manage(request.user, instance):
            return api_error('غير مصرح لك بتعديل هذا الهدف المعرفي', 403)
        serializer = KnowledgeObjectSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        instance.question_count = instance.questions.visible_to(request.user).count()
        return api_success(data=KnowledgeObjectSerializer(instance).data)

    @transaction.atomic
    def delete(self, request, pk):
        # Match linked-content lock ordering before taking the parent row.
        list(Question.objects.select_for_update().filter(knowledge_object_id=pk).order_by('pk').values_list('pk', flat=True))
        instance = get_object_or_404(KnowledgeObject.objects.select_for_update(), pk=pk)
        if not _may_manage(request.user, instance):
            return api_error('غير مصرح لك بحذف هذا الهدف المعرفي', 403)
        check_revision(instance.version, expected_revision(request))
        instance.delete()
        return api_success(message='تم حذف الهدف المعرفي')


class KnowledgeObjectQuestionsView(APIView):
    """Caller-visible linked questions, including authorized drafts, with normal pagination."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        get_object_or_404(KnowledgeObject, pk=pk)
        questions = (Question.objects.visible_to(request.user).filter(knowledge_object_id=pk)
                     .select_related('category', 'authored_by', 'owned_by', 'case', 'knowledge_object')
                     .prefetch_related('tags').order_by('id'))
        page, meta = paginate(questions, request)
        page = list(page)
        cache = QuestionSerializer.build_case_sibling_cache(page, request.user)
        return api_success(data={'items': QuestionSerializer(page, many=True, context={
            'request': request, 'case_sibling_cache': cache,
        }).data, **meta})
