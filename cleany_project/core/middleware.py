from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class RoleBasedAccessMiddleware:
    """
    Middleware to handle role-based access to views.
    Redirects users to appropriate dashboard based on their role.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        path = request.path_info
        user = request.user
        
        # Skip for non-authenticated users or admin paths
        if not user.is_authenticated or path.startswith('/admin/'):
            return self.get_response(request)
        
        # Redirect to role registration pages if profile doesn't exist
        if user.is_company() and not hasattr(user, 'company_profile') and not path.startswith('/register/company/'):
            if path != reverse('company_registration') and not path.startswith('/logout/'):
                messages.warning(request, "Please complete your company profile first.")
                return redirect('company_registration')
        
        elif user.is_cleaner() and not hasattr(user, 'cleaner_profile') and not path.startswith('/register/cleaner/'):
            if path != reverse('cleaner_registration') and not path.startswith('/logout/'):
                messages.warning(request, "Please complete your cleaner profile first.")
                return redirect('cleaner_registration')
        
        # Handle role-specific access to dashboards
        if path == reverse('customer_dashboard') and not user.is_customer():
            return redirect('dashboard')
        
        elif path == reverse('company_dashboard') and not user.is_company():
            return redirect('dashboard')
        
        elif path == reverse('cleaner_dashboard') and not user.is_cleaner():
            return redirect('dashboard')
        
        # Continue with the request
        response = self.get_response(request)
        return response
