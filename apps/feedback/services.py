# backend/apps/feedback/services.py

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.users.models import User

from .models import Bookmark, QuestionFlag


class FeedbackService:

    @staticmethod
    @transaction.atomic
    def toggle_bookmark(user_id, question_id):
        User.objects.select_for_update().only('id').get(pk=user_id)
        bookmark = Bookmark.objects.select_for_update().filter(
            user_id=user_id, question_id=question_id,
        ).first()
        if bookmark is not None:
            bookmark.delete()
            return False
        Bookmark.objects.create(user_id=user_id, question_id=question_id)
        return True

    @staticmethod
    @transaction.atomic
    def flag_question(user_id, question_id, reason=None, master_exam_attempt=None):
        """Serialize open-flag creation even without partial unique indexes."""
        User.objects.select_for_update().only('id').get(pk=user_id)
        open_flags = QuestionFlag.objects.select_for_update().filter(
            user_id=user_id,
            question_id=question_id,
            resolved=False,
        )
        if open_flags.first() is not None:
            return False

        try:
            with transaction.atomic():
                QuestionFlag.objects.create(
                    user_id=user_id,
                    question_id=question_id,
                    reason=reason,
                    master_exam_attempt=master_exam_attempt,
                )
            return True
        except IntegrityError:
            # Preserve protection against writers outside this service where
            # a partial unique index exists; do not hide unrelated failures.
            if open_flags.first() is not None:
                return False
            raise

    @staticmethod
    def resolve_flag(flag_id, moderator):
        """Keep the first moderator's resolution when requests are repeated."""
        return bool(FeedbackService.resolve_flags(
            QuestionFlag.objects.filter(pk=flag_id), moderator,
        ))

    @staticmethod
    def resolve_flags(queryset, moderator):
        now = timezone.now()
        return queryset.filter(resolved=False).update(
            resolved=True, resolved_by=moderator.username,
            resolved_at=now, updated_at=now,
        )
