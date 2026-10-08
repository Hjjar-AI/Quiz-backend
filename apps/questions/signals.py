"""Preserve dependent state for API, admin and queryset deletions."""

from django.db.models.deletion import ProtectedError
from django.db.models.signals import m2m_changed, post_delete, pre_delete
from django.dispatch import receiver
from apps.planning.models import StudyPlanner

from .models import Category, ClinicalCase, KnowledgeObject, Question, Tag


@receiver(pre_delete, sender=ClinicalCase)
@receiver(pre_delete, sender=KnowledgeObject)
def capture_detached_questions(sender, instance, using, **kwargs):
    field = 'case_id' if sender is ClinicalCase else 'knowledge_object_id'
    # SET_NULL is executed by Django's collector before post_delete. Locking
    # questions here serializes linkage/review writes and freezes this set.
    questions = Question.objects.using(using).select_for_update().filter(
        **{field: instance.pk},
    ).order_by('pk')
    list(questions.values_list('pk', flat=True))
    # Prevent new FK links while the collector detaches these questions.
    list(sender.objects.using(using).select_for_update().filter(pk=instance.pk))
    instance._detached_learning_ids = list(questions.values_list('pk', flat=True))


@receiver(post_delete, sender=ClinicalCase)
@receiver(post_delete, sender=KnowledgeObject)
def invalidate_detached_learning(sender, instance, using, **kwargs):
    from apps.learning.evidence import invalidate_question_learning
    invalidate_question_learning(instance._detached_learning_ids, using=using)


@receiver(pre_delete, sender=Tag)
@receiver(pre_delete, sender=Category)
def protect_planner_targets(sender, instance, using, **kwargs):
    if sender is Tag:
        from .hierarchy import lock_tag_hierarchy
        lock_tag_hierarchy(using)
    # Share the taxonomy row lock with M2M additions so a concurrent planner
    # cannot acquire a target after this protection check.
    list(sender.objects.using(using).select_for_update().filter(pk=instance.pk))
    relation = 'target_tags' if sender is Tag else 'target_categories'
    planners = StudyPlanner.objects.using(using).filter(**{relation: instance.pk})
    through = getattr(StudyPlanner, relation).through
    field = 'tag_id' if sender is Tag else 'category_id'
    # Locking reads also avoid stale repeatable-read snapshots on MariaDB.
    if list(through.objects.using(using).select_for_update()
            .filter(**{field: instance.pk}).values_list('pk', flat=True)):
        raise ProtectedError('Remove or replace this study planner target before deletion.', planners)


def lock_planner_targets(sender, instance, action, reverse, model, pk_set, using, **kwargs):
    if action != 'pre_add' or not pk_set:
        return
    taxonomy = Tag if sender is _tag_targets else Category
    if taxonomy is Tag:
        from .hierarchy import lock_tag_hierarchy
        lock_tag_hierarchy(using)
    ids = [instance.pk] if reverse else pk_set
    list(taxonomy.objects.using(using).select_for_update().filter(pk__in=ids).order_by('pk'))


_tag_targets = StudyPlanner.target_tags.through
m2m_changed.connect(lock_planner_targets, sender=_tag_targets, dispatch_uid='lock_planner_tag_targets')
m2m_changed.connect(lock_planner_targets, sender=StudyPlanner.target_categories.through,
                    dispatch_uid='lock_planner_category_targets')
