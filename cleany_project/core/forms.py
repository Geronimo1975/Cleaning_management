from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import (
    User, Company, Cleaner, Customer, ServiceType, Job, JobApplication,
    Document, Timesheet, Payroll, Rating
)


class CustomUserCreationForm(UserCreationForm):
    """Form for user registration."""
    role = forms.ChoiceField(choices=User.Role.choices)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2', 'phone_number', 'address')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user


class CompanyForm(forms.ModelForm):
    """Form for company details."""
    class Meta:
        model = Company
        fields = ('name', 'description', 'registration_number', 'tax_id', 'founding_date', 'logo', 'website')
        widgets = {
            'founding_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class CleanerForm(forms.ModelForm):
    """Form for cleaner details."""
    class Meta:
        model = Cleaner
        fields = ('bio', 'experience_years', 'hourly_rate', 'is_available', 'specializations', 'tax_id', 'social_security_number')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'specializations': forms.CheckboxSelectMultiple(),
        }


class CustomerForm(forms.ModelForm):
    """Form for customer details."""
    class Meta:
        model = Customer
        fields = ('payment_info',)
        widgets = {
            'payment_info': forms.Textarea(attrs={'rows': 3}),
        }


class ServiceTypeForm(forms.ModelForm):
    """Form for service types."""
    class Meta:
        model = ServiceType
        fields = ('name', 'description', 'base_price')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class JobForm(forms.ModelForm):
    """Form for job creation and editing."""
    class Meta:
        model = Job
        fields = ('title', 'service_type', 'job_type', 'description', 'location', 'start_datetime', 'price', 'recurring_frequency')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def clean_start_datetime(self):
        start_datetime = self.cleaned_data.get('start_datetime')
        if start_datetime and start_datetime < timezone.now():
            raise ValidationError("Start time cannot be in the past.")
        return start_datetime
    
    def clean_recurring_frequency(self):
        recurring_frequency = self.cleaned_data.get('recurring_frequency')
        job_type = self.cleaned_data.get('job_type')
        
        if job_type == Job.JobType.PART_TIME and recurring_frequency > 0:
            raise ValidationError("One-time services cannot be recurring.")
        
        return recurring_frequency


class JobApplicationForm(forms.ModelForm):
    """Form for job applications."""
    class Meta:
        model = JobApplication
        fields = ('cover_letter', 'price_offer')
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 4}),
        }
    
    def clean_price_offer(self):
        price_offer = self.cleaned_data.get('price_offer')
        if price_offer <= 0:
            raise ValidationError("Price offer must be greater than zero.")
        return price_offer


class DocumentUploadForm(forms.ModelForm):
    """Form for document uploads."""
    class Meta:
        model = Document
        fields = ('title', 'description', 'file', 'document_type', 'is_public')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class TimesheetForm(forms.ModelForm):
    """Form for timesheet entry."""
    class Meta:
        model = Timesheet
        fields = ('date', 'start_time', 'end_time', 'break_duration', 'notes')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            import datetime
            start = datetime.datetime.combine(datetime.date.today(), start_time)
            end = datetime.datetime.combine(datetime.date.today(), end_time)
            
            # If end time is earlier than start time, assume it's the next day
            if end < start:
                # No validation needed for overnight shifts
                pass
            elif (end - start).total_seconds() / 3600 > 16:
                raise ValidationError("Working time cannot exceed 16 hours.")
        
        return cleaned_data


class PayrollForm(forms.ModelForm):
    """Form for payroll processing."""
    class Meta:
        model = Payroll
        fields = ('cleaner', 'period_start', 'period_end', 'base_salary', 'bonus', 
                  'tax_deduction', 'social_security_deduction', 'payment_date', 'payment_method', 'notes')
        widgets = {
            'period_start': forms.DateInput(attrs={'type': 'date'}),
            'period_end': forms.DateInput(attrs={'type': 'date'}),
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        period_start = cleaned_data.get('period_start')
        period_end = cleaned_data.get('period_end')
        
        if period_start and period_end and period_start > period_end:
            raise ValidationError("End date must be after start date.")
        
        # Calculate net amount
        base_salary = cleaned_data.get('base_salary') or 0
        bonus = cleaned_data.get('bonus') or 0
        tax_deduction = cleaned_data.get('tax_deduction') or 0
        social_security_deduction = cleaned_data.get('social_security_deduction') or 0
        
        net_amount = base_salary + bonus - tax_deduction - social_security_deduction
        if net_amount < 0:
            raise ValidationError("Net amount cannot be negative.")
        
        cleaned_data['net_amount'] = net_amount
        return cleaned_data


class RatingForm(forms.ModelForm):
    """Form for ratings and reviews."""
    class Meta:
        model = Rating
        fields = ('score', 'comment')
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
            'score': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
        }


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information."""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'address', 'profile_picture')


class JobStatusUpdateForm(forms.ModelForm):
    """Form for updating job status."""
    class Meta:
        model = Job
        fields = ('status',)


class JobCompletionForm(forms.Form):
    """Form for job completion with actual start and end times."""
    actual_start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=True
    )
    actual_end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=True
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('actual_start_time')
        end_time = cleaned_data.get('actual_end_time')
        
        if start_time and end_time and start_time > end_time:
            raise ValidationError("End time must be after start time.")
        
        return cleaned_data


class JobAssignmentForm(forms.Form):
    """Form for assigning a job to a company and/or cleaner."""
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        required=False,
        empty_label="Select a company"
    )
    
    cleaner = forms.ModelChoiceField(
        queryset=Cleaner.objects.all(),
        required=False,
        empty_label="Select a cleaner"
    )
    
    def __init__(self, *args, **kwargs):
        company_qs = kwargs.pop('company_queryset', None)
        cleaner_qs = kwargs.pop('cleaner_queryset', None)
        super().__init__(*args, **kwargs)
        
        if company_qs is not None:
            self.fields['company'].queryset = company_qs
        
        if cleaner_qs is not None:
            self.fields['cleaner'].queryset = cleaner_qs
