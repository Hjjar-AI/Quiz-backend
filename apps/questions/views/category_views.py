# backend/apps/questions/views/category_views.py

import re
from django.db import transaction
from apps.core.revisions import expected_revision, check_revision
from apps.core.write_receipts import create_with_receipt

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models.deletion import ProtectedError

from ..models import Category, CATEGORY_NAME_MAX_LENGTH
from ..colors import is_valid_hex_color
from ..serializers import CategorySerializer
from apps.core.permissions import HasCapability
from apps.core.utils import api_success, api_error
from apps.core.audit import log_privileged_action


_CATEGORY_ICON_RE = re.compile(r'^bi-[a-z0-9-]{1,47}$')


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

    def post(self, request):
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
        category = get_object_or_404(Category.objects.select_for_update(), id=category_id)
        check_revision(category.version, expected_revision(request))
        category_name = category.name
        try:
            category.delete()
        except ProtectedError:
            return api_error('التصنيف مستخدم في خطة دراسة؛ أزل الهدف أو استبدله أولاً', 409)
        log_privileged_action(request, 'category.delete', target_repr=category_name,
                              details={'category_id': category_id})
        return api_success(message='تم حذف التصنيف')
