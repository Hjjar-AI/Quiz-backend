# backend/apps/exams/views/__init__.py
"""
Package surface for the exam views.

`apps/exams/urls.py` does `from . import views` and references every
view class through the module namespace. `config/urls.py` imports
`TestHistoryView` directly. Both import paths keep working after the
split from a single `views.py` module into this package, because
every public view class is re-exported here.
"""

from .session_views import (
    StartSessionView,
    GetQuestionView,
    SubmitAnswerView,
    FinishSessionView,
    PauseSessionView,
    ResumeSessionView,
    DiscardProgressView,
    StatusView,
)
from .history_views import TestHistoryView, TestHistoryDetailView
from .blueprint_views import BlueprintListView, BlueprintDetailView


__all__ = [
    'OfflinePackView',
    'OfflineCompletionView',
    # Session runner
    'StartSessionView',
    'GetQuestionView',
    'SubmitAnswerView',
    'FinishSessionView',
    'PauseSessionView',
    'ResumeSessionView',
    'DiscardProgressView',
    'StatusView',
    # History
    'TestHistoryView',
    'TestHistoryDetailView',
    # Blueprints
    'BlueprintListView',
    'BlueprintDetailView',
]

from .offline_views import OfflinePackView, OfflineCompletionView, OfflineCatalogView
