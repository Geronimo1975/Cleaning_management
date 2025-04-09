from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum, F, ExpressionWrapper, DurationField, Q
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from .models import WorkDay, TimeEntry, WorkSchedule, Timesheet, TimesheetEntry, TimeEntryApproval
from accounts.models import User, CleanerProfile, CompanyProfile
from .forms import TimeEntryForm, TimesheetForm, WorkScheduleForm, WorkDayForm
import json
import datetime
import math
from decimal import Decimal


def get_cleaner_profile(user):
    """Helper function to get cleaner profile if user is cleaner."""
    if hasattr(user, 'cleaner_profile'):
        return user.cleaner_profile
    return None


def get_company_profile(user):
    """Helper function to get company profile if user is company."""
    if hasattr(user, 'company_profile'):
        return user.company_profile
    return None


# Time entry management views
@login_required
def time_entry_list_view(request):
    """View for listing all time entries a user has access to."""
    # Get user role-specific data
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Get entries based on user role
    entries = []
    if cleaner_profile:
        # Cleaners see their own entries
        entries = TimeEntry.objects.filter(cleaner=cleaner_profile)
    elif company_profile:
        # Companies see entries for their cleaners
        entries = TimeEntry.objects.filter(company=company_profile)
    elif request.user.role == User.Role.ADMIN:
        # Admins see all entries
        entries = TimeEntry.objects.all()
    
    # Get current active entry if any
    active_entry = None
    if cleaner_profile:
        try:
            active_entry = TimeEntry.objects.get(cleaner=cleaner_profile, is_active=True)
        except (TimeEntry.DoesNotExist, TimeEntry.MultipleObjectsReturned):
            # Handle case of no active entry or multiple active entries (should not happen)
            pass
    
    # Calculate time summary stats
    today = timezone.now().date()
    week_start = today - datetime.timedelta(days=today.weekday())
    month_start = datetime.date(today.year, today.month, 1)
    
    today_entries = entries.filter(clock_in_time__date=today)
    week_entries = entries.filter(clock_in_time__date__gte=week_start, clock_in_time__date__lte=today)
    month_entries = entries.filter(clock_in_time__date__gte=month_start, clock_in_time__date__lte=today)
    
    # Calculate hours
    today_hours = sum([entry.total_duration_hours() for entry in today_entries if entry.clock_out_time])
    week_hours = sum([entry.total_duration_hours() for entry in week_entries if entry.clock_out_time])
    month_hours = sum([entry.total_duration_hours() for entry in month_entries if entry.clock_out_time])
    
    # Pagination
    paginator = Paginator(entries.order_by('-clock_in_time'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Time Entries',
        'section': 'timetracking',
        'page_obj': page_obj,
        'entries': page_obj.object_list,
        'active_entry': active_entry,
        'today_hours': today_hours,
        'week_hours': week_hours,
        'month_hours': month_hours,
        'is_cleaner': cleaner_profile is not None,
        'is_company': company_profile is not None,
        'is_admin': request.user.role == User.Role.ADMIN,
    }
    
    return render(request, 'timetracking/time_entry_list.html', context)


@login_required
def create_time_entry_view(request):
    """View for manually creating a new time entry."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Determine if user can create entries
    can_create = (cleaner_profile is not None or 
                  company_profile is not None or 
                  request.user.role == User.Role.ADMIN)
    
    if not can_create:
        messages.error(request, 'You do not have permission to create time entries.')
        return redirect('timetracking:list')
    
    # For company users or admins, we need to select a cleaner
    selected_cleaner = None
    if company_profile or request.user.role == User.Role.ADMIN:
        cleaner_id = request.GET.get('cleaner_id')
        if cleaner_id:
            selected_cleaner = get_object_or_404(CleanerProfile, id=cleaner_id)
        
        # If no cleaner selected, redirect to cleaner selection
        if not selected_cleaner:
            return redirect('timetracking:select_cleaner')
    else:
        # For cleaner users, use their own profile
        selected_cleaner = cleaner_profile
    
    if request.method == 'POST':
        form = TimeEntryForm(
            request.POST, 
            cleaner=selected_cleaner,
            company=company_profile
        )
        
        if form.is_valid():
            entry = form.save()
            messages.success(request, 'Time entry created successfully.')
            return redirect('timetracking:entry_detail', entry_id=entry.id)
    else:
        form = TimeEntryForm(
            cleaner=selected_cleaner,
            company=company_profile
        )
    
    context = {
        'title': 'Create Time Entry',
        'section': 'timetracking',
        'form': form,
        'selected_cleaner': selected_cleaner,
        'company_profile': company_profile,
    }
    
    return render(request, 'timetracking/time_entry_form.html', context)


@login_required
def select_cleaner_view(request):
    """View for company users to select a cleaner for time entry creation."""
    company_profile = get_company_profile(request.user)
    
    if not company_profile and request.user.role != User.Role.ADMIN:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('timetracking:list')
    
    # Get cleaners based on user role
    if company_profile:
        cleaners = CleanerProfile.objects.filter(company=company_profile)
    else:
        cleaners = CleanerProfile.objects.all()
    
    context = {
        'title': 'Select Cleaner',
        'section': 'timetracking',
        'cleaners': cleaners,
    }
    
    return render(request, 'timetracking/select_cleaner.html', context)


@login_required
def time_entry_detail_view(request, entry_id):
    """View for viewing details of a time entry."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Get the entry with appropriate permissions check
    if cleaner_profile:
        entry = get_object_or_404(TimeEntry, id=entry_id, cleaner=cleaner_profile)
    elif company_profile:
        entry = get_object_or_404(TimeEntry, id=entry_id, company=company_profile)
    elif request.user.role == User.Role.ADMIN:
        entry = get_object_or_404(TimeEntry, id=entry_id)
    else:
        messages.error(request, 'You do not have permission to view this time entry.')
        return redirect('timetracking:list')
    
    context = {
        'title': 'Time Entry Details',
        'section': 'timetracking',
        'entry': entry,
        'can_edit': True,  # We can add more fine-grained permissions later
        'can_delete': True,
        'can_verify': company_profile is not None or request.user.role == User.Role.ADMIN,
    }
    
    return render(request, 'timetracking/time_entry_detail.html', context)


@login_required
def edit_time_entry_view(request, entry_id):
    """View for editing a time entry."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Get the entry with appropriate permissions check
    if cleaner_profile:
        entry = get_object_or_404(TimeEntry, id=entry_id, cleaner=cleaner_profile)
    elif company_profile:
        entry = get_object_or_404(TimeEntry, id=entry_id, company=company_profile)
    elif request.user.role == User.Role.ADMIN:
        entry = get_object_or_404(TimeEntry, id=entry_id)
    else:
        messages.error(request, 'You do not have permission to edit this time entry.')
        return redirect('timetracking:list')
    
    if request.method == 'POST':
        form = TimeEntryForm(
            request.POST, 
            instance=entry,
            cleaner=entry.cleaner,
            company=entry.company
        )
        
        if form.is_valid():
            entry = form.save()
            messages.success(request, 'Time entry updated successfully.')
            return redirect('timetracking:entry_detail', entry_id=entry.id)
    else:
        form = TimeEntryForm(
            instance=entry,
            cleaner=entry.cleaner,
            company=entry.company
        )
    
    context = {
        'title': 'Edit Time Entry',
        'section': 'timetracking',
        'form': form,
        'entry': entry,
    }
    
    return render(request, 'timetracking/time_entry_form.html', context)


@login_required
def delete_time_entry_view(request, entry_id):
    """View for deleting a time entry."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Get the entry with appropriate permissions check
    if cleaner_profile:
        entry = get_object_or_404(TimeEntry, id=entry_id, cleaner=cleaner_profile)
    elif company_profile:
        entry = get_object_or_404(TimeEntry, id=entry_id, company=company_profile)
    elif request.user.role == User.Role.ADMIN:
        entry = get_object_or_404(TimeEntry, id=entry_id)
    else:
        messages.error(request, 'You do not have permission to delete this time entry.')
        return redirect('timetracking:list')
    
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Time entry deleted successfully.')
        return redirect('timetracking:entry_list')
    
    context = {
        'title': 'Delete Time Entry',
        'section': 'timetracking',
        'entry': entry,
    }
    
    return render(request, 'timetracking/time_entry_confirm_delete.html', context)


@login_required
def verify_time_entry_view(request, entry_id):
    """View for verifying a time entry."""
    company_profile = get_company_profile(request.user)
    
    # Only company users or admins can verify entries
    if not company_profile and request.user.role != User.Role.ADMIN:
        messages.error(request, 'You do not have permission to verify time entries.')
        return redirect('timetracking:list')
    
    # Get the entry
    if company_profile:
        entry = get_object_or_404(TimeEntry, id=entry_id, company=company_profile)
    else:
        entry = get_object_or_404(TimeEntry, id=entry_id)
    
    if request.method == 'POST':
        entry.is_verified = True
        entry.verified_by = request.user
        entry.verification_date = timezone.now()
        entry.save()
        
        messages.success(request, 'Time entry verified successfully.')
        return redirect('timetracking:entry_detail', entry_id=entry.id)
    
    context = {
        'title': 'Verify Time Entry',
        'section': 'timetracking',
        'entry': entry,
    }
    
    return render(request, 'timetracking/time_entry_verify.html', context)


# Time clock operations
@login_required
def clock_in_view(request):
    """View for clocking in."""
    cleaner_profile = get_cleaner_profile(request.user)
    
    if not cleaner_profile:
        messages.error(request, 'Only cleaners can clock in.')
        return redirect('timetracking:list')
    
    # Check if already clocked in
    active_entry = TimeEntry.objects.filter(cleaner=cleaner_profile, is_active=True).first()
    if active_entry:
        messages.warning(request, 'You are already clocked in.')
        return redirect('timetracking:list')
    
    # Process the clock in
    if request.method == 'POST':
        # Get location data if available
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        address = request.POST.get('address')
        
        # Create new time entry
        entry = TimeEntry(
            cleaner=cleaner_profile,
            company=cleaner_profile.company,
            clock_in_time=timezone.now(),
            is_active=True,
            clock_in_location_lat=latitude if latitude else None,
            clock_in_location_lng=longitude if longitude else None,
            clock_in_location_address=address
        )
        entry.save()
        
        messages.success(request, 'Successfully clocked in.')
        return redirect('timetracking:list')
    
    context = {
        'title': 'Clock In',
        'section': 'timetracking',
    }
    
    return render(request, 'timetracking/clock_in.html', context)


@login_required
def clock_out_view(request):
    """View for clocking out."""
    cleaner_profile = get_cleaner_profile(request.user)
    
    if not cleaner_profile:
        messages.error(request, 'Only cleaners can clock out.')
        return redirect('timetracking:list')
    
    # Get active time entry
    try:
        active_entry = TimeEntry.objects.get(cleaner=cleaner_profile, is_active=True)
    except TimeEntry.DoesNotExist:
        messages.warning(request, 'You are not currently clocked in.')
        return redirect('timetracking:list')
    except TimeEntry.MultipleObjectsReturned:
        # Handle rare case of multiple active entries
        active_entries = TimeEntry.objects.filter(cleaner=cleaner_profile, is_active=True)
        for entry in active_entries[1:]:
            entry.is_active = False
            entry.save()
        active_entry = active_entries.first()
    
    # Process the clock out
    if request.method == 'POST':
        # Get location data if available
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        address = request.POST.get('address')
        
        # Update the time entry
        active_entry.clock_out(
            latitude=latitude if latitude else None,
            longitude=longitude if longitude else None,
            address=address
        )
        
        messages.success(request, 'Successfully clocked out.')
        return redirect('timetracking:list')
    
    context = {
        'title': 'Clock Out',
        'section': 'timetracking',
        'active_entry': active_entry,
    }
    
    return render(request, 'timetracking/clock_out.html', context)


@login_required
def break_start_view(request):
    """View for starting a break."""
    cleaner_profile = get_cleaner_profile(request.user)
    
    if not cleaner_profile:
        messages.error(request, 'Only cleaners can start breaks.')
        return redirect('timetracking:list')
    
    # Get active time entry
    try:
        active_entry = TimeEntry.objects.get(cleaner=cleaner_profile, is_active=True)
    except TimeEntry.DoesNotExist:
        messages.warning(request, 'You are not currently clocked in.')
        return redirect('timetracking:list')
    
    # Check if already on break
    if active_entry.is_on_break():
        messages.warning(request, 'You are already on a break.')
        return redirect('timetracking:list')
    
    # Start the break
    active_entry.start_break()
    
    messages.success(request, 'Break started.')
    return redirect('timetracking:list')


@login_required
def break_end_view(request):
    """View for ending a break."""
    cleaner_profile = get_cleaner_profile(request.user)
    
    if not cleaner_profile:
        messages.error(request, 'Only cleaners can end breaks.')
        return redirect('timetracking:list')
    
    # Get active time entry
    try:
        active_entry = TimeEntry.objects.get(cleaner=cleaner_profile, is_active=True)
    except TimeEntry.DoesNotExist:
        messages.warning(request, 'You are not currently clocked in.')
        return redirect('timetracking:list')
    
    # Check if on break
    if not active_entry.is_on_break():
        messages.warning(request, 'You are not currently on a break.')
        return redirect('timetracking:list')
    
    # End the break
    active_entry.end_break()
    
    messages.success(request, 'Break ended.')
    return redirect('timetracking:list')


# Timesheet management
@login_required
def timesheet_list_view(request):
    """View for listing timesheets."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Get timesheets based on user role
    if cleaner_profile:
        timesheets = Timesheet.objects.filter(cleaner=cleaner_profile)
    elif company_profile:
        timesheets = Timesheet.objects.filter(company=company_profile)
    elif request.user.role == User.Role.ADMIN:
        timesheets = Timesheet.objects.all()
    else:
        timesheets = Timesheet.objects.none()
    
    # Pagination
    paginator = Paginator(timesheets.order_by('-start_date'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Timesheets',
        'section': 'timetracking',
        'page_obj': page_obj,
        'timesheets': page_obj.object_list,
        'is_cleaner': cleaner_profile is not None,
        'is_company': company_profile is not None,
        'is_admin': request.user.role == User.Role.ADMIN,
    }
    
    return render(request, 'timetracking/timesheet_list.html', context)


@login_required
def create_timesheet_view(request):
    """View for creating a new timesheet."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Determine if user can create timesheets
    can_create = (cleaner_profile is not None or 
                  company_profile is not None or 
                  request.user.role == User.Role.ADMIN)
    
    if not can_create:
        messages.error(request, 'You do not have permission to create timesheets.')
        return redirect('timetracking:timesheet_list')
    
    # For company users or admins, we need to select a cleaner
    selected_cleaner = None
    if company_profile or request.user.role == User.Role.ADMIN:
        cleaner_id = request.GET.get('cleaner_id')
        if cleaner_id:
            selected_cleaner = get_object_or_404(CleanerProfile, id=cleaner_id)
        
        # If no cleaner selected, redirect to cleaner selection
        if not selected_cleaner:
            return redirect('timetracking:select_cleaner_timesheet')
    else:
        # For cleaner users, use their own profile
        selected_cleaner = cleaner_profile
    
    if request.method == 'POST':
        form = TimesheetForm(
            request.POST,
            cleaner=selected_cleaner,
            company=company_profile
        )
        
        if form.is_valid():
            timesheet = form.save()
            
            # Now populate with time entries from the period
            entries = TimeEntry.objects.filter(
                cleaner=selected_cleaner,
                clock_in_time__date__gte=timesheet.start_date,
                clock_in_time__date__lte=timesheet.end_date,
                is_verified=True
            )
            
            for entry in entries:
                TimesheetEntry.objects.create(
                    timesheet=timesheet,
                    time_entry=entry
                )
            
            # Update the hour totals
            timesheet.update_hours()
            
            messages.success(request, 'Timesheet created successfully.')
            return redirect('timetracking:timesheet_detail', timesheet_id=timesheet.id)
    else:
        # Set default start and end dates based on timesheet type
        today = timezone.now().date()
        start_date = today - datetime.timedelta(days=today.weekday())  # Start of week
        end_date = start_date + datetime.timedelta(days=6)  # End of week
        
        form = TimesheetForm(
            initial={
                'start_date': start_date,
                'end_date': end_date,
                'timesheet_type': 'weekly'
            },
            cleaner=selected_cleaner,
            company=company_profile
        )
    
    context = {
        'title': 'Create Timesheet',
        'section': 'timetracking',
        'form': form,
        'selected_cleaner': selected_cleaner,
    }
    
    return render(request, 'timetracking/timesheet_form.html', context)


@login_required
def select_cleaner_timesheet_view(request):
    """View for company users to select a cleaner for timesheet creation."""
    company_profile = get_company_profile(request.user)
    
    if not company_profile and request.user.role != User.Role.ADMIN:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('timetracking:timesheet_list')
    
    # Get cleaners based on user role
    if company_profile:
        cleaners = CleanerProfile.objects.filter(company=company_profile)
    else:
        cleaners = CleanerProfile.objects.all()
    
    context = {
        'title': 'Select Cleaner for Timesheet',
        'section': 'timetracking',
        'cleaners': cleaners,
        'for_timesheet': True,
    }
    
    return render(request, 'timetracking/select_cleaner.html', context)


@login_required
def timesheet_detail_view(request, timesheet_id):
    """View for viewing details of a timesheet."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Get the timesheet with appropriate permissions check
    if cleaner_profile:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id, cleaner=cleaner_profile)
    elif company_profile:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id, company=company_profile)
    elif request.user.role == User.Role.ADMIN:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id)
    else:
        messages.error(request, 'You do not have permission to view this timesheet.')
        return redirect('timetracking:timesheet_list')
    
    # Get all time entries for this timesheet
    timesheet_entries = timesheet.entries.all().select_related('time_entry')
    time_entries = [te.time_entry for te in timesheet_entries]
    
    context = {
        'title': 'Timesheet Details',
        'section': 'timetracking',
        'timesheet': timesheet,
        'time_entries': time_entries,
        'can_edit': timesheet.status == 'draft',
        'can_delete': timesheet.status == 'draft',
        'can_submit': timesheet.status == 'draft' and cleaner_profile is not None,
        'can_approve': timesheet.status == 'submitted' and (company_profile is not None or request.user.role == User.Role.ADMIN),
        'can_reject': timesheet.status == 'submitted' and (company_profile is not None or request.user.role == User.Role.ADMIN),
    }
    
    return render(request, 'timetracking/timesheet_detail.html', context)


@login_required
def edit_timesheet_view(request, timesheet_id):
    """View for editing a timesheet."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Get the timesheet with appropriate permissions check
    if cleaner_profile:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id, cleaner=cleaner_profile)
    elif company_profile:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id, company=company_profile)
    elif request.user.role == User.Role.ADMIN:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id)
    else:
        messages.error(request, 'You do not have permission to edit this timesheet.')
        return redirect('timetracking:timesheet_list')
    
    # Can only edit draft timesheets
    if timesheet.status != 'draft':
        messages.error(request, 'Cannot edit a timesheet that has been submitted or approved.')
        return redirect('timetracking:timesheet_detail', timesheet_id=timesheet.id)
    
    if request.method == 'POST':
        form = TimesheetForm(
            request.POST,
            instance=timesheet,
            cleaner=timesheet.cleaner,
            company=timesheet.company
        )
        
        if form.is_valid():
            timesheet = form.save()
            
            # Update the entries based on the new date range
            # First remove existing entries
            timesheet.entries.all().delete()
            
            # Now add entries from the new date range
            entries = TimeEntry.objects.filter(
                cleaner=timesheet.cleaner,
                clock_in_time__date__gte=timesheet.start_date,
                clock_in_time__date__lte=timesheet.end_date,
                is_verified=True
            )
            
            for entry in entries:
                TimesheetEntry.objects.create(
                    timesheet=timesheet,
                    time_entry=entry
                )
            
            # Update the hour totals
            timesheet.update_hours()
            
            messages.success(request, 'Timesheet updated successfully.')
            return redirect('timetracking:timesheet_detail', timesheet_id=timesheet.id)
    else:
        form = TimesheetForm(
            instance=timesheet,
            cleaner=timesheet.cleaner,
            company=timesheet.company
        )
    
    context = {
        'title': 'Edit Timesheet',
        'section': 'timetracking',
        'form': form,
        'timesheet': timesheet,
    }
    
    return render(request, 'timetracking/timesheet_form.html', context)


@login_required
def delete_timesheet_view(request, timesheet_id):
    """View for deleting a timesheet."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Get the timesheet with appropriate permissions check
    if cleaner_profile:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id, cleaner=cleaner_profile)
    elif company_profile:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id, company=company_profile)
    elif request.user.role == User.Role.ADMIN:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id)
    else:
        messages.error(request, 'You do not have permission to delete this timesheet.')
        return redirect('timetracking:timesheet_list')
    
    # Can only delete draft timesheets
    if timesheet.status != 'draft':
        messages.error(request, 'Cannot delete a timesheet that has been submitted or approved.')
        return redirect('timetracking:timesheet_detail', timesheet_id=timesheet.id)
    
    if request.method == 'POST':
        timesheet.delete()
        messages.success(request, 'Timesheet deleted successfully.')
        return redirect('timetracking:timesheet_list')
    
    context = {
        'title': 'Delete Timesheet',
        'section': 'timetracking',
        'timesheet': timesheet,
    }
    
    return render(request, 'timetracking/timesheet_confirm_delete.html', context)


@login_required
def submit_timesheet_view(request, timesheet_id):
    """View for submitting a timesheet for approval."""
    cleaner_profile = get_cleaner_profile(request.user)
    
    # Only cleaners can submit their own timesheets
    if not cleaner_profile:
        messages.error(request, 'Only cleaners can submit timesheets.')
        return redirect('timetracking:timesheet_list')
    
    timesheet = get_object_or_404(Timesheet, id=timesheet_id, cleaner=cleaner_profile)
    
    # Can only submit draft timesheets
    if timesheet.status != 'draft':
        messages.error(request, 'This timesheet has already been submitted or processed.')
        return redirect('timetracking:timesheet_detail', timesheet_id=timesheet.id)
    
    if request.method == 'POST':
        timesheet.status = 'submitted'
        timesheet.submitted_date = timezone.now()
        timesheet.save()
        
        messages.success(request, 'Timesheet submitted for approval.')
        return redirect('timetracking:timesheet_detail', timesheet_id=timesheet.id)
    
    context = {
        'title': 'Submit Timesheet',
        'section': 'timetracking',
        'timesheet': timesheet,
    }
    
    return render(request, 'timetracking/timesheet_submit.html', context)


@login_required
def approve_timesheet_view(request, timesheet_id):
    """View for approving a timesheet."""
    company_profile = get_company_profile(request.user)
    
    # Only companies or admins can approve timesheets
    if not company_profile and request.user.role != User.Role.ADMIN:
        messages.error(request, 'You do not have permission to approve timesheets.')
        return redirect('timetracking:timesheet_list')
    
    # Get the timesheet
    if company_profile:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id, company=company_profile)
    else:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id)
    
    # Can only approve submitted timesheets
    if timesheet.status != 'submitted':
        messages.error(request, 'Only submitted timesheets can be approved.')
        return redirect('timetracking:timesheet_detail', timesheet_id=timesheet.id)
    
    if request.method == 'POST':
        timesheet.status = 'approved'
        timesheet.approved_by = request.user
        timesheet.approved_date = timezone.now()
        timesheet.save()
        
        messages.success(request, 'Timesheet approved.')
        return redirect('timetracking:timesheet_detail', timesheet_id=timesheet.id)
    
    context = {
        'title': 'Approve Timesheet',
        'section': 'timetracking',
        'timesheet': timesheet,
    }
    
    return render(request, 'timetracking/timesheet_approve.html', context)


@login_required
def reject_timesheet_view(request, timesheet_id):
    """View for rejecting a timesheet."""
    company_profile = get_company_profile(request.user)
    
    # Only companies or admins can reject timesheets
    if not company_profile and request.user.role != User.Role.ADMIN:
        messages.error(request, 'You do not have permission to reject timesheets.')
        return redirect('timetracking:timesheet_list')
    
    # Get the timesheet
    if company_profile:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id, company=company_profile)
    else:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id)
    
    # Can only reject submitted timesheets
    if timesheet.status != 'submitted':
        messages.error(request, 'Only submitted timesheets can be rejected.')
        return redirect('timetracking:timesheet_detail', timesheet_id=timesheet.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        timesheet.status = 'rejected'
        timesheet.notes = (timesheet.notes or '') + f'\n\nRejected by {request.user.get_full_name()} at {timezone.now()}: {reason}'
        timesheet.save()
        
        messages.success(request, 'Timesheet rejected.')
        return redirect('timetracking:timesheet_detail', timesheet_id=timesheet.id)
    
    context = {
        'title': 'Reject Timesheet',
        'section': 'timetracking',
        'timesheet': timesheet,
    }
    
    return render(request, 'timetracking/timesheet_reject.html', context)


@login_required
def export_timesheet_view(request, timesheet_id):
    """View for exporting a timesheet to PDF/CSV."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Get the timesheet with appropriate permissions check
    if cleaner_profile:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id, cleaner=cleaner_profile)
    elif company_profile:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id, company=company_profile)
    elif request.user.role == User.Role.ADMIN:
        timesheet = get_object_or_404(Timesheet, id=timesheet_id)
    else:
        messages.error(request, 'You do not have permission to export this timesheet.')
        return redirect('timetracking:timesheet_list')
    
    # Get format (PDF or CSV)
    export_format = request.GET.get('format', 'pdf').lower()
    
    if export_format == 'csv':
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="timesheet_{timesheet.id}.csv"'
        
        import csv
        writer = csv.writer(response)
        writer.writerow(['Date', 'Start Time', 'End Time', 'Break (min)', 'Hours', 'Job', 'Notes'])
        
        for entry in timesheet.entries.all().select_related('time_entry'):
            time_entry = entry.time_entry
            writer.writerow([
                time_entry.clock_in_time.date(),
                time_entry.clock_in_time.time(),
                time_entry.clock_out_time.time() if time_entry.clock_out_time else '',
                time_entry.break_duration_minutes,
                f'{time_entry.total_duration_hours():.2f}',
                time_entry.job_assignment.id if time_entry.job_assignment else '',
                time_entry.notes
            ])
        
        return response
    else:
        # For now, just show a message that PDF export is coming soon
        messages.info(request, 'PDF export will be available soon.')
        return redirect('timetracking:timesheet_detail', timesheet_id=timesheet.id)


