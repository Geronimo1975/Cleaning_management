from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.conf import settings
from django.contrib import messages

from accounts.models import User, CleanerProfile


class TimeTrackingAccessMiddleware:
    """
    Middleware to check if a cleaner is complete with their profile
    before accessing time tracking features, with an exception for
    the Time Clock page which should be accessible to all cleaners.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        return response
        
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            return None
            
        # Get current URL name
        url_name = resolve(request.path_info).url_name
        app_name = resolve(request.path_info).app_name
        
        # Only apply to timetracking app
        if app_name != 'timetracking':
            return None
            
        # Let users access the time_clock view regardless of profile status
        if url_name == 'time_clock':
            return None
            
        # Check if user is a cleaner
        if request.user.role != User.Role.CLEANER:
            return None
            
        # Check if profile is complete
        if not request.user.is_profile_complete:
            messages.warning(
                request,
                'Please complete your profile before accessing all time tracking features.'
            )
            return redirect('timetracking:time_clock')
            
        return None