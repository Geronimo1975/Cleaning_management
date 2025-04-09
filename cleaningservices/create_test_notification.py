import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cleaningservices.settings')
django.setup()

from notifications.models import Notification
from accounts.models import User


def create_test_notification():
    """Create a test notification for the first user."""
    user = User.objects.first()
    if not user:
        print("No users found in the database.")
        return
    
    print(f"Creating notification for user: {user.email}")
    notification = Notification.objects.create(
        user=user,
        title='Welcome to CleanConnect',
        message='Thank you for joining our platform. We hope you enjoy our services.',
        notification_type='SYSTEM'
    )
    print(f"Notification created with ID: {notification.id}")


if __name__ == '__main__':
    create_test_notification()