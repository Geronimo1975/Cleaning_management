from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, CustomerProfile, CompanyProfile, CleanerProfile


class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form using email instead of username."""
    username = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))


class UserRegistrationForm(UserCreationForm):
    """Form for user registration with role selection."""
    ROLE_CHOICES = [
        (User.Role.CUSTOMER, 'Customer - I need cleaning services'),
        (User.Role.COMPANY, 'Cleaning Company - I provide cleaning services'),
        (User.Role.CLEANER, 'Cleaner - I perform cleaning services'),
    ]
    
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'phone', 'role', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.phone = self.cleaned_data['phone']
        
        if commit:
            user.save()
        return user


class CustomerProfileForm(forms.ModelForm):
    """Form for customer profile information."""
    class Meta:
        model = CustomerProfile
        fields = ['address', 'city', 'postal_code', 'state', 'country']
        widgets = {
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CompanyProfileForm(forms.ModelForm):
    """Form for company profile information."""
    class Meta:
        model = CompanyProfile
        fields = ['company_name', 'business_registration_number', 'tax_id', 
                 'description', 'founded_year', 'website', 'address', 
                 'city', 'postal_code', 'state', 'country']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'business_registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'founded_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CleanerProfileForm(forms.ModelForm):
    """Form for cleaner profile information."""
    SPECIALIZATION_CHOICES = [
        ('residential', 'Residential Cleaning'),
        ('commercial', 'Commercial Cleaning'),
        ('deep', 'Deep Cleaning'),
        ('window', 'Window Cleaning'),
        ('carpet', 'Carpet Cleaning'),
        ('move_in_out', 'Move-in/Move-out Cleaning'),
    ]
    
    specializations = forms.MultipleChoiceField(
        choices=SPECIALIZATION_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
    
    class Meta:
        model = CleanerProfile
        fields = ['is_freelancer', 'tax_id', 'social_security_number', 
                 'experience_years', 'specializations', 'employment_type',
                 'address', 'city', 'postal_code', 'state', 'country']
        widgets = {
            'is_freelancer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'social_security_number': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_specializations(self):
        """Convert specializations to a list for JSONField storage."""
        return list(self.cleaned_data['specializations'])


class UserProfilePictureForm(forms.ModelForm):
    """Form for updating profile picture."""
    class Meta:
        model = User
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
