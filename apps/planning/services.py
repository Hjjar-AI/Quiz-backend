# backend/apps/planning/services.py

from datetime import datetime, time, timedelta

from django.utils import timezone
from django.db import transaction
from django.db.models import F

from apps.exams.models import TestHistory
from apps.master_exams.models import MasterExamAttempt
from apps.questions.models import Tag, clean_tag_name

from .models import StudyPlanner, StudyPlannerDay


class StudyPlannerService:

    @staticmethod
    def get_or_create_planner(user):
        planner, created = StudyPlanner.objects.get_or_create(user=user)
        return planner

    @staticmethod
    @transaction.atomic
    def update_planner(user, target, category_ids, tag_names, start_date, end_date):
        """
        Replace the planner's configuration.

        `category_ids` is a list of category ids. Ids that do not
        resolve to a live Category are silently dropped.
        `tag_names` is a list of tag names. Names that do not resolve
        to an existing Tag are created on the fly — this matches the
        previous behaviour where target_tags was a free-form list of
        names.

        Both lists are treated as full replacements: whatever was
        there before is cleared and replaced with the incoming set.
        """
        # Match tag merges: hierarchy first, then planner and its FK links.
        from apps.questions.hierarchy import lock_tag_hierarchy
        lock_tag_hierarchy()
        planner, _ = StudyPlanner.objects.select_for_update().get_or_create(user=user)
        old_scope = (
            set(planner.target_categories.values_list('pk', flat=True)),
            set(planner.target_tags.values_list('name', flat=True)),
            planner.start_date, planner.end_date,
        )
        planner.target_questions_per_day = target
        planner.start_date = start_date
        planner.end_date = end_date
        planner.save(update_fields=[
            'target_questions_per_day', 'start_date', 'end_date', 'updated_at',
        ])

        # ── Categories ────────────────────────────────────────────
        if category_ids:
            from apps.questions.models import Category
            cats = Category.objects.filter(id__in=category_ids)
            planner.target_categories.set(cats)
        else:
            planner.target_categories.clear()

        # ── Tags ──────────────────────────────────────────────────
        if tag_names:
            tag_objects = []
            seen = set()
            for raw in tag_names:
                name = clean_tag_name(str(raw))
                if not name or name in seen:
                    continue
                seen.add(name)
                tag, _ = Tag.objects.get_or_create(name=name)
                tag_objects.append(tag)
            planner.target_tags.set(tag_objects)
        else:
            planner.target_tags.clear()

        new_scope = (
            set(planner.target_categories.values_list('pk', flat=True)),
            set(planner.target_tags.values_list('name', flat=True)),
            planner.start_date, planner.end_date,
        )
        if old_scope != new_scope:
            # Earlier activity belongs to the earlier plan. A scope/window
            # change starts today's new plan at zero; target-only edits retain
            # progress. Keep previous days as historical records.
            StudyPlannerDay.objects.update_or_create(
                planner=planner, date=timezone.localdate(),
                defaults={'questions_answered': 0},
            )

        return planner

    @staticmethod
    @transaction.atomic
    def record_learning_progress(user, results, occurred_at=None):
        """Credit each committed learning event, including unfinished study.

        Session writers call this once under their existing idempotency locks.
        The daily ledger retains progress after a session is discarded.
        """
        planner, _ = StudyPlanner.objects.select_for_update().get_or_create(user=user)
        category_ids = set(planner.target_categories.values_list('pk', flat=True))
        tag_names = set(planner.target_tags.values_list('name', flat=True))
        targeted = bool(category_ids or tag_names)
        counts = {}
        for result in results:
            day = timezone.localdate(result.get('_occurred_at') or occurred_at) if result.get('_occurred_at') or occurred_at else timezone.localdate()
            if day < planner.start_date or (planner.end_date and day > planner.end_date):
                continue
            if result.get('user_answer') is not None and (not targeted or result.get('category_id') in category_ids or bool(set(result.get('tag_names') or []) & tag_names)):
                counts[day] = counts.get(day, 0) + 1
        for day, count in counts.items():
            StudyPlannerDay.objects.get_or_create(planner=planner, date=day, defaults={'questions_answered': 0})
            StudyPlannerDay.objects.filter(planner=planner, date=day).update(questions_answered=F('questions_answered') + count)
        return sum(counts.values())

    @staticmethod
    @transaction.atomic
    def record_daily_progress(user):
        """Read today's durable ledger, or reconstruct it from learning events.

        Ordinary, offline and master learning contribute. When category/tag
        targets exist, only answered events matching either target count.
        """
        today = timezone.localdate()

        planner, _ = StudyPlanner.objects.select_for_update().prefetch_related(
            'target_categories', 'target_tags',
        ).get_or_create(user=user)

        # New activity is credited by the session writer. Recomputing from
        # completed histories would erase paused/discarded learning events.
        day = StudyPlannerDay.objects.filter(planner=planner, date=today).first()
        if day is not None:
            return day.questions_answered

        # A dated plan does not accrue progress before it starts or after it
        # ends. This prevents old/general activity from satisfying a new plan.
        in_window = (
            today >= planner.start_date
            and (planner.end_date is None or today <= planner.end_date)
        )
        answered_today = 0
        if in_window:
            local_tz = timezone.get_current_timezone()
            day_start = timezone.make_aware(datetime.combine(today, time.min), local_tz)
            day_end = day_start + timedelta(days=1)
            category_ids = set(
                planner.target_categories.values_list('id', flat=True)
            )
            tag_names = set(
                planner.target_tags.values_list('name', flat=True)
            )
            is_targeted = bool(category_ids or tag_names)

            from apps.learning.models import LearningEvent
            events = LearningEvent.objects.filter(user=user, occurred_at__gte=day_start, occurred_at__lt=day_end)
            for event in events:
                if not is_targeted or event.category_id_snapshot in category_ids or bool(set(event.tag_names) & tag_names):
                    answered_today += 1

        # Fast path: the (planner, date) row exists. A single UPDATE
        # against the indexed pair.
        updated = (
            StudyPlannerDay.objects
            .filter(planner__user=user, date=today)
            .update(questions_answered=answered_today)
        )

        # Slow path: first study day for this account, or the day
        # row was manually removed. Set up the planner, then insert
        # the day.
        if not updated:
            StudyPlannerDay.objects.update_or_create(
                planner=planner,
                date=today,
                defaults={'questions_answered': answered_today},
            )

        return answered_today

    @staticmethod
    def delete_planner(user):
        # Cascades to StudyPlannerDay via the FK.
        StudyPlanner.objects.filter(user=user).delete()
