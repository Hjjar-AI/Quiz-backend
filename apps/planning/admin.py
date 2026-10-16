# backend/apps/planning/admin.py

from django.contrib import admin
from django.db import router, transaction

from .models import StudyPlanner, StudyPlannerDay


class StudyPlannerDayInline(admin.TabularInline):
    model = StudyPlannerDay
    extra = 0
    fields = ('date', 'questions_answered')
    ordering = ('-date',)
    readonly_fields = ('date', 'questions_answered')
    can_delete = False
    max_num = 30  # keep the edit page bounded for long-lived accounts

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(StudyPlanner)
class StudyPlannerAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'target_questions_per_day', 'start_date', 'end_date',
        'category_count', 'tag_count',
    )
    search_fields = ('user__username',)
    filter_horizontal = ('target_categories', 'target_tags')
    inlines = [StudyPlannerDayInline]
    readonly_fields = ('version',)

    def save_model(self, request, obj, form, change):
        from .services import StudyPlannerService
        if change:
            previous = StudyPlanner.objects.select_for_update().get(pk=obj.pk)
            StudyPlannerService._scope(previous)
            obj.version = previous.version + 1
        obj._scope_update_in_progress = True
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        from .services import StudyPlannerService
        StudyPlannerService.record_scope_change(form.instance)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        # Admin saves the planner before its M2M links, so acquire the same
        # hierarchy-first lock order as the API and tag merge service.
        using = router.db_for_write(self.model)
        with transaction.atomic(using=using):
            if request.method == 'POST':
                from apps.users.models import User
                User.objects.using(using).select_for_update().get(pk=request.user.pk)
                from apps.questions.hierarchy import lock_tag_hierarchy
                lock_tag_hierarchy(using)
            return super().changeform_view(request, object_id, form_url, extra_context)

    def category_count(self, obj):
        return obj.target_categories.count()
    category_count.short_description = 'Categories'

    def tag_count(self, obj):
        return obj.target_tags.count()
    tag_count.short_description = 'Tags'


@admin.register(StudyPlannerDay)
class StudyPlannerDayAdmin(admin.ModelAdmin):
    list_display = ('planner', 'date', 'questions_answered')
    list_filter = ('date',)
    search_fields = ('planner__user__username',)
    date_hierarchy = 'date'
    ordering = ('-date',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
