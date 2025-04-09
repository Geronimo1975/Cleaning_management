from django import forms
from .models import (
    PayPeriod, Payslip, Contract, TaxClass, 
    SocialSecurity, PayScale
)
from accounts.models import CleanerProfile


class PayPeriodForm(forms.ModelForm):
    """Form for creating and editing pay periods."""
    class Meta:
        model = PayPeriod
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError('End date must be after start date.')
        
        return cleaned_data


class PayslipForm(forms.ModelForm):
    """Form for editing payslips."""
    class Meta:
        model = Payslip
        fields = [
            'regular_hours', 'overtime_hours', 'weekend_hours', 
            'night_hours', 'holiday_hours', 'hourly_rate',
            'bonus', 'reimbursements', 'other_deductions', 'notes'
        ]
        widgets = {
            'regular_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'overtime_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'weekend_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'night_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'holiday_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bonus': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reimbursements': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_deductions': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ContractForm(forms.ModelForm):
    """Form for creating and editing employment contracts."""
    class Meta:
        model = Contract
        fields = [
            'cleaner', 'start_date', 'end_date', 'contract_type',
            'weekly_hours', 'pay_scale', 'base_salary', 'hourly_rate',
            'tax_class', 'health_insurance_type', 'has_children',
            'contract_document'
        ]
        widgets = {
            'cleaner': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'weekly_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'pay_scale': forms.Select(attrs={'class': 'form-select'}),
            'base_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_class': forms.Select(attrs={'class': 'form-select'}),
            'health_insurance_type': forms.Select(attrs={'class': 'form-select'}),
            'has_children': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'contract_document': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super(ContractForm, self).__init__(*args, **kwargs)
        
        # Filter cleaners to show only those related to this company
        if company:
            self.fields['cleaner'].queryset = CleanerProfile.objects.filter(company=company)
    
    def clean(self):
        cleaned_data = super().clean()
        contract_type = cleaned_data.get('contract_type')
        base_salary = cleaned_data.get('base_salary')
        hourly_rate = cleaned_data.get('hourly_rate')
        
        # Validate based on contract type
        if contract_type in ['full_time', 'part_time']:
            if not base_salary:
                self.add_error('base_salary', 'Base salary is required for full-time and part-time contracts.')
        elif contract_type in ['mini_job', 'freelance']:
            if not hourly_rate:
                self.add_error('hourly_rate', 'Hourly rate is required for mini-job and freelance contracts.')
        
        return cleaned_data


class TaxClassForm(forms.ModelForm):
    """Form for managing tax classes."""
    class Meta:
        model = TaxClass
        fields = ['class_number', 'description']
        widgets = {
            'class_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }


class SocialSecurityForm(forms.ModelForm):
    """Form for managing social security rates."""
    class Meta:
        model = SocialSecurity
        fields = [
            'year', 'health_insurance_rate', 'pension_insurance_rate',
            'unemployment_insurance_rate', 'care_insurance_rate',
            'additional_health_rate', 'additional_care_rate_no_children',
            'health_insurance_threshold', 'pension_insurance_threshold'
        ]
        widgets = {
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'health_insurance_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pension_insurance_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unemployment_insurance_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'care_insurance_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'additional_health_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'additional_care_rate_no_children': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'health_insurance_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pension_insurance_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class PayScaleForm(forms.ModelForm):
    """Form for managing pay scales."""
    class Meta:
        model = PayScale
        fields = [
            'name', 'description', 'base_hourly_rate',
            'experience_premium_1', 'experience_premium_3', 'experience_premium_5',
            'weekend_premium', 'night_premium', 'holiday_premium'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'base_hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'experience_premium_1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'experience_premium_3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'experience_premium_5': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'weekend_premium': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'night_premium': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'holiday_premium': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
