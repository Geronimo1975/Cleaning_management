from django.contrib import admin
from .models import DashboardSavedView, AnalyticsReport


@admin.register(DashboardSavedView)
class DashboardSavedViewAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_default', 'created_at', 'updated_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('name', 'user__username', 'user__email')
    date_hierarchy = 'created_at'


@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'report_type', 'period', 'start_date', 'end_date', 'is_scheduled', 'created_at')
    list_filter = ('report_type', 'period', 'is_scheduled', 'created_at')
    search_fields = ('title', 'user__username', 'user__email')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'last_run', 'next_run')
    fieldsets = (
        (None, {
            'fields': ('title', 'user', 'report_type', 'period', 'start_date', 'end_date')
        }),
        ('Filters', {
            'fields': ('company', 'cleaner', 'parameters')
        }),
        ('Report Data', {
            'fields': ('data', 'pdf_report')
        }),
        ('Scheduling', {
            'fields': ('is_scheduled', 'schedule_frequency', 'last_run', 'next_run')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )