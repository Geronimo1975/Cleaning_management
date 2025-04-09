from django.urls import path
from . import views

urlpatterns = [
    # Main notification pages
    path('', views.notification_list, name='notification_list'),
    path('<int:notification_id>/mark-read/', views.mark_notification_read, name='notification_mark_read'),
    path('mark-all-read/', views.mark_all_read, name='notification_mark_all_read'),
    
    # API endpoints for AJAX
    path('api/recent/', views.get_recent_notifications, name='notification_api_recent'),
    path('api/unread-count/', views.get_unread_count, name='notification_api_unread_count'),
]