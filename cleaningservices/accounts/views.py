from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib import messages
from .forms import (
    UserRegistrationForm, CustomAuthenticationForm, 
    CustomerProfileForm, CompanyProfileForm, CleanerProfileForm,
    UserProfilePictureForm
)
from .models import User, CustomerProfile, CompanyProfile, CleanerProfile


class CustomLoginView(LoginView):
    """Custom login view using the email-based authentication form."""
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        """Redirect to appropriate dashboard based on user's role."""
        user = self.request.user
        if user.role == User.Role.CUSTOMER:
            return reverse_lazy('customer_dashboard')
        elif user.role == User.Role.COMPANY:
            return reverse_lazy('company_dashboard')
        elif user.role == User.Role.CLEANER:
            return reverse_lazy('cleaner_dashboard')
        else:
            return reverse_lazy('home')


class UserRegistrationView(CreateView):
    """View for user registration with role selection."""
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    
    def form_valid(self, form):
        # Save the user instance
        user = form.save()
        
        # Create the appropriate profile based on the selected role
        if user.role == User.Role.CUSTOMER:
            CustomerProfile.objects.create(user=user)
        elif user.role == User.Role.COMPANY:
            CompanyProfile.objects.create(user=user)
        elif user.role == User.Role.CLEANER:
            CleanerProfile.objects.create(user=user)
        
        # Log the user in
        login(self.request, user)
        messages.success(self.request, 'Registration successful! Please complete your profile.')
        
        # Redirect to the appropriate profile completion page
        return redirect('complete_profile')
    
    def form_invalid(self, form):
        messages.error(self.request, 'Registration failed. Please correct the errors below.')
        return super().form_invalid(form)


@login_required
def complete_profile_view(request):
    """View for completing user profile based on role."""
    user = request.user
    
    # Determine which profile form to use based on user role
    if user.role == User.Role.CUSTOMER:
        profile_instance = CustomerProfile.objects.get(user=user)
        form_class = CustomerProfileForm
    elif user.role == User.Role.COMPANY:
        profile_instance = CompanyProfile.objects.get(user=user)
        form_class = CompanyProfileForm
    elif user.role == User.Role.CLEANER:
        profile_instance = CleanerProfile.objects.get(user=user)
        form_class = CleanerProfileForm
    else:
        messages.error(request, 'Invalid user role.')
        return redirect('home')
    
    if request.method == 'POST':
        form = form_class(request.POST, instance=profile_instance)
        if form.is_valid():
            form.save()
            
            # Mark profile as complete
            user.is_profile_complete = True
            user.save()
            
            messages.success(request, 'Profile completed successfully!')
            
            # Redirect to appropriate dashboard
            if user.role == User.Role.CUSTOMER:
                return redirect('customer_dashboard')
            elif user.role == User.Role.COMPANY:
                return redirect('company_dashboard')
            elif user.role == User.Role.CLEANER:
                return redirect('cleaner_dashboard')
    else:
        form = form_class(instance=profile_instance)
    
    return render(request, 'accounts/profile.html', {
        'form': form,
        'user_role': user.get_role_display(),
    })


@login_required
def profile_view(request):
    """View for viewing and updating user profile."""
    user = request.user
    
    # Get the appropriate profile based on user role
    if user.role == User.Role.CUSTOMER:
        profile_instance = CustomerProfile.objects.get(user=user)
        profile_form_class = CustomerProfileForm
    elif user.role == User.Role.COMPANY:
        profile_instance = CompanyProfile.objects.get(user=user)
        profile_form_class = CompanyProfileForm
    elif user.role == User.Role.CLEANER:
        profile_instance = CleanerProfile.objects.get(user=user)
        profile_form_class = CleanerProfileForm
    else:
        messages.error(request, 'Invalid user role.')
        return redirect('home')
    
    # Handle profile form submission
    if request.method == 'POST' and 'update_profile' in request.POST:
        profile_form = profile_form_class(request.POST, instance=profile_instance)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        profile_form = profile_form_class(instance=profile_instance)
    
    # Handle profile picture form submission
    picture_form = UserProfilePictureForm(instance=user)
    if request.method == 'POST' and 'update_picture' in request.POST:
        picture_form = UserProfilePictureForm(request.POST, request.FILES, instance=user)
        if picture_form.is_valid():
            picture_form.save()
            messages.success(request, 'Profile picture updated successfully!')
            return redirect('profile')
    
    return render(request, 'accounts/profile.html', {
        'profile_form': profile_form,
        'picture_form': picture_form,
        'user': user,
    })


@login_required
def logout_view(request):
    """View for logging out users."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')