# Work schedule management
@login_required
def work_schedule_list_view(request):
    """View for listing work schedules."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Get schedules based on user role
    if cleaner_profile:
        schedules = WorkSchedule.objects.filter(cleaner=cleaner_profile)
    elif company_profile:
        schedules = WorkSchedule.objects.filter(company=company_profile)
    elif request.user.role == User.Role.ADMIN:
        schedules = WorkSchedule.objects.all()
    else:
        schedules = WorkSchedule.objects.none()
    
    # Pagination
    paginator = Paginator(schedules.order_by('-start_date'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Work Schedules',
        'section': 'timetracking',
        'page_obj': page_obj,
        'schedules': page_obj.object_list,
        'is_cleaner': cleaner_profile is not None,
        'is_company': company_profile is not None,
        'is_admin': request.user.role == User.Role.ADMIN,
    }
    
    return render(request, 'timetracking/schedule_list.html', context)


@login_required
def create_work_schedule_view(request):
    """View for creating a new work schedule."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Determine if user can create schedules
    can_create = (company_profile is not None or request.user.role == User.Role.ADMIN)
    
    if not can_create:
        messages.error(request, 'You do not have permission to create work schedules.')
        return redirect('timetracking:schedule_list')
    
    # Need to select a cleaner
    selected_cleaner = None
    cleaner_id = request.GET.get('cleaner_id')
    if cleaner_id:
        selected_cleaner = get_object_or_404(CleanerProfile, id=cleaner_id)
    
    # If no cleaner selected, redirect to cleaner selection
    if not selected_cleaner:
        return redirect('timetracking:select_cleaner_schedule')
    
    if request.method == 'POST':
        form = WorkScheduleForm(
            request.POST,
            cleaner=selected_cleaner,
            company=company_profile
        )
        
        if form.is_valid():
            schedule = form.save()
            messages.success(request, 'Work schedule created successfully.')
            return redirect('timetracking:schedule_detail', schedule_id=schedule.id)
    else:
        # Set default start date to beginning of next week
        today = timezone.now().date()
        days_to_next_monday = (7 - today.weekday()) % 7
        if days_to_next_monday == 0:
            days_to_next_monday = 7  # If today is Monday, go to next Monday
        start_date = today + datetime.timedelta(days=days_to_next_monday)
        
        form = WorkScheduleForm(
            initial={
                'start_date': start_date,
                'schedule_type': 'regular'
            },
            cleaner=selected_cleaner,
            company=company_profile
        )
    
    context = {
        'title': 'Create Work Schedule',
        'section': 'timetracking',
        'form': form,
        'selected_cleaner': selected_cleaner,
    }
    
    return render(request, 'timetracking/schedule_form.html', context)


