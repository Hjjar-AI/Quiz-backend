"""Shared validation for knowledge-object model and API writes."""

import re
from numbers import Integral

from django.core.exceptions import ValidationError

from apps.core.model_validation import require


def normalize_knowledge_translations(value):
    require(isinstance(value, dict), 'translations', 'Translations must be an object.')
    limits = {'title': 200, 'learning_objective': 3000, 'canonical_answer': 3000}
    cleaned = {}
    for locale, content in value.items():
        require(
            isinstance(locale, str) and bool(re.fullmatch(r'[a-zA-Z]{2,3}(?:[-_][a-zA-Z]{2})?', locale.strip())),
            'translations', 'Invalid translation locale.',
        )
        locale = locale.strip().replace('_', '-').lower()
        require(locale not in cleaned, 'translations', 'Duplicate translation locale.')
        require(
            isinstance(content, dict) and not (set(content) - set(limits)),
            'translations', 'Invalid translation fields.',
        )
        normalized = {}
        for field, text in content.items():
            require(
                isinstance(text, str) and len(text.strip()) <= limits[field],
                'translations', f'Invalid or oversized translated {field}.',
            )
            if text.strip():
                normalized[field] = text.strip()
        cleaned[locale] = normalized
    return cleaned


def validate_knowledge_object(obj):
    for field, limit in (('title', 200), ('learning_objective', 3000)):
        value = getattr(obj, field)
        require(
            isinstance(value, str) and bool(value.strip()) and len(value) <= limit,
            field, f'A nonblank value of at most {limit} characters is required.',
        )
    require(
        isinstance(obj.canonical_answer, str) and len(obj.canonical_answer) <= 3000,
        'canonical_answer', 'Canonical answer must be text of at most 3000 characters.',
    )
    for field in ('key_facts', 'misconceptions'):
        value = getattr(obj, field)
        require(
            isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value),
            field, 'Must be a list of nonblank text values.',
        )
    require(obj.status in dict(obj.STATUS_CHOICES), 'status', 'Invalid knowledge status.')
    if obj.source_page is not None:
        require(
            isinstance(obj.source_page, Integral) and not isinstance(obj.source_page, bool)
            and obj.source_page >= 1,
            'source_page', 'Source page must be a positive integer.',
        )
    normalize_knowledge_translations(obj.translations)
