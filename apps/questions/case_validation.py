"""Optional, partial translations for a shared clinical vignette."""
import re


def normalize_case_translations(value):
    from .models import CASE_STEM_MAX_LENGTH
    if not isinstance(value, dict):
        raise ValueError('Case translations must be an object keyed by locale.')
    limits = {'title': 200, 'stem': CASE_STEM_MAX_LENGTH}
    cleaned = {}
    seen = set()
    for locale, content in value.items():
        if not isinstance(locale, str) or not re.fullmatch(r'[a-zA-Z]{2,3}(?:[-_][a-zA-Z]{2})?', locale.strip()):
            raise ValueError('Invalid case translation locale.')
        locale = locale.strip().replace('_', '-').lower()
        if locale in seen:
            raise ValueError('Duplicate case translation locale.')
        seen.add(locale)
        if not isinstance(content, dict) or set(content) - set(limits):
            raise ValueError('Case translations support title and stem only.')
        fields = {}
        for field, text in content.items():
            if not isinstance(text, str) or len(text.strip()) > limits[field]:
                raise ValueError(f'Invalid or oversized translated case {field}.')
            if text.strip():
                fields[field] = text.strip()
        if fields:
            cleaned[locale] = fields
    return cleaned
