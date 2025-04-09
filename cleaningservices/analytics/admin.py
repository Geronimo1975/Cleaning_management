from django.contrib import admin
from .models import DashboardSavedView, AnalyticsReport, ChartConfiguration, AnalyticsWidget


@admin.register(DashboardSavedView)
class DashboardSavedViewAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_default', 'created_at', 'updated_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('name', 'user__username', 'user__email')
    date_hierarchy = 'created_at'


@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'report_type', 'period', 'start_date', 'end_date', 'is_scheduled', 'is_public', 'created_at')
    list_filter = ('report_type', 'period', 'is_scheduled', 'is_public', 'created_at')
    search_fields = ('title', 'user__username', 'user__email')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'last_run', 'next_run', 'access_token')
    filter_horizontal = ('shared_with',)
    fieldsets = (
        (None, {
            'fields': ('title', 'user', 'report_type', 'period', 'start_date', 'end_date')
        }),
        ('Filters', {
            'fields': ('company', 'cleaner', 'parameters')
        }),
        ('Report Data', {
            'fields': ('data', 'pdf_report', 'excel_report', 'csv_report', 'preferred_formats')
        }),
        ('Scheduling', {
            'fields': ('is_scheduled', 'schedule_frequency', 'last_run', 'next_run')
        }),
        ('Sharing', {
            'fields': ('is_public', 'access_token', 'shared_with'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ChartConfiguration)
class ChartConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'chart_type', 'is_public', 'created_at', 'updated_at')
    list_filter = ('chart_type', 'is_public', 'created_at')
    search_fields = ('name', 'user__username', 'user__email')
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': ('name', 'user', 'chart_type', 'is_public')
        }),
        ('Configuration', {
            'fields': ('configuration',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AnalyticsWidget)
class AnalyticsWidgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'widget_type', 'refresh_interval', 'is_public', 'created_at')
    list_filter = ('widget_type', 'is_public', 'created_at')
    search_fields = ('name', 'user__username', 'user__email', 'description')
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'user', 'widget_type', 'is_public')
        }),
        ('Data Source', {
            'fields': ('data_source', 'refresh_interval')
        }),
        ('Configuration', {
            'fields': ('configuration',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')