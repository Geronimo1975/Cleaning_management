from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class Notification(models.Model):
    """
    Model for storing notifications.
    """
    
    class NotificationType(models.TextChoices):
        JOB = 'JOB', _('Job')
        DOCUMENT = 'DOCUMENT', _('Document')
        PAYMENT = 'PAYMENT', _('Payment')
        MESSAGE = 'MESSAGE', _('Message')
        SYSTEM = 'SYSTEM', _('System')
    
    # Who the notification is for
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    # The notification content
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )
    
    # Optional link related to the notification
    action_url = models.CharField(max_length=255, blank=True, null=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type}: {self.title} (for {self.user.username})"
    
    def mark_as_read(self):
        """Mark the notification as read if it's not already."""
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save(update_fields=['read', 'read_at'])
    
    @classmethod
    def create_notification(cls, user, title, message, notification_type=NotificationType.SYSTEM, action_url=None):
        """
        Helper method to create a notification.
        """
        notification = cls(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            action_url=action_url
        )
        notification.save()
        return notification