from django import forms
from .models import JobRequest, JobBid, JobAssignment, TimeTracking, JobCompletion, ServiceCategory


class JobRequestForm(forms.ModelForm):
    """Form for customers to create job requests."""
    class Meta:
        model = JobRequest
        fields = [
            'service_category', 'title', 'description',
            'address', 'city', 'postal_code', 'state', 'country',
            'area_size', 'estimated_duration', 'job_type',
            'preferred_date', 'preferred_time',
            'recurring_frequency', 'contract_start_date', 'contract_end_date',
            'budget', 'special_requirements', 'supply_requirements'
        ]
        widgets = {
            'service_category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'area_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'estimated_duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'preferred_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'preferred_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'recurring_frequency': forms.Select(attrs={'class': 'form-select'}),
            'contract_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control'}),
            'special_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'supply_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super(JobRequestForm, self).__init__(*args, **kwargs)
        self.fields['recurring_frequency'].required = False
        self.fields['contract_start_date'].required = False
        self.fields['contract_end_date'].required = False
        self.fields['special_requirements'].required = False
        self.fields['supply_requirements'].required = False


class JobBidForm(forms.ModelForm):
    """Form for companies to submit bids for job requests."""
    class Meta:
        model = JobBid
        fields = ['price', 'estimated_hours', 'message', 'can_start_at']
        widgets = {
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'can_start_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class JobAssignmentForm(forms.ModelForm):
    """Form for companies to assign cleaners to jobs."""
    class Meta:
        model = JobAssignment
        fields = ['cleaner', 'scheduled_start', 'scheduled_end']
        widgets = {
            'cleaner': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'scheduled_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class TimeTrackingForm(forms.ModelForm):
    """Form for cleaners to track their time."""
    class Meta:
        model = TimeTracking
        fields = ['clock_in', 'clock_out', 'break_start', 'break_end', 'notes']
        widgets = {
            'clock_in': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'clock_out': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'break_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'break_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class JobCompletionForm(forms.ModelForm):
    """Form for recording job completion details."""
    class Meta:
        model = JobCompletion
        fields = ['completed_at', 'tasks_completed', 'issues_reported']
        widgets = {
            'completed_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'tasks_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'issues_reported': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class JobFeedbackForm(forms.ModelForm):
    """Form for customers to provide feedback on completed jobs."""
    class Meta:
        model = JobCompletion
        fields = ['customer_rating', 'customer_feedback']
        widgets = {
            'customer_rating': forms.Select(attrs={'class': 'form-select'}),
            'customer_feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
