"""Shared limits for explicit question selections (filter exports are unchanged)."""
from django.conf import settings


MAX_MANUAL_FLAT_EXPORT_QUESTIONS = 10000


def manual_export_limit(fmt):
    if fmt == 'pdf':
        return getattr(settings, 'PDF_EXPORT_MAX_QUESTIONS', 1000)
    return MAX_MANUAL_FLAT_EXPORT_QUESTIONS
