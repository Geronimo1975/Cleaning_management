from django.apps import AppConfig


class TimetrackingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'timetracking'
    verbose_name = 'Time & Location Tracking'

    def ready(self):
        try:
            import timetracking.signals  # noqa
        except ImportError:
            pass