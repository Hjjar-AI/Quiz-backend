# backend/apps/questions/views/category_views.py

import re
from django.db import transaction
from django.db.models import F, Q
from apps.core.revisions import expected_revision, check_revision
from apps.core.write_receipts import create_with_receipt

from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models.deletion import ProtectedError

from ..models import Category, Question, KnowledgeObject, CATEGORY_NAME_MAX_LENGTH
from ..colors import is_valid_hex_color
from ..serializers import CategorySerializer
from apps.core.permissions import HasCapability
from apps.core.utils import api_success, api_error
from apps.core.audit import log_privileged_action
from ..hierarchy import lock_tag_hierarchy
from apps.users.models import User


_CATEGORY_ICON_RE = re.compile(r'^bi-[a-z0-9-]{1,47}$')


def _lock_category_writer(request):
    User.objects.select_for_update().only('id').get(pk=request.user.pk)
    lock_tag_hierarchy()


def _validate_color(raw, default='#667eea'):
    """Return a validated hex color, or None if invalid."""
    if raw is None or raw == '':
        return default
    value = str(raw).strip()
    if not is_valid_hex_color(value):
        return None
    return value


def _validate_icon(raw, default='bi-folder'):
    """Return the validated icon class, or None if invalid."""
    if raw is None or raw == '':
        return default
    value = str(raw).strip()
    if not _CATEGORY_ICON_RE.match(value):
        return None
    return value


def _coerce_name(raw, fallback=None):
    """Trim a required name field. Returns fallback if raw is empty."""
    if raw is None:
        return fallback
    value = str(raw).strip()
    if not value:
        return fallback
    return value


