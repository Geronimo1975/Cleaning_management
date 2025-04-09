from django import forms
from django.utils import timezone
from datetime import datetime, timedelta

from .models import AnalyticsReport, DashboardSavedView
from accounts.models import CompanyProfile, CleanerProfile


class ReportFilterForm(forms.Form):
    """Form for filtering analytics data."""
    PERIOD_CHOICES = [
        ('', 'Select Period'),
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('this_quarter', 'This Quarter'),
        ('last_quarter', 'Last Quarter'),
        ('this_year', 'This Year'),
        ('last_year', 'Last Year'),
        ('custom', 'Custom Range'),
    ]
    
    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    
    company = forms.ModelChoiceField(
        queryset=CompanyProfile.objects.all(),
        required=False,
        empty_label='All Companies',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    
    cleaner = forms.ModelChoiceField(
        queryset=CleanerProfile.objects.all(),
        required=False,
        empty_label='All Cleaners',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    
    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # If custom range is selected, both start and end date are required
        if period == 'custom':
            if not start_date:
                self.add_error('start_date', 'Start date is required for custom range')
            if not end_date:
                self.add_error('end_date', 'End date is required for custom range')
            
            # Ensure end date is not before start date
            if start_date and end_date and end_date < start_date:
                self.add_error('end_date', 'End date cannot be before start date')
        
        # If predefined period is selected, calculate the date range
        elif period and period != '':
            today = timezone.now().date()
            
            if period == 'today':
                start_date = today
                end_date = today
            elif period == 'yesterday':
                yesterday = today - timedelta(days=1)
                start_date = yesterday
                end_date = yesterday
            elif period == 'this_week':
                start_date = today - timedelta(days=today.weekday())
                end_date = today
            elif period == 'last_week':
                start_date = today - timedelta(days=today.weekday() + 7)
                end_date = start_date + timedelta(days=6)
            elif period == 'this_month':
                start_date = today.replace(day=1)
                end_date = today
            elif period == 'last_month':
                if today.month == 1:
                    last_month = today.replace(year=today.year-1, month=12, day=1)
                else:
                    last_month = today.replace(month=today.month-1, day=1)
                
                start_date = last_month
                # Last day of last month
                if today.month == 1:
                    end_date = today.replace(year=today.year-1, month=12, day=31)
                else:
                    next_month = today.replace(day=1)
                    end_date = next_month - timedelta(days=1)
            elif period == 'this_quarter':
                current_quarter = (today.month - 1) // 3 + 1
                start_date = datetime(today.year, 3 * current_quarter - 2, 1).date()
                if current_quarter == 4:
                    end_date = datetime(today.year, 12, 31).date()
                else:
                    end_date = datetime(today.year, 3 * current_quarter + 1, 1).date() - timedelta(days=1)
            elif period == 'last_quarter':
                current_quarter = (today.month - 1) // 3 + 1
                last_quarter = current_quarter - 1
                last_quarter_year = today.year
                
                if last_quarter == 0:
                    last_quarter = 4
                    last_quarter_year -= 1
                    
                start_date = datetime(last_quarter_year, 3 * last_quarter - 2, 1).date()
                if last_quarter == 4:
                    end_date = datetime(last_quarter_year, 12, 31).date()
                else:
                    end_date = datetime(last_quarter_year, 3 * last_quarter + 1, 1).date() - timedelta(days=1)
            elif period == 'this_year':
                start_date = today.replace(month=1, day=1)
                end_date = today
            elif period == 'last_year':
                start_date = datetime(today.year - 1, 1, 1).date()
                end_date = datetime(today.year - 1, 12, 31).date()
            
            cleaned_data['start_date'] = start_date
            cleaned_data['end_date'] = end_date
        
        return cleaned_data


class AnalyticsReportForm(forms.ModelForm):
    """Form for creating and editing analytics reports."""
    class Meta:
        model = AnalyticsReport
        fields = [
            'title', 'report_type', 'period', 'start_date', 'end_date', 
            'company', 'cleaner', 'parameters', 'is_scheduled', 'schedule_frequency'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
            'cleaner': forms.Select(attrs={'class': 'form-select'}),
            'parameters': forms.Textarea(attrs={'class': 'form-control json-editor', 'rows': 5}),
            'is_scheduled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'schedule_frequency': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make the parameters field optional and add helper text
        self.fields['parameters'].required = False
        self.fields['parameters'].help_text = 'Enter JSON parameters for the report (optional)'
        
        # Add frequency options for scheduled reports
        self.fields['schedule_frequency'].choices = [
            ('', 'Select Frequency'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
        ]
        
        # Filter company and cleaner choices based on user role
        if user:
            if user.role == user.Role.COMPANY:
                try:
                    company = CompanyProfile.objects.get(user=user)
                    self.fields['company'].initial = company
                    self.fields['company'].widget.attrs['disabled'] = True
                    self.fields['cleaner'].queryset = CleanerProfile.objects.filter(company=company)
                except CompanyProfile.DoesNotExist:
                    pass
            elif user.role == user.Role.CLEANER:
                try:
                    cleaner = CleanerProfile.objects.get(user=user)
                    self.fields['cleaner'].initial = cleaner
                    self.fields['cleaner'].widget.attrs['disabled'] = True
                    if cleaner.company:
                        self.fields['company'].initial = cleaner.company
                except CleanerProfile.DoesNotExist:
                    pass
    
    def clean_parameters(self):
        """Validate and clean the parameters JSON field."""
        parameters = self.cleaned_data.get('parameters')
        
        if not parameters:
            return {}
            
        # If it's already a dict, return it
        if isinstance(parameters, dict):
            return parameters
            
        # Otherwise, it's a string, so validate it's valid JSON
        try:
            import json
            return json.loads(parameters)
        except json.JSONDecodeError:
            raise forms.ValidationError('Parameters must be valid JSON')


class DashboardSavedViewForm(forms.ModelForm):
    """Form for saving dashboard configurations."""
    class Meta:
        model = DashboardSavedView
        fields = ['name', 'configuration', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'configuration': forms.Textarea(attrs={'class': 'form-control json-editor', 'rows': 5}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_configuration(self):
        """Validate and clean the configuration JSON field."""
        configuration = self.cleaned_data.get('configuration')
        
        # If it's already a dict, return it
        if isinstance(configuration, dict):
            return configuration
            
        # Otherwise, it's a string, so validate it's valid JSON
        try:
            import json
            return json.loads(configuration)
        except json.JSONDecodeError:
            raise forms.ValidationError('Configuration must be valid JSON')