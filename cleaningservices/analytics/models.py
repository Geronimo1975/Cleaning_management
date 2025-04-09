from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from contracts.models import Contract
from timetracking.models import TimeRecord


class DashboardSavedView(models.Model):
    """Saved dashboard view configuration."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_views')
    name = models.CharField(max_length=255)
    configuration = models.JSONField(default=dict)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Dashboard Saved View')
        verbose_name_plural = _('Dashboard Saved Views')

    def __str__(self):
        return f"{self.name} ({self.user.get_full_name()})"


class AnalyticsReport(models.Model):
    """Analytics report with configurable parameters."""
    REPORT_TYPE_CHOICES = [
        ('time_tracking', 'Time Tracking Report'),
        ('contract', 'Contract Report'),
        ('cleaner', 'Cleaner Performance Report'),
        ('revenue', 'Revenue Report'),
    ]
    
    PERIOD_CHOICES = [
        ('custom', 'Custom Date Range'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
    ]
    
    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics_reports')
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    period = models.CharField(max_length=50, choices=PERIOD_CHOICES, default='custom')
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Filters
    company = models.ForeignKey(
        'accounts.CompanyProfile', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='analytics_reports',
        help_text=_('Filter report by company')
    )
    cleaner = models.ForeignKey(
        'accounts.CleanerProfile', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='analytics_reports',
        help_text=_('Filter report by cleaner')
    )
    
    # Additional parameters as JSON
    parameters = models.JSONField(default=dict, blank=True)
    
    # Report data
    data = models.JSONField(default=dict, blank=True)
    pdf_report = models.FileField(upload_to='analytics/reports/', null=True, blank=True)
    
    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, null=True, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Analytics Report')
        verbose_name_plural = _('Analytics Reports')

    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"