class CategoryListView(APIView):
    """
    List all categories. Read-only; any authenticated user. Used by
    the category picker, the FilterBar, and the analytics breakdowns.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return api_success(data={
            'items': serializer.data,
            'total': categories.count(),
        })


class CategoryCreateView(APIView):
    """
    Create a category. Requires 'categories.manage'.
    """
    permission_classes = [HasCapability]
    required_capability = 'categories.manage'

    @transaction.atomic
    def post(self, request):
        _lock_category_writer(request)
        data = request.data

        name = _coerce_name(data.get('name'))
        if not name:
            return api_error('اسم التصنيف مطلوب', 400)

        if len(name) > CATEGORY_NAME_MAX_LENGTH:
            return api_error(
                f'اسم التصنيف يجب ألا يتجاوز {CATEGORY_NAME_MAX_LENGTH} حرفاً',
                400,
            )

        color = _validate_color(data.get('color'), default='#667eea')
        if color is None:
            return api_error(
                'اللون غير صالح. استخدم صيغة HEX مثل #667eea أو #fff أو #667eea80',
                400,
            )

        icon = _validate_icon(data.get('icon'), default='bi-folder')
        if icon is None:
            return api_error(
                'الأيقونة غير صالحة. استخدم اسماً من Bootstrap Icons مثل bi-folder',
                400,
            )

        def create():
            from rest_framework.exceptions import ValidationError
            if Category.objects.filter(name=name).exists():
                raise ValidationError({'name': ['التصنيف موجود مسبقاً']})
            return Category.objects.create(
                name=name,
                description=data.get('description'),
                color=color,
                icon=icon,
                created_by=request.user.username,
            )
        category = create_with_receipt(request, 'category.create', Category, create)
        log_privileged_action(request, 'category.create', target=category)
        return api_success(
            data=CategorySerializer(category).data,
            message='تم إنشاء التصنيف',
            code=201,
        )


class CategoryUpdateView(APIView):
    """
    Update a category. Requires 'categories.manage'.
    """
    permission_classes = [HasCapability]
    required_capability = 'categories.manage'

    @transaction.atomic
    def put(self, request, category_id):
        _lock_category_writer(request)
        category = get_object_or_404(Category.objects.select_for_update(), id=category_id)
        check_revision(category.version, expected_revision(request))
        data = request.data

        new_name = _coerce_name(data.get('name'), fallback=category.name)
        if not new_name:
            return api_error('اسم التصنيف مطلوب', 400)

        if len(new_name) > CATEGORY_NAME_MAX_LENGTH:
            return api_error(
                f'اسم التصنيف يجب ألا يتجاوز {CATEGORY_NAME_MAX_LENGTH} حرفاً',
                400,
            )
        if new_name != category.name and Category.objects.filter(name=new_name).exists():
            return api_error('التصنيف موجود مسبقاً', 400)

        new_color = _validate_color(
            data.get('color', category.color), default=category.color,
        )
        if new_color is None:
            return api_error(
                'اللون غير صالح. استخدم صيغة HEX مثل #667eea أو #fff أو #667eea80',
                400,
            )

        new_icon = _validate_icon(
            data.get('icon', category.icon), default=category.icon,
        )
        if new_icon is None:
            return api_error(
                'الأيقونة غير صالحة. استخدم اسماً من Bootstrap Icons مثل bi-folder',
                400,
            )

        category.name = new_name
        category.description = data.get('description', category.description)
        category.color = new_color
        category.icon = new_icon
        category.save()
        log_privileged_action(request, 'category.update', target=category)

        return api_success(data=CategorySerializer(category).data)


class CategoryMergeView(APIView):
    """Merge one category into an existing category without losing its links."""
    permission_classes = [HasCapability]
    required_capability = 'categories.manage'

    @transaction.atomic
    def post(self, request):
        _lock_category_writer(request)
        source_id = serializers.IntegerField(min_value=1).run_validation(request.data.get('source_id'))
        target_id = serializers.IntegerField(min_value=1).run_validation(request.data.get('target_id'))
        source_version = expected_revision(request)
        target_version = serializers.IntegerField(min_value=1).run_validation(request.data.get('target_version'))
        if source_id == target_id:
            return api_error('اختر تصنيفاً آخر / Choose another category', 400)

        def merge():
            from apps.exams.models import Blueprint, BlueprintWeight
            from apps.planning.models import StudyPlanner
            from apps.planning.services import StudyPlannerService

            # Same gate as planner API/admin and tag structural writers,
            # acquired before questions/categories/planners in this merge.
            lock_tag_hierarchy()

            # Assessed-parent/editor writes lock questions before their parent.
            # Include both categories so opposing merges share ordered locks.
            affected = Question.objects.filter(Q(category_id__in=[source_id, target_id]) |
                                               Q(knowledge_object__category_id__in=[source_id, target_id]))
            list(Question.objects.select_for_update().filter(pk__in=affected.values('pk'))
                 .order_by('pk').values_list('pk', flat=True))
            # Both identities are checked under the same ordered locks. The
            # receipt guards response-loss retries even after source deletion.
            rows = {row.pk: row for row in Category.objects.select_for_update()
                    .filter(pk__in=[source_id, target_id]).order_by('pk')}
            source = rows.get(source_id)
            target = rows.get(target_id)
            if source is None or target is None:
                from django.http import Http404
                raise Http404
            check_revision(source.version, source_version)
            check_revision(target.version, target_version)

            objects = KnowledgeObject.objects.select_for_update().filter(category_id=source_id)
            list(objects.order_by('pk').values_list('pk', flat=True))
            moved = Question.objects.filter(category_id=source_id).update(
                category_id=target_id, version=F('version') + 1)
            knowledge = objects.update(category_id=target_id, version=F('version') + 1)

            planners = list(StudyPlanner.objects.select_for_update()
                            .filter(target_categories=source).order_by('pk'))
            for planner in planners:
                StudyPlannerService._scope(planner)
                planner._scope_update_in_progress = True
                planner.target_categories.add(target)
                planner.target_categories.remove(source)
                StudyPlannerService.record_scope_change(planner, retain_today=True)

            blueprints = list(Blueprint.objects.select_for_update()
                              .filter(weight_entries__category=source).order_by('pk'))
            for blueprint in blueprints:
                entries = {row.category_id: row for row in BlueprintWeight.objects.select_for_update()
                           .filter(blueprint=blueprint, category_id__in=[source_id, target_id])}
                entry = entries.get(source_id)
                if entry is None:
                    continue
                if target_id in entries:
                    existing = entries[target_id]
                    existing.weight += entry.weight
                    import math
                    if not math.isfinite(existing.weight):
                        raise serializers.ValidationError({'weights': 'Merged weight is too large.'})
                    existing.save(update_fields=['weight'])
                    entry.delete()
                else:
                    entry.category = target
                    entry.save(update_fields=['category'])

            source_name = source.name
            source.delete()
            # The actor lock was acquired before the structural/content locks,
            # so the audit FK cannot invert learner/question ordering here.
            log_privileged_action(
                request, 'category.merge', target=target,
                details={'source_id': source_id, 'source_name': source_name,
                         'questions_moved': moved, 'knowledge_objects_moved': knowledge,
                         'planners_migrated': len(planners), 'blueprints_migrated': len(blueprints)})
            return target

        target = create_with_receipt(request, 'category.merge', Category, merge)
        return api_success(data=CategorySerializer(target).data,
                           message='تم دمج التصنيف / Category merged')


class CategoryDeleteView(APIView):
    """
    Delete a category. Requires 'categories.manage'. Questions in the
    category are not deleted — their category FK is set to NULL
    (SET_NULL on the model).
    """
    permission_classes = [HasCapability]
    required_capability = 'categories.manage'

    @transaction.atomic
    def delete(self, request, category_id):
        _lock_category_writer(request)
        category = get_object_or_404(Category.objects.select_for_update(), id=category_id)
        check_revision(category.version, expected_revision(request))
        category_name = category.name
        try:
            category.delete()
        except ProtectedError:
            return api_error('التصنيف مستخدم في خطة دراسة؛ أزل الهدف أو استبدله أولاً', 409)
        log_privileged_action(
            request, 'category.delete', target_repr=category_name,
            details={'category_id': category_id})
        return api_success(message='تم حذف التصنيف')
