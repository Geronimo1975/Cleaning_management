from django.db import models
from accounts.models import User, CleanerProfile, CompanyProfile


class DashboardSavedView(models.Model):
    """Model to save user dashboard configurations."""
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_dashboard_views')
    configuration = models.JSONField(help_text="JSON configuration for the dashboard layout and included widgets")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.user.get_full_name()}"


class AnalyticsReport(models.Model):
    """Model for saving generated reports."""
    REPORT_TYPES = [
        ('cleaner_performance', 'Cleaner Performance'),
        ('company_revenue', 'Company Revenue'),
        ('job_statistics', 'Job Statistics'),
        ('contract_status', 'Contract Status'),
        ('customer_satisfaction', 'Customer Satisfaction'),
        ('time_tracking', 'Time Tracking'),
        ('custom', 'Custom Report'),
    ]
    
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom Range'),
    ]
    
    title = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics_reports')
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Filters
    company = models.ForeignKey(CompanyProfile, on_delete=models.SET_NULL, null=True, blank=True)
    cleaner = models.ForeignKey(CleanerProfile, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Data
    parameters = models.JSONField(default=dict, help_text="Parameters used to generate the report")
    data = models.JSONField(default=dict, help_text="Report data")
    
    # PDF storage
    pdf_report = models.FileField(upload_to='reports/', null=True, blank=True)
    
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True, null=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.report_type}) - {self.user.get_full_name()}"