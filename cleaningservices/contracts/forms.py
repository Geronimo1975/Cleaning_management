from django import forms
from .models import Contract, ContractTemplate, ContractAddendum
from accounts.models import CleanerProfile, CompanyProfile

class ContractTemplateForm(forms.ModelForm):
    """Form for creating and editing contract templates."""
    class Meta:
        model = ContractTemplate
        fields = [
            'name', 'description', 'template_content', 'template_file',
            'default_terms'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'template_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'default_terms': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '{"hours": 40, "monthly_salary": 3000, ...}'}),
            'template_file': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.company:
            instance.company = self.company
        
        if commit:
            instance.save()
        return instance


class ContractForm(forms.ModelForm):
    """Form for creating and editing contracts."""
    class Meta:
        model = Contract
        fields = [
            'cleaner', 'template', 'contract_number', 'title', 'description',
            'start_date', 'end_date', 'contract_type', 'working_hours_weekly',
            'hourly_rate', 'monthly_salary', 'terms_and_conditions', 'contract_file'
        ]
        widgets = {
            'cleaner': forms.Select(attrs={'class': 'form-select'}),
            'template': forms.Select(attrs={'class': 'form-select'}),
            'contract_number': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'working_hours_weekly': forms.NumberInput(attrs={'class': 'form-control'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'monthly_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'terms_and_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'contract_file': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If company is provided, filter templates by company
        if self.company:
            self.fields['template'].queryset = ContractTemplate.objects.filter(company=self.company)
        
        # Filter cleaners to show company's employees or freelancers
        if self.company:
            self.fields['cleaner'].queryset = CleanerProfile.objects.filter(
                company=self.company
            ) | CleanerProfile.objects.filter(is_freelancer=True)
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.company:
            instance.company = self.company
        
        if self.user:
            instance.created_by = self.user
        
        if commit:
            instance.save()
        
        return instance


class ContractAddendumForm(forms.ModelForm):
    """Form for creating and editing contract addenda."""
    class Meta:
        model = ContractAddendum
        fields = [
            'title', 'description', 'effective_date', 'changes', 'document_file'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'changes': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'document_file': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.contract = kwargs.pop('contract', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.contract:
            instance.contract = self.contract
        
        if self.user:
            instance.created_by = self.user
        
        if commit:
            instance.save()
        
        return instance