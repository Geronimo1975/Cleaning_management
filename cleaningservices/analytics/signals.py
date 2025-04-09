from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import AnalyticsReport


@receiver(post_save, sender=AnalyticsReport)
def set_next_run_date(sender, instance, created, **kwargs):
    """
    Set the next run date for scheduled reports after saving.
    """
    if created and instance.is_scheduled and not instance.next_run:
        from .views import calculate_next_run
        
        instance.next_run = calculate_next_run(instance.schedule_frequency)
        # Use update to avoid recursive signal triggering
        type(instance).objects.filter(pk=instance.pk).update(next_run=instance.next_run)