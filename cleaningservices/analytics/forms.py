from django import forms
from django.utils.translation import gettext_lazy as _
import json

from .models import DashboardSavedView, AnalyticsReport
from accounts.models import CompanyProfile, CleanerProfile


class DashboardCustomizationForm(forms.Form):
    """Form for customizing dashboard layout and widgets."""
    configuration = forms.JSONField(
        widget=forms.HiddenInput(), 
        required=False,
        initial={}
    )
    
    def clean_configuration(self):
        """Validate configuration JSON structure."""
        configuration = self.cleaned_data.get('configuration')
        
        if not configuration:
            # Default configuration
            return {
                'layout': 'grid',
                'widgets': [
                    {'type': 'time_summary', 'position': 1, 'size': 'medium'},
                    {'type': 'contract_status', 'position': 2, 'size': 'medium'},
                    {'type': 'cleaner_performance', 'position': 3, 'size': 'large'},
                    {'type': 'revenue_chart', 'position': 4, 'size': 'large'},
                ]
            }
        
        if isinstance(configuration, str):
            try:
                configuration = json.loads(configuration)
            except json.JSONDecodeError:
                raise forms.ValidationError(_("Invalid JSON format in configuration"))
        
        # Validate required fields
        if 'layout' not in configuration:
            configuration['layout'] = 'grid'
        
        if 'widgets' not in configuration or not isinstance(configuration['widgets'], list):
            raise forms.ValidationError(_("Configuration must contain a 'widgets' list"))
        
        # Validate widget entries
        valid_widget_types = ['time_summary', 'contract_status', 'cleaner_performance', 
                             'revenue_chart', 'customer_satisfaction', 'job_statistics']
        
        valid_sizes = ['small', 'medium', 'large', 'full']
        
        for widget in configuration['widgets']:
            if 'type' not in widget:
                raise forms.ValidationError(_("Each widget must have a 'type'"))
            
            if widget['type'] not in valid_widget_types:
                raise forms.ValidationError(_(f"Invalid widget type: {widget['type']}"))
            
            if 'size' in widget and widget['size'] not in valid_sizes:
                raise forms.ValidationError(_(f"Invalid widget size: {widget['size']}"))
            
            if 'position' not in widget:
                widget['position'] = len(configuration['widgets'])
        
        return configuration


class ReportForm(forms.ModelForm):
    """Form for creating and editing analytics reports."""
    class Meta:
        model = AnalyticsReport
        fields = [
            'title', 'report_type', 'period', 'start_date', 'end_date',
            'company', 'cleaner', 'is_scheduled', 'schedule_frequency'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'period': forms.Select(attrs={'class': 'form-select', 'id': 'period-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
            'cleaner': forms.Select(attrs={'class': 'form-select'}),
            'is_scheduled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'schedule-check'}),
            'schedule_frequency': forms.Select(attrs={'class': 'form-select', 'id': 'schedule-frequency'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter company and cleaner choices
        self.fields['company'].queryset = CompanyProfile.objects.all().order_by('company_name')
        self.fields['cleaner'].queryset = CleanerProfile.objects.all().order_by('user__first_name')
        
        # Make some fields optional
        self.fields['schedule_frequency'].required = False
        
        # Set field dependencies
        self.fields['company'].help_text = _("Filter report data by company")
        self.fields['cleaner'].help_text = _("Filter report data by cleaner")
    
    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        period = cleaned_data.get('period')
        is_scheduled = cleaned_data.get('is_scheduled')
        schedule_frequency = cleaned_data.get('schedule_frequency')
        
        # Validate date range
        if start_date and end_date and start_date > end_date:
            self.add_error('start_date', _("Start date cannot be after end date"))
        
        # Validate scheduling options
        if is_scheduled and not schedule_frequency:
            self.add_error('schedule_frequency', _("Schedule frequency is required when scheduling is enabled"))
        
        return cleaned_data