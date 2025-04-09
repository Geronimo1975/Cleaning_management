from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Notification

User = get_user_model()

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin configuration for Notification model."""
    
    list_display = (
        'id', 
        'notification_type',
        'title',
        'user_display',
        'created_at', 
        'read',
        'mark_as_read_action'
    )
    list_filter = ('notification_type', 'read', 'created_at')
    search_fields = ('title', 'message', 'user__email', 'user__username')
    readonly_fields = ('created_at', 'read_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'notification_type', 'title', 'message')
        }),
        ('Status', {
            'fields': ('read', 'read_at')
        }),
        ('Actions', {
            'fields': ('action_url',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def user_display(self, obj):
        """Display user's name and email."""
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.email})"
        return "Unknown user"
    user_display.short_description = "User"
    
    def mark_as_read_action(self, obj):
        """Custom action to mark notification as read."""
        if obj.read:
            return "✓ Read"
        return "⚠ Unread"
    mark_as_read_action.short_description = "Status"
    
    actions = ['mark_selected_as_read']
    
    def mark_selected_as_read(self, request, queryset):
        """Admin action to mark selected notifications as read."""
        updated = queryset.filter(read=False).update(read=True, read_at=timezone.now())
        self.message_user(request, f"{updated} notifications marked as read.")
    mark_selected_as_read.short_description = "Mark selected notifications as read"
    
    def get_queryset(self, request):
        """Add prefetch for related user objects."""
        return super().get_queryset(request).select_related('user')