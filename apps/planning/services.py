# backend/apps/planning/services.py

from datetime import datetime, time, timedelta

from django.utils import timezone
from django.db import transaction
from django.db.models import F, Sum

from apps.questions.models import Tag, clean_tag_name

from .models import StudyPlanner, StudyPlannerDay, StudyPlannerScope, StudyPlannerScopeDay


class StudyPlannerService:

    @staticmethod
    def _snapshot(planner):
        return {'category_ids': sorted(planner.target_categories.values_list('pk',flat=True)),
                'tag_names': sorted(planner.target_tags.values_list('name',flat=True)),
                'start_date':planner.start_date,'end_date':planner.end_date}

    @staticmethod
    def _scope(planner):
        scope=planner.scope_history.filter(ended_at__isnull=True).order_by('-pk').first()
        if scope is None:
            scope=StudyPlannerScope.objects.create(planner=planner,**StudyPlannerService._snapshot(planner))
            # Retain the existing ledger when first introducing scope history.
            StudyPlannerScopeDay.objects.bulk_create([StudyPlannerScopeDay(scope=scope,date=day.date,questions_answered=day.questions_answered) for day in planner.days.all()])
        return scope

    @staticmethod
    def record_scope_change(planner, retain_today=False):
        scope=StudyPlannerService._scope(planner)
        snapshot=StudyPlannerService._snapshot(planner)
        if all(getattr(scope,key)==value for key,value in snapshot.items()): return scope
        now=timezone.now();today=timezone.localdate()
        old_count=StudyPlannerService._project_count(planner,today)
        scope.ended_at=now;scope.save(update_fields=['ended_at'])
        fresh=StudyPlannerScope.objects.create(planner=planner,effective_at=now,reset_progress=not retain_today,**snapshot)
        # Metadata-only taxonomy changes can retain today's displayed progress.
        StudyPlannerScopeDay.objects.create(scope=fresh,date=today,questions_answered=0)
        StudyPlannerDay.objects.update_or_create(planner=planner,date=today,defaults={'questions_answered':old_count if retain_today else 0})
        return fresh

    @staticmethod
    def _project_count(planner, day):
        rows=StudyPlannerScopeDay.objects.filter(scope__planner=planner,date=day)
        if day==timezone.localdate():
            boundary=planner.scope_history.filter(reset_progress=True).order_by('-pk').first()
            if boundary is not None: rows=rows.filter(scope_id__gte=boundary.pk)
        return rows.aggregate(value=Sum('questions_answered'))['value'] or 0

    @staticmethod
    def _matches(scope, when, category, tags):
        day=timezone.localdate(when)
        return day>=scope.start_date and (scope.end_date is None or day<=scope.end_date) and (
            not (scope.category_ids or scope.tag_names) or category in scope.category_ids or bool(set(tags or []) & set(scope.tag_names)))

    @staticmethod
    def get_or_create_planner(user):
        planner, created = StudyPlanner.objects.get_or_create(user=user)
        return planner

    @staticmethod
    @transaction.atomic
    def update_planner(user, target, category_ids, tag_names, start_date, end_date, *, expected_version, expected_id):
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
        from apps.core.revisions import check_revision
        if planner.pk != expected_id:
            from apps.core.exceptions import RevisionConflict
            raise RevisionConflict()
        check_revision(planner.version,expected_version)
        StudyPlannerService._scope(planner)
        planner._scope_update_in_progress=True
        planner.version += 1
        planner.target_questions_per_day = target
        planner.start_date = start_date
        planner.end_date = end_date
        planner.save(update_fields=[
            'target_questions_per_day', 'start_date', 'end_date', 'updated_at','version',
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

        StudyPlannerService.record_scope_change(planner)
        planner.refresh_from_db()

        return planner

    @staticmethod
    @transaction.atomic
    def record_learning_progress(user, results, occurred_at=None):
        """Credit each committed learning event, including unfinished study.

        Session writers call this once under their existing idempotency locks.
        The daily ledger retains progress after a session is discarded.
        """
        planner, _ = StudyPlanner.objects.select_for_update().get_or_create(user=user)
        StudyPlannerService._scope(planner)
        scopes=list(planner.scope_history.order_by('-pk'))
        total=0; changed=set()
        for result in results:
            when=result.get('_occurred_at') or occurred_at or timezone.now()
            scope=next((row for row in scopes if (row.effective_at is None or when>=row.effective_at) and (row.ended_at is None or when<row.ended_at)),None)
            if scope is None or result.get('user_answer') is None or not StudyPlannerService._matches(scope,when,result.get('category_id'),result.get('tag_names')): continue
            day=timezone.localdate(when)
            StudyPlannerScopeDay.objects.get_or_create(scope=scope,date=day)
            StudyPlannerScopeDay.objects.filter(scope=scope,date=day).update(questions_answered=F('questions_answered')+1)
            changed.add(day);total+=1
        for day in changed:
            count=StudyPlannerService._project_count(planner,day)
            StudyPlannerDay.objects.update_or_create(planner=planner,date=day,defaults={'questions_answered':count})
        return total

    @staticmethod
    @transaction.atomic
    def record_daily_progress(user):
        """Read today's durable ledger, or reconstruct it from learning events.

        Ordinary, offline and master learning contribute. When category/tag
        targets exist, only answered events matching either target count.
        """
        today=timezone.localdate()
        planner,_=StudyPlanner.objects.select_for_update().get_or_create(user=user)
        scope=StudyPlannerService._scope(planner)
        saved=scope.days.filter(date=today).first()
        if saved is not None: return StudyPlannerService._project_count(planner,today)
        from apps.learning.models import LearningEvent
        day_start=timezone.make_aware(datetime.combine(today,time.min));day_end=day_start+timedelta(days=1)
        events=LearningEvent.objects.filter(user=user,occurred_at__gte=day_start,occurred_at__lt=day_end)
        if scope.effective_at is not None: events=events.filter(occurred_at__gte=scope.effective_at)
        count=sum(StudyPlannerService._matches(scope,event.occurred_at,event.category_id_snapshot,event.tag_names) for event in events)
        StudyPlannerScopeDay.objects.update_or_create(scope=scope,date=today,defaults={'questions_answered':count})
        StudyPlannerDay.objects.update_or_create(planner=planner,date=today,defaults={'questions_answered':count})
        return count

    @staticmethod
    @transaction.atomic
    def delete_planner(user, *, expected_version, expected_id):
        from apps.core.revisions import check_revision
        from django.shortcuts import get_object_or_404
        planner=get_object_or_404(StudyPlanner.objects.select_for_update(),user=user,pk=expected_id)
        check_revision(planner.version,expected_version)
        planner.delete()
