# backend/apps/master_exams/admin.py

from django.contrib import admin
from django.db import router, transaction
from apps.users.models import User
from apps.questions.hierarchy import lock_tag_hierarchy

from .models import (
    MasterExam,
    MasterExamQuestion,
    MasterExamAttempt,
    MasterExamAcknowledgement,
)


class MasterExamQuestionInline(admin.TabularInline):
    model = MasterExamQuestion
    extra = 0
    fields = ('order', 'question')
    autocomplete_fields = ['question']
    ordering = ('order',)


class MasterExamAttemptInline(admin.TabularInline):
    model = MasterExamAttempt
    extra = 0
    fields = (
        'user', 'is_complete', 'is_makeup', 'forced_finish',
        'correct_count', 'answered_count', 'total_questions', 'accuracy', 'weighted_score',
        'started_at', 'finished_at',
    )
    readonly_fields = fields
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(MasterExam)
class MasterExamAdmin(admin.ModelAdmin):
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        using = router.db_for_write(self.model)
        try:
            locked_id = int(object_id) if object_id is not None else None
        except (TypeError, ValueError):
            locked_id = None
        with transaction.atomic(using=using):
            if request.method == 'POST':
                User.objects.using(using).select_for_update().only('id').get(pk=request.user.pk)
                list(MasterExam.objects.using(using).select_for_update().filter(pk=locked_id))
                lock_tag_hierarchy(using)
            return super().changeform_view(request, object_id, form_url, extra_context)

    list_display = (
        'name', 'primary_attending', 'stored_status', 'opens_at', 'closes_at',
        'duration_minutes', 'question_count_display',
    )
    list_filter = ('stored_status',)
    search_fields = ('name', 'description', 'primary_attending__username')
    date_hierarchy = 'opens_at'
    readonly_fields = (
        'version', 'published_at', 'completed_at', 'published_to_bank_at',
        'created_at', 'updated_at',
    )
    inlines = [MasterExamQuestionInline, MasterExamAttemptInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'instructions', 'exam_topic_tag'),
        }),
        ('Attendings', {
            'fields': ('primary_attending', 'co_attendings'),
        }),
        ('Schedule', {
            'fields': ('opens_at', 'closes_at', 'duration_minutes', 'allow_makeup'),
        }),
        ('Audience', {
            'fields': ('audience_all_doctors', 'audience_groups', 'audience_users'),
        }),
        ('Scoring', {
            'fields': ('weight_easy', 'weight_medium', 'weight_hard'),
        }),
        ('Shuffle', {
            'fields': ('shuffle_questions', 'shuffle_choices'),
        }),
        ('Status', {
            'fields': (
                'stored_status', 'version',
                'published_at', 'completed_at', 'published_to_bank_at',
                'created_at', 'updated_at',
            ),
        }),
    )

    def question_count_display(self, obj):
        return obj.exam_questions.count()
    question_count_display.short_description = 'Questions'


@admin.register(MasterExamQuestion)
class MasterExamQuestionAdmin(admin.ModelAdmin):
    list_display = ('master_exam', 'order', 'question')
    list_filter = ('master_exam',)
    autocomplete_fields = ['question', 'master_exam']
    ordering = ('master_exam', 'order')

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        using = router.db_for_write(self.model)
        try:
            locked_id = int(object_id) if object_id is not None else None
        except (TypeError, ValueError):
            locked_id = None
        with transaction.atomic(using=using):
            if request.method == 'POST':
                User.objects.using(using).select_for_update().only('id').get(pk=request.user.pk)
                ids = set(MasterExamQuestion.objects.using(using).filter(pk=locked_id).values_list('master_exam_id', flat=True))
                try:
                    ids.add(int(request.POST.get('master_exam', '')))
                except (TypeError, ValueError):
                    pass  # Let the form render its normal validation error.
                list(MasterExam.objects.using(using).select_for_update().filter(pk__in=ids).order_by('pk'))
                lock_tag_hierarchy(using)
            return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(MasterExamAttempt)
class MasterExamAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'master_exam', 'is_complete', 'is_makeup', 'forced_finish',
        'correct_count', 'answered_count', 'total_questions', 'accuracy', 'started_at',
    )
    list_filter = ('is_complete', 'is_makeup', 'forced_finish')
    search_fields = ('user__username', 'master_exam__name', 'session_id')
    date_hierarchy = 'started_at'
    readonly_fields = (
        'session_id', 'master_exam', 'user', 'question_ids', 'answers',
        'current_question_id', 'started_at', 'deadline_at', 'finished_at',
        'results', 'correct_count', 'answered_count', 'total_questions', 'weighted_score',
        'accuracy', 'is_complete', 'is_makeup', 'forced_finish',
        'exam_name_snapshot', 'created_at', 'updated_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(MasterExamAcknowledgement)
class MasterExamAcknowledgementAdmin(admin.ModelAdmin):
    list_display = ('user', 'master_exam', 'acknowledged_at')
    search_fields = ('user__username', 'master_exam__name')
    date_hierarchy = 'acknowledged_at'
