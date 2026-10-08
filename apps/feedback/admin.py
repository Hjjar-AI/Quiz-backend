# backend/apps/feedback/admin.py

from django.contrib import admin

from .models import Bookmark, QuestionFlag, QuestionRating
from .services import FeedbackService


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'created_at')


@admin.register(QuestionFlag)
class QuestionFlagAdmin(admin.ModelAdmin):
    list_display = ('question', 'user', 'reason', 'resolved', 'created_at')
    list_filter = ('resolved',)
    actions = ['resolve_flags']

    def resolve_flags(self, request, queryset):
        count = FeedbackService.resolve_flags(queryset, request.user)
        self.message_user(request, f'{count} flags resolved.')
    resolve_flags.short_description = 'Resolve selected flags'


@admin.register(QuestionRating)
class QuestionRatingAdmin(admin.ModelAdmin):
    list_display = ('question', 'user', 'rating', 'created_at')
