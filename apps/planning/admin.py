# backend/apps/planning/admin.py

from django.contrib import admin
from django.db import router, transaction

from .models import StudyPlanner, StudyPlannerDay


class StudyPlannerDayInline(admin.TabularInline):
    model = StudyPlannerDay
    extra = 0
    fields = ('date', 'questions_answered')
    ordering = ('-date',)
    readonly_fields = ()
    max_num = 30  # keep the edit page bounded for long-lived accounts


@admin.register(StudyPlanner)
class StudyPlannerAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'target_questions_per_day', 'start_date', 'end_date',
        'category_count', 'tag_count',
    )
    search_fields = ('user__username',)
    filter_horizontal = ('target_categories', 'target_tags')
    inlines = [StudyPlannerDayInline]

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        # Admin saves the planner before its M2M links, so acquire the same
        # hierarchy-first lock order as the API and tag merge service.
        using = router.db_for_write(self.model)
        with transaction.atomic(using=using):
            if request.method == 'POST':
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
