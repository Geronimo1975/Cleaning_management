from django import forms
from django.utils.translation import gettext_lazy as _
from .models import TimeEntry, Timesheet, WorkSchedule, WorkDay


class TimeEntryForm(forms.ModelForm):
    """Form for manual time entry creation and editing."""
    
    # Add date field separate from datetime for easier entry
    date = forms.DateField(
        label=_("Date"),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    # Time inputs separate from datetime for easier entry
    clock_in_time_input = forms.TimeField(
        label=_("Clock In Time"),
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )
    
    clock_out_time_input = forms.TimeField(
        label=_("Clock Out Time"),
        required=False,
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )
    
    # Location fields
    clock_in_location_address = forms.CharField(
        label=_("Clock In Location"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    clock_out_location_address = forms.CharField(
        label=_("Clock Out Location"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Hidden fields for location coordinates
    clock_in_location_lat = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    clock_in_location_lng = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    clock_out_location_lat = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    clock_out_location_lng = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    class Meta:
        model = TimeEntry
        fields = [
            'job_request', 'job_assignment', 
            'break_duration_minutes', 'notes', 'is_manual_entry'
        ]
        widgets = {
            'job_request': forms.Select(attrs={'class': 'form-select'}),
            'job_assignment': forms.Select(attrs={'class': 'form-select'}),
            'break_duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3'
            }),
            'is_manual_entry': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        self.cleaner = kwargs.pop('cleaner', None)
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values for form fields if we're editing an existing entry
        if self.instance and self.instance.pk:
            if self.instance.clock_in_time:
                self.fields['date'].initial = self.instance.clock_in_time.date()
                self.fields['clock_in_time_input'].initial = self.instance.clock_in_time.time()
            
            if self.instance.clock_out_time:
                self.fields['clock_out_time_input'].initial = self.instance.clock_out_time.time()
        
        # Set the instance's cleaner and company
        if self.cleaner:
            self.instance.cleaner = self.cleaner
        
        if self.company:
            self.instance.company = self.company
        
        # Set is_manual_entry to True by default
        self.initial['is_manual_entry'] = True
    
    def clean(self):
        """Validate the form data."""
        cleaned_data = super().clean()
        
        date = cleaned_data.get('date')
        clock_in_time_input = cleaned_data.get('clock_in_time_input')
        clock_out_time_input = cleaned_data.get('clock_out_time_input')
        
        if date and clock_in_time_input:
            # Combine date and time into a datetime
            import datetime
            from django.utils import timezone
            
            # Create naive datetime then make it timezone-aware
            naive_datetime = datetime.datetime.combine(date, clock_in_time_input)
            cleaned_data['clock_in_time'] = timezone.make_aware(naive_datetime)
            
            if clock_out_time_input:
                naive_datetime = datetime.datetime.combine(date, clock_out_time_input)
                cleaned_data['clock_out_time'] = timezone.make_aware(naive_datetime)
                
                # Validate that clock_out_time is after clock_in_time
                if cleaned_data['clock_out_time'] < cleaned_data['clock_in_time']:
                    # Handle overnight shifts by adding a day to clock_out_time
                    cleaned_data['clock_out_time'] = timezone.make_aware(
                        datetime.datetime.combine(date + datetime.timedelta(days=1), clock_out_time_input)
                    )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save the time entry."""
        instance = super().save(commit=False)
        
        # Set from cleaned data
        instance.clock_in_time = self.cleaned_data.get('clock_in_time')
        instance.clock_out_time = self.cleaned_data.get('clock_out_time')
        
        # If clock out time exists, mark as not active
        if instance.clock_out_time:
            instance.is_active = False
        
        # Set the location data if provided
        instance.clock_in_location_lat = self.cleaned_data.get('clock_in_location_lat')
        instance.clock_in_location_lng = self.cleaned_data.get('clock_in_location_lng')
        instance.clock_in_location_address = self.cleaned_data.get('clock_in_location_address')
        
        instance.clock_out_location_lat = self.cleaned_data.get('clock_out_location_lat')
        instance.clock_out_location_lng = self.cleaned_data.get('clock_out_location_lng')
        instance.clock_out_location_address = self.cleaned_data.get('clock_out_location_address')
        
        if commit:
            instance.save()
        
        return instance


class TimesheetForm(forms.ModelForm):
    """Form for creating and editing timesheets."""
    
    class Meta:
        model = Timesheet
        fields = [
            'start_date', 'end_date', 'timesheet_type', 'notes'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'timesheet_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.cleaner = kwargs.pop('cleaner', None)
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Set the instance's cleaner and company
        if self.cleaner:
            self.instance.cleaner = self.cleaner
        
        if self.company:
            self.instance.company = self.company


class WorkScheduleForm(forms.ModelForm):
    """Form for creating and editing work schedules."""
    
    class Meta:
        model = WorkSchedule
        fields = [
            'name', 'start_date', 'end_date', 'schedule_type', 'hours_per_week'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'schedule_type': forms.Select(attrs={'class': 'form-select'}),
            'hours_per_week': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.5'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.cleaner = kwargs.pop('cleaner', None)
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Set the instance's cleaner and company
        if self.cleaner:
            self.instance.cleaner = self.cleaner
        
        if self.company:
            self.instance.company = self.company


class WorkDayForm(forms.ModelForm):
    """Form for adding/editing workdays in a schedule."""
    
    class Meta:
        model = WorkDay
        fields = [
            'date', 'day_type', 'start_time', 'end_time', 'break_duration', 'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'day_type': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'break_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.schedule = kwargs.pop('schedule', None)
        super().__init__(*args, **kwargs)
        
        if self.schedule:
            self.instance.schedule = self.schedule