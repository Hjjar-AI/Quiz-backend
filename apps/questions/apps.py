from django.apps import AppConfig


class QuestionsConfig(AppConfig):
    name = 'apps.questions'

    def ready(self):
        from . import signals  # noqa: F401
