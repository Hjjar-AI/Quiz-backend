# backend/apps/learning/models.py
from django.db import models
from django.utils import timezone
import math
from apps.core.model_validation import InvariantValidationMixin, require, validate_counts


class UserQuestionAttempt(InvariantValidationMixin, models.Model):
    ERROR_REASON_CHOICES = [
        ('unknown', 'Did not know the answer'),
        ('misread', 'Misread the question'),
        ('confused', 'Confused between two choices'),
        ('guessed', 'Guessed'),
    ]

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='question_attempts',
    )
    question = models.ForeignKey(
        'questions.Question',
        on_delete=models.CASCADE,
        related_name='user_attempts',
    )
    last_correct = models.BooleanField(default=False)
    last_confidence = models.BooleanField(
        default=True,
        help_text='True if the user was confident in their last answer.',
    )
    last_confidence_score = models.PositiveSmallIntegerField(
        default=3,
        help_text='Confidence score: 1=guessing, 2=uncertain, 3=confident.',
    )
    last_error_reason = models.CharField(
        max_length=20,
        choices=ERROR_REASON_CHOICES,
        null=True,
        blank=True,
        help_text=(
            'Set on a wrong answer via the reflection prompt. Null when '
            'the last answer was correct or the user skipped the prompt.'
        ),
    )
    last_answered_at = models.DateTimeField(default=timezone.now)
    attempts = models.IntegerField(default=0)
    wrong_count = models.IntegerField(default=0)
    ever_correct = models.BooleanField(default=False)
    ease_factor = models.FloatField(default=2.5)
    interval_days = models.IntegerField(default=0)
    repetitions = models.IntegerField(default=0)
    next_due = models.DateTimeField(null=True, blank=True, db_index=True)

    def validate_invariants(self):
        validate_counts(self, 'attempts', 'wrong_count', 'interval_days', 'repetitions')
        require(
            self.wrong_count <= self.attempts,
            'wrong_count', 'Wrong answers cannot exceed attempts.',
        )
        require(
            self.ever_correct == (self.attempts > self.wrong_count),
            'ever_correct', 'Correct-answer history must agree with the attempt counters.',
        )
        require(
            self.repetitions <= self.attempts - self.wrong_count
            and (self.last_correct or self.repetitions == 0),
            'repetitions', 'Successful repetitions must agree with the answer history.',
        )
        require(
            not self.last_correct or self.ever_correct,
            'ever_correct', 'A correct last answer requires ever_correct.',
        )
        require(
            not self.last_correct or not self.last_error_reason,
            'last_error_reason', 'A correct answer cannot have an error reason.',
        )
        validate_counts(self, 'last_confidence_score')
        require(
            1 <= self.last_confidence_score <= 3
            and self.last_confidence == (self.last_confidence_score == 3),
            'last_confidence_score', 'Confidence score and confidence flag must agree.',
        )
        require(
            isinstance(self.ease_factor, (int, float)) and math.isfinite(self.ease_factor)
            and self.ease_factor >= 1.3,
            'ease_factor', 'Ease factor must be finite and at least 1.3.',
        )
        require(
            self.last_error_reason in (None, '', *dict(self.ERROR_REASON_CHOICES)),
            'last_error_reason', 'Invalid error reason.',
        )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'question'],
                name='uqa_unique_per_user_question',
            ),
            # The SRS engine never writes a negative counter. The DB
            # enforces it so a migration, manual SQL, or a future
            # refactor cannot slip a negative value past the model
            # layer and corrupt the due-date computation.
            models.CheckConstraint(
                condition=models.Q(attempts__gte=0),
                name='uqa_attempts_non_negative',
            ),
            models.CheckConstraint(
                condition=models.Q(wrong_count__gte=0),
                name='uqa_wrong_count_non_negative',
            ),
            # SM-2 also produces these invariants: repetitions and
            # interval_days are non-negative, ease_factor is at least
            # EASE_FLOOR (1.3). Constraint-elevating them catches a
            # future edit that forgets the `max(EASE_FLOOR, ...)` line
            # in srs_service._apply_review.
            models.CheckConstraint(
                condition=models.Q(repetitions__gte=0),
                name='uqa_repetitions_non_negative',
            ),
            models.CheckConstraint(
                condition=models.Q(interval_days__gte=0),
                name='uqa_interval_days_non_negative',
            ),
            models.CheckConstraint(
                condition=models.Q(ease_factor__gte=1.3),
                name='uqa_ease_factor_floor',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(last_confidence_score__gte=1)
                    & models.Q(last_confidence_score__lte=3)
                ),
                name='uqa_confidence_score_range',
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'next_due'], name='uqa_user_due_idx'),
            models.Index(fields=['user', 'ever_correct'], name='uqa_user_evercorrect_idx'),
        ]
        ordering = ['-last_answered_at']

    def __str__(self):
        mark = '✓' if self.last_correct else '✗'
        return f"{self.user.username} · Q{self.question_id} · {mark}"
