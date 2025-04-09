from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from django.db.models import F

from .models import Notification

@login_required
def notification_list(request):
    """Display all notifications for the current user."""
    notifications = request.user.notifications.all()
    
    return render(request, 'notifications/list.html', {
        'notifications': notifications,
    })

@login_required
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if is_ajax:
        return JsonResponse({
            'success': True,
            'redirect_url': notification.action_url or request.META.get('HTTP_REFERER', '/')
        })
    
    # If not ajax, redirect to the notification's action URL if available, otherwise stay on the current page
    if notification.action_url:
        return redirect(notification.action_url)
    return redirect('notification_list')

@login_required
@require_POST
def mark_all_read(request):
    """Mark all notifications as read for the current user."""
    unread_count = request.user.notifications.filter(read=False).count()
    request.user.notifications.filter(read=False).update(read=True, read_at=timezone.now())
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if is_ajax:
        return JsonResponse({
            'success': True,
            'count': unread_count
        })
    
    messages.success(request, f"{unread_count} notifications marked as read.")
    return redirect('notification_list')

@login_required
def get_recent_notifications(request):
    """API endpoint to get recent notifications for the dropdown."""
    notifications = request.user.notifications.all()[:5]
    unread_count = request.user.notifications.filter(read=False).count()
    
    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message[:100] + ('...' if len(notification.message) > 100 else ''),
            'notification_type': notification.notification_type,
            'created_at': notification.created_at.strftime('%b %d, %Y') + ' (' + 
                          notification.created_at.strftime('%I:%M %p') + ')',
            'read': notification.read,
            'action_url': notification.action_url,
        })
    
    return JsonResponse({
        'notifications': notification_data,
        'unread_count': unread_count
    })

@login_required
def get_unread_count(request):
    """API endpoint to get only the count of unread notifications."""
    count = request.user.notifications.filter(read=False).count()
    return JsonResponse({'count': count})