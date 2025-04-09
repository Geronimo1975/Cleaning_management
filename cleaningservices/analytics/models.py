from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
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
        ('customer_satisfaction', 'Customer Satisfaction'),
        ('job_statistics', 'Job Statistics'),
        ('attendance', 'Attendance Report'),
        ('payroll', 'Payroll Report'),
    ]
    
    PERIOD_CHOICES = [
        ('custom', 'Custom Date Range'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF Document'),
        ('xlsx', 'Excel Spreadsheet'),
        ('csv', 'CSV File'),
        ('json', 'JSON Data'),
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
    excel_report = models.FileField(upload_to='analytics/reports/', null=True, blank=True)
    csv_report = models.FileField(upload_to='analytics/reports/', null=True, blank=True)
    
    # Preferred format(s)
    preferred_formats = models.JSONField(default=list, blank=True, 
                                        help_text=_('List of preferred export formats'))
    
    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, null=True, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    # Sharing
    is_public = models.BooleanField(default=False, 
                                   help_text=_('If enabled, report can be viewed by others with shared link'))
    access_token = models.CharField(max_length=64, null=True, blank=True, unique=True,
                                  help_text=_('Token for accessing shared report'))
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_reports')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Analytics Report')
        verbose_name_plural = _('Analytics Reports')

    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"
        
    def is_expired(self):
        """Check if a scheduled report is past its next run time."""
        if not self.is_scheduled or not self.next_run:
            return False
        return timezone.now() > self.next_run
        
    def calculate_next_run(self):
        """Calculate the next scheduled run based on frequency."""
        if not self.is_scheduled or not self.schedule_frequency:
            return None
            
        now = timezone.now()
        
        if self.schedule_frequency == 'DAILY':
            next_run = now + timezone.timedelta(days=1)
        elif self.schedule_frequency == 'WEEKLY':
            next_run = now + timezone.timedelta(weeks=1)
        elif self.schedule_frequency == 'MONTHLY':
            # Add one month (approximation)
            if now.month == 12:
                next_run = timezone.datetime(now.year + 1, 1, now.day, 
                                           now.hour, now.minute, tzinfo=now.tzinfo)
            else:
                next_run = timezone.datetime(now.year, now.month + 1, now.day,
                                           now.hour, now.minute, tzinfo=now.tzinfo)
        elif self.schedule_frequency == 'QUARTERLY':
            # Add three months (approximation)
            month = now.month + 3
            year = now.year
            if month > 12:
                month = month - 12
                year += 1
            next_run = timezone.datetime(year, month, now.day,
                                       now.hour, now.minute, tzinfo=now.tzinfo)
        else:
            return None
            
        return next_run
        
    def save(self, *args, **kwargs):
        """Override save to update next_run when scheduling is enabled."""
        if self.is_scheduled and not self.next_run:
            self.next_run = self.calculate_next_run()
        super().save(*args, **kwargs)


class ChartConfiguration(models.Model):
    """Configuration for charts used in dashboard and reports."""
    CHART_TYPE_CHOICES = [
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('doughnut', 'Doughnut Chart'),
        ('radar', 'Radar Chart'),
        ('polarArea', 'Polar Area Chart'),
        ('bubble', 'Bubble Chart'),
        ('scatter', 'Scatter Chart'),
    ]
    
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chart_configurations')
    chart_type = models.CharField(max_length=20, choices=CHART_TYPE_CHOICES)
    configuration = models.JSONField(default=dict)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Chart Configuration')
        verbose_name_plural = _('Chart Configurations')
        
    def __str__(self):
        return f"{self.name} ({self.get_chart_type_display()})"


class AnalyticsWidget(models.Model):
    """Custom analytics widget that can be added to dashboards."""
    WIDGET_TYPE_CHOICES = [
        ('chart', 'Chart Widget'),
        ('metric', 'Metric Widget'),
        ('table', 'Table Widget'),
        ('calendar', 'Calendar Widget'),
        ('status', 'Status Widget'),
        ('custom', 'Custom Widget'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_widgets')
    configuration = models.JSONField(default=dict)
    data_source = models.CharField(max_length=255, blank=True, help_text=_('API endpoint or data source'))
    refresh_interval = models.PositiveIntegerField(default=0, help_text=_('Refresh interval in seconds (0 for manual)'))
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Analytics Widget')
        verbose_name_plural = _('Analytics Widgets')
        
    def __str__(self):
        return f"{self.name} ({self.get_widget_type_display()})"