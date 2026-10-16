"""Authorization policy shared by case metadata write paths."""


def visible_cases(user):
    from django.db.models import Q
    from .models import ClinicalCase, Question

    if user is None or not getattr(user, 'is_authenticated', False):
        return ClinicalCase.objects.none()
    if user.has_capability('questions.edit_case_stem_any'):
        return ClinicalCase.objects.all()
    visible_ids = Question.objects.visible_to(user).exclude(case_id__isnull=True).values('case_id')
    return ClinicalCase.objects.filter(Q(authored_by=user) | Q(pk__in=visible_ids)).distinct()


def can_edit_case(user, case):
    if user.has_capability('questions.edit_case_stem_any'):
        return True
    return (
        user.has_capability('questions.edit_case_stem_own')
        and case.questions.filter(authored_by=user).exists()
    )