@login_required
def select_cleaner_schedule_view(request):
    """View for selecting a cleaner for schedule creation."""
    company_profile = get_company_profile(request.user)
    
    if not company_profile and request.user.role != User.Role.ADMIN:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('timetracking:schedule_list')
    
    # Get cleaners based on user role
    if company_profile:
        cleaners = CleanerProfile.objects.filter(company=company_profile)
    else:
        cleaners = CleanerProfile.objects.all()
    
    context = {
        'title': 'Select Cleaner for Schedule',
        'section': 'timetracking',
        'cleaners': cleaners,
        'for_schedule': True,
    }
    
    return render(request, 'timetracking/select_cleaner.html', context)


@login_required
def work_schedule_detail_view(request, schedule_id):
    """View for viewing details of a work schedule."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Get the schedule with appropriate permissions check
    if cleaner_profile:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id, cleaner=cleaner_profile)
    elif company_profile:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id, company=company_profile)
    elif request.user.role == User.Role.ADMIN:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id)
    else:
        messages.error(request, 'You do not have permission to view this work schedule.')
        return redirect('timetracking:schedule_list')
    
    # Get all workdays for this schedule
    workdays = schedule.workdays.all().order_by('date')
    
    context = {
        'title': 'Work Schedule Details',
        'section': 'timetracking',
        'schedule': schedule,
        'workdays': workdays,
        'can_edit': not schedule.is_approved,
        'can_delete': not schedule.is_approved,
        'can_approve': not schedule.is_approved and (company_profile is not None or request.user.role == User.Role.ADMIN),
        'can_add_workday': not schedule.is_approved and (company_profile is not None or request.user.role == User.Role.ADMIN),
    }
    
    return render(request, 'timetracking/schedule_detail.html', context)


@login_required
def edit_work_schedule_view(request, schedule_id):
    """View for editing a work schedule."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Get the schedule with appropriate permissions check
    if cleaner_profile:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id, cleaner=cleaner_profile)
    elif company_profile:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id, company=company_profile)
    elif request.user.role == User.Role.ADMIN:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id)
    else:
        messages.error(request, 'You do not have permission to edit this work schedule.')
        return redirect('timetracking:schedule_list')
    
    # Can only edit unapproved schedules
    if schedule.is_approved:
        messages.error(request, 'Cannot edit an approved work schedule.')
        return redirect('timetracking:schedule_detail', schedule_id=schedule.id)
    
    if request.method == 'POST':
        form = WorkScheduleForm(
            request.POST,
            instance=schedule,
            cleaner=schedule.cleaner,
            company=schedule.company
        )
        
        if form.is_valid():
            schedule = form.save()
            messages.success(request, 'Work schedule updated successfully.')
            return redirect('timetracking:schedule_detail', schedule_id=schedule.id)
    else:
        form = WorkScheduleForm(
            instance=schedule,
            cleaner=schedule.cleaner,
            company=schedule.company
        )
    
    context = {
        'title': 'Edit Work Schedule',
        'section': 'timetracking',
        'form': form,
        'schedule': schedule,
    }
    
    return render(request, 'timetracking/schedule_form.html', context)


@login_required
def delete_work_schedule_view(request, schedule_id):
    """View for deleting a work schedule."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Get the schedule with appropriate permissions check
    if cleaner_profile:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id, cleaner=cleaner_profile)
    elif company_profile:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id, company=company_profile)
    elif request.user.role == User.Role.ADMIN:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id)
    else:
        messages.error(request, 'You do not have permission to delete this work schedule.')
        return redirect('timetracking:schedule_list')
    
    # Can only delete unapproved schedules
    if schedule.is_approved:
        messages.error(request, 'Cannot delete an approved work schedule.')
        return redirect('timetracking:schedule_detail', schedule_id=schedule.id)
    
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Work schedule deleted successfully.')
        return redirect('timetracking:schedule_list')
    
    context = {
        'title': 'Delete Work Schedule',
        'section': 'timetracking',
        'schedule': schedule,
    }
    
    return render(request, 'timetracking/schedule_confirm_delete.html', context)


@login_required
def approve_work_schedule_view(request, schedule_id):
    """View for approving a work schedule."""
    company_profile = get_company_profile(request.user)
    
    # Only companies or admins can approve schedules
    if not company_profile and request.user.role != User.Role.ADMIN:
        messages.error(request, 'You do not have permission to approve work schedules.')
        return redirect('timetracking:schedule_list')
    
    # Get the schedule
    if company_profile:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id, company=company_profile)
    else:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id)
    
    # Can only approve unapproved schedules
    if schedule.is_approved:
        messages.error(request, 'This work schedule is already approved.')
        return redirect('timetracking:schedule_detail', schedule_id=schedule.id)
    
    if request.method == 'POST':
        schedule.is_approved = True
        schedule.approved_by = request.user
        schedule.approved_date = timezone.now()
        schedule.save()
        
        messages.success(request, 'Work schedule approved.')
        return redirect('timetracking:schedule_detail', schedule_id=schedule.id)
    
    context = {
        'title': 'Approve Work Schedule',
        'section': 'timetracking',
        'schedule': schedule,
    }
    
    return render(request, 'timetracking/schedule_approve.html', context)


@login_required
def add_workday_view(request, schedule_id):
    """View for adding a workday to a schedule."""
    company_profile = get_company_profile(request.user)
    
    # Only companies or admins can add workdays
    if not company_profile and request.user.role != User.Role.ADMIN:
        messages.error(request, 'You do not have permission to add workdays.')
        return redirect('timetracking:schedule_list')
    
    # Get the schedule
    if company_profile:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id, company=company_profile)
    else:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id)
    
    # Can only add workdays to unapproved schedules
    if schedule.is_approved:
        messages.error(request, 'Cannot add workdays to an approved schedule.')
        return redirect('timetracking:schedule_detail', schedule_id=schedule.id)
    
    if request.method == 'POST':
        form = WorkDayForm(request.POST, schedule=schedule)
        
        if form.is_valid():
            workday = form.save()
            messages.success(request, 'Workday added successfully.')
            return redirect('timetracking:schedule_detail', schedule_id=schedule.id)
    else:
        form = WorkDayForm(schedule=schedule)
    
    context = {
        'title': 'Add Workday',
        'section': 'timetracking',
        'form': form,
        'schedule': schedule,
    }
    
    return render(request, 'timetracking/workday_form.html', context)


@login_required
def edit_workday_view(request, schedule_id, workday_id):
    """View for editing a workday."""
    company_profile = get_company_profile(request.user)
    
    # Only companies or admins can edit workdays
    if not company_profile and request.user.role != User.Role.ADMIN:
        messages.error(request, 'You do not have permission to edit workdays.')
        return redirect('timetracking:schedule_list')
    
    # Get the schedule and workday
    if company_profile:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id, company=company_profile)
    else:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id)
    
    workday = get_object_or_404(WorkDay, id=workday_id, schedule=schedule)
    
    # Can only edit workdays in unapproved schedules
    if schedule.is_approved:
        messages.error(request, 'Cannot edit workdays in an approved schedule.')
        return redirect('timetracking:schedule_detail', schedule_id=schedule.id)
    
    if request.method == 'POST':
        form = WorkDayForm(request.POST, instance=workday, schedule=schedule)
        
        if form.is_valid():
            workday = form.save()
            messages.success(request, 'Workday updated successfully.')
            return redirect('timetracking:schedule_detail', schedule_id=schedule.id)
    else:
        form = WorkDayForm(instance=workday, schedule=schedule)
    
    context = {
        'title': 'Edit Workday',
        'section': 'timetracking',
        'form': form,
        'schedule': schedule,
        'workday': workday,
    }
    
    return render(request, 'timetracking/workday_form.html', context)


@login_required
def delete_workday_view(request, schedule_id, workday_id):
    """View for deleting a workday."""
    company_profile = get_company_profile(request.user)
    
    # Only companies or admins can delete workdays
    if not company_profile and request.user.role != User.Role.ADMIN:
        messages.error(request, 'You do not have permission to delete workdays.')
        return redirect('timetracking:schedule_list')
    
    # Get the schedule and workday
    if company_profile:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id, company=company_profile)
    else:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id)
    
    workday = get_object_or_404(WorkDay, id=workday_id, schedule=schedule)
    
    # Can only delete workdays from unapproved schedules
    if schedule.is_approved:
        messages.error(request, 'Cannot delete workdays from an approved schedule.')
        return redirect('timetracking:schedule_detail', schedule_id=schedule.id)
    
    if request.method == 'POST':
        workday.delete()
        messages.success(request, 'Workday deleted successfully.')
        return redirect('timetracking:schedule_detail', schedule_id=schedule.id)
    
    context = {
        'title': 'Delete Workday',
        'section': 'timetracking',
        'schedule': schedule,
        'workday': workday,
    }
    
    return render(request, 'timetracking/workday_confirm_delete.html', context)


# API endpoints
@login_required
def get_current_status_view(request):
    """API view for getting current time tracking status for a user."""
    cleaner_profile = get_cleaner_profile(request.user)
    
    if not cleaner_profile:
        return JsonResponse({'error': 'Only cleaners have time tracking status.'}, status=400)
    
    # Get active time entry if any
    try:
        active_entry = TimeEntry.objects.get(cleaner=cleaner_profile, is_active=True)
        is_clocked_in = True
        is_on_break = active_entry.is_on_break()
        current_entry = {
            'id': active_entry.id,
            'clock_in_time': active_entry.clock_in_time.isoformat(),
            'duration_minutes': active_entry.total_duration_minutes(),
            'break_duration_minutes': active_entry.break_duration_minutes,
        }
    except (TimeEntry.DoesNotExist, TimeEntry.MultipleObjectsReturned):
        is_clocked_in = False
        is_on_break = False
        current_entry = None
    
    # Calculate hours for today and this week
    today = timezone.now().date()
    week_start = today - datetime.timedelta(days=today.weekday())
    
    today_entries = TimeEntry.objects.filter(cleaner=cleaner_profile, clock_in_time__date=today)
    week_entries = TimeEntry.objects.filter(
        cleaner=cleaner_profile,
        clock_in_time__date__gte=week_start,
        clock_in_time__date__lte=today
    )
    
    today_hours = sum([entry.total_duration_hours() for entry in today_entries if entry.clock_out_time])
    week_hours = sum([entry.total_duration_hours() for entry in week_entries if entry.clock_out_time])
    
    # Add current active entry hours to today and week hours if clocked in
    if is_clocked_in and not is_on_break:
        current_duration_hours = (timezone.now() - active_entry.clock_in_time).total_seconds() / 3600
        current_duration_hours -= active_entry.break_duration_minutes / 60
        
        today_hours += max(0, current_duration_hours)
        week_hours += max(0, current_duration_hours)
    
    data = {
        'is_clocked_in': is_clocked_in,
        'is_on_break': is_on_break,
        'current_entry': current_entry,
        'today_hours': round(today_hours, 2),
        'week_hours': round(week_hours, 2),
        'server_time': timezone.now().isoformat(),
    }
    
    return JsonResponse(data)


@login_required
def get_active_entries_view(request):
    """API view for getting all active time entries for a user or company."""
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    active_entries = []
    
    if cleaner_profile:
        # For cleaners, get their own active entry
        entries = TimeEntry.objects.filter(cleaner=cleaner_profile, is_active=True)
    elif company_profile:
        # For companies, get all active entries for their cleaners
        entries = TimeEntry.objects.filter(company=company_profile, is_active=True)
    elif request.user.role == User.Role.ADMIN:
        # For admins, get all active entries
        entries = TimeEntry.objects.filter(is_active=True)
    else:
        entries = []
    
    for entry in entries:
        active_entries.append({
            'id': entry.id,
            'cleaner_name': entry.cleaner.user.get_full_name(),
            'cleaner_id': entry.cleaner.id,
            'clock_in_time': entry.clock_in_time.isoformat(),
            'location': entry.clock_in_location_address or 'Unknown location',
            'duration_minutes': entry.total_duration_minutes(),
            'is_on_break': entry.is_on_break(),
            'job_id': entry.job_assignment.id if entry.job_assignment else None,
            'job_name': str(entry.job_assignment) if entry.job_assignment else None,
        })
    
    data = {
        'active_entries': active_entries,
        'count': len(active_entries),
    }
    
    return JsonResponse(data)


@login_required
def get_location_view(request):
    """API view for getting the location for a time entry."""
    entry_id = request.GET.get('entry_id')
    
    if not entry_id:
        return JsonResponse({'error': 'No entry ID provided.'}, status=400)
    
    cleaner_profile = get_cleaner_profile(request.user)
    company_profile = get_company_profile(request.user)
    
    # Get the entry with appropriate permissions check
    if cleaner_profile:
        entry = get_object_or_404(TimeEntry, id=entry_id, cleaner=cleaner_profile)
    elif company_profile:
        entry = get_object_or_404(TimeEntry, id=entry_id, company=company_profile)
    elif request.user.role == User.Role.ADMIN:
        entry = get_object_or_404(TimeEntry, id=entry_id)
    else:
        return JsonResponse({'error': 'You do not have permission to view this time entry.'}, status=403)
    
    data = {
        'clock_in_location': {
            'lat': float(entry.clock_in_location_lat) if entry.clock_in_location_lat else None,
            'lng': float(entry.clock_in_location_lng) if entry.clock_in_location_lng else None,
            'address': entry.clock_in_location_address or 'Unknown location',
        },
        'clock_out_location': {
            'lat': float(entry.clock_out_location_lat) if entry.clock_out_location_lat else None,
            'lng': float(entry.clock_out_location_lng) if entry.clock_out_location_lng else None,
            'address': entry.clock_out_location_address or 'Unknown location',
        },
        'has_location_data': (
            entry.clock_in_location_lat is not None or 
            entry.clock_out_location_lat is not None
        ),
    }
    
    return JsonResponse(data)