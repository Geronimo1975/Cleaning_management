from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Avg, Count

from accounts.models import User, CustomerProfile, CompanyProfile, CleanerProfile
from .models import (
    ServiceCategory, JobRequest, JobBid, JobAssignment, 
    TimeTracking, JobCompletion
)
from .forms import (
    JobRequestForm, JobBidForm, JobAssignmentForm, 
    TimeTrackingForm, JobCompletionForm, JobFeedbackForm
)


def is_customer(user):
    """Check if user is a customer."""
    return user.is_authenticated and user.role == User.Role.CUSTOMER


def is_company(user):
    """Check if user is a company."""
    return user.is_authenticated and user.role == User.Role.COMPANY


def is_cleaner(user):
    """Check if user is a cleaner."""
    return user.is_authenticated and user.role == User.Role.CLEANER


@login_required
def job_list_view(request):
    """View for listing job requests based on user role."""
    user = request.user
    
    if user.role == User.Role.CUSTOMER:
        # Customers see their own job requests
        customer_profile = CustomerProfile.objects.get(user=user)
        job_requests = JobRequest.objects.filter(customer=customer_profile).order_by('-created_at')
        template = 'jobs/customer_job_list.html'
        
    elif user.role == User.Role.COMPANY:
        # Companies see available jobs and their bids
        company_profile = CompanyProfile.objects.get(user=user)
        
        # Get job requests where status is published or the company has already bid
        available_jobs = JobRequest.objects.filter(
            (Q(status='published') & ~Q(bids__company=company_profile)) |
            Q(bids__company=company_profile)
        ).distinct().order_by('-created_at')
        
        # Get jobs assigned to this company
        assigned_jobs = JobRequest.objects.filter(
            assignment__company=company_profile
        ).order_by('-created_at')
        
        context = {
            'available_jobs': available_jobs,
            'assigned_jobs': assigned_jobs,
        }
        
        template = 'jobs/company_job_list.html'
        return render(request, template, context)
        
    elif user.role == User.Role.CLEANER:
        # Cleaners see jobs assigned to them
        cleaner_profile = CleanerProfile.objects.get(user=user)
        job_requests = JobRequest.objects.filter(
            assignment__cleaner=cleaner_profile
        ).order_by('-created_at')
        template = 'jobs/cleaner_job_list.html'
    
    else:
        messages.error(request, 'You are not authorized to view job listings.')
        return redirect('home')
    
    # Paginate results
    paginator = Paginator(job_requests, 10)
    page = request.GET.get('page')
    
    try:
        jobs = paginator.page(page)
    except PageNotAnInteger:
        jobs = paginator.page(1)
    except EmptyPage:
        jobs = paginator.page(paginator.num_pages)
    
    return render(request, template, {'jobs': jobs})


@login_required
@user_passes_test(is_customer)
def create_job_request_view(request):
    """View for customers to create new job requests."""
    if request.method == 'POST':
        form = JobRequestForm(request.POST)
        if form.is_valid():
            job_request = form.save(commit=False)
            customer_profile = CustomerProfile.objects.get(user=request.user)
            job_request.customer = customer_profile
            job_request.status = 'published'  # or 'draft' if you want to implement a draft feature
            job_request.save()
            
            messages.success(request, 'Job request created successfully!')
            return redirect('job_detail', job_id=job_request.id)
    else:
        form = JobRequestForm()
    
    service_categories = ServiceCategory.objects.all()
    
    return render(request, 'jobs/create.html', {
        'form': form,
        'service_categories': service_categories,
    })


@login_required
def job_detail_view(request, job_id):
    """View for displaying job request details."""
    job_request = get_object_or_404(JobRequest, id=job_id)
    user = request.user
    
    # Check permissions based on role
    if user.role == User.Role.CUSTOMER:
        customer_profile = CustomerProfile.objects.get(user=user)
        if job_request.customer != customer_profile:
            messages.error(request, 'You are not authorized to view this job request.')
            return redirect('job_list')
    
    elif user.role == User.Role.COMPANY:
        company_profile = CompanyProfile.objects.get(user=user)
        
        # Companies can see published jobs or jobs they've bid on or been assigned to
        if (job_request.status not in ['published', 'assigned'] and 
            not JobBid.objects.filter(job_request=job_request, company=company_profile).exists() and
            not JobAssignment.objects.filter(job_request=job_request, company=company_profile).exists()):
            messages.error(request, 'You are not authorized to view this job request.')
            return redirect('job_list')
        
        # Check if the company has already placed a bid
        existing_bid = JobBid.objects.filter(job_request=job_request, company=company_profile).first()
        
        # Create bid form if no existing bid
        if not existing_bid and job_request.status == 'published':
            if request.method == 'POST' and 'submit_bid' in request.POST:
                bid_form = JobBidForm(request.POST)
                if bid_form.is_valid():
                    bid = bid_form.save(commit=False)
                    bid.job_request = job_request
                    bid.company = company_profile
                    bid.save()
                    
                    messages.success(request, 'Your bid has been submitted successfully!')
                    return redirect('job_detail', job_id=job_request.id)
            else:
                bid_form = JobBidForm()
        else:
            bid_form = None
            
        return render(request, 'jobs/detail.html', {
            'job': job_request,
            'bid': existing_bid,
            'bid_form': bid_form,
        })
    
    elif user.role == User.Role.CLEANER:
        cleaner_profile = CleanerProfile.objects.get(user=user)
        
        # Cleaners can only see jobs assigned to them
        if not JobAssignment.objects.filter(job_request=job_request, cleaner=cleaner_profile).exists():
            messages.error(request, 'You are not authorized to view this job request.')
            return redirect('job_list')
        
        assignment = JobAssignment.objects.get(job_request=job_request, cleaner=cleaner_profile)
        
        # Time tracking
        current_time_entry = TimeTracking.objects.filter(
            assignment=assignment,
            cleaner=cleaner_profile,
            clock_out__isnull=True
        ).first()
        
        if request.method == 'POST':
            if 'clock_in' in request.POST:
                # Create new time entry
                time_entry = TimeTracking(
                    assignment=assignment,
                    cleaner=cleaner_profile,
                    clock_in=timezone.now(),
                    status='active'
                )
                
                # Save location if provided
                if 'lat' in request.POST and 'lng' in request.POST:
                    time_entry.clock_in_lat = request.POST.get('lat')
                    time_entry.clock_in_lng = request.POST.get('lng')
                
                time_entry.save()
                messages.success(request, 'Clock-in recorded successfully!')
                return redirect('job_detail', job_id=job_request.id)
                
            elif 'clock_out' in request.POST and current_time_entry:
                # Update existing time entry
                current_time_entry.clock_out = timezone.now()
                
                # Save location if provided
                if 'lat' in request.POST and 'lng' in request.POST:
                    current_time_entry.clock_out_lat = request.POST.get('lat')
                    current_time_entry.clock_out_lng = request.POST.get('lng')
                
                # Calculate duration
                current_time_entry.total_minutes = current_time_entry.calculate_duration()
                current_time_entry.status = 'completed'
                current_time_entry.save()
                
                messages.success(request, 'Clock-out recorded successfully!')
                return redirect('job_detail', job_id=job_request.id)
                
            elif 'break_start' in request.POST and current_time_entry:
                current_time_entry.break_start = timezone.now()
                current_time_entry.save()
                messages.success(request, 'Break start recorded!')
                return redirect('job_detail', job_id=job_request.id)
                
            elif 'break_end' in request.POST and current_time_entry and current_time_entry.break_start:
                current_time_entry.break_end = timezone.now()
                current_time_entry.save()
                messages.success(request, 'Break end recorded!')
                return redirect('job_detail', job_id=job_request.id)
            
            elif 'complete_job' in request.POST:
                completion_form = JobCompletionForm(request.POST)
                if completion_form.is_valid():
                    completion = completion_form.save(commit=False)
                    completion.assignment = assignment
                    completion.save()
                    
                    # Update assignment status
                    assignment.status = 'completed'
                    assignment.save()
                    
                    # Update job request status
                    job_request.status = 'completed'
                    job_request.save()
                    
                    messages.success(request, 'Job marked as completed!')
                    return redirect('job_list')
        else:
            completion_form = JobCompletionForm(initial={'completed_at': timezone.now()})
        
        time_entries = TimeTracking.objects.filter(
            assignment=assignment,
            cleaner=cleaner_profile
        ).order_by('-clock_in')
        
        return render(request, 'jobs/detail.html', {
            'job': job_request,
            'assignment': assignment,
            'current_time_entry': current_time_entry,
            'time_entries': time_entries,
            'completion_form': completion_form,
        })
    
    # For customers, just show the job details and bids if applicable
    bids = JobBid.objects.filter(job_request=job_request)
    assignment = JobAssignment.objects.filter(job_request=job_request).first()
    
    # For completed jobs, show feedback form for customers
    completion = JobCompletion.objects.filter(assignment=assignment).first() if assignment else None
    
    if user.role == User.Role.CUSTOMER and completion and not completion.customer_rating:
        if request.method == 'POST' and 'submit_feedback' in request.POST:
            feedback_form = JobFeedbackForm(request.POST, instance=completion)
            if feedback_form.is_valid():
                feedback_form.save()
                messages.success(request, 'Thank you for your feedback!')
                return redirect('job_detail', job_id=job_request.id)
        else:
            feedback_form = JobFeedbackForm()
    else:
        feedback_form = None
    
    return render(request, 'jobs/detail.html', {
        'job': job_request,
        'bids': bids,
        'assignment': assignment,
        'completion': completion,
        'feedback_form': feedback_form,
    })


@login_required
@user_passes_test(is_customer)
def manage_bids_view(request, job_id):
    """View for customers to manage bids on their job requests."""
    job_request = get_object_or_404(JobRequest, id=job_id)
    customer_profile = CustomerProfile.objects.get(user=request.user)
    
    # Verify ownership
    if job_request.customer != customer_profile:
        messages.error(request, 'You are not authorized to manage bids for this job request.')
        return redirect('job_list')
    
    # Get all bids for this job
    bids = JobBid.objects.filter(job_request=job_request).order_by('price')
    
    if request.method == 'POST':
        if 'accept_bid' in request.POST:
            bid_id = request.POST.get('accept_bid')
            bid = get_object_or_404(JobBid, id=bid_id, job_request=job_request)
            
            # Accept this bid
            bid.status = 'accepted'
            bid.save()
            
            # Reject all other bids
            JobBid.objects.filter(job_request=job_request).exclude(id=bid_id).update(status='rejected')
            
            # Update job request status
            job_request.status = 'assigned'
            job_request.save()
            
            messages.success(request, f'You have accepted the bid from {bid.company.company_name}.')
            return redirect('job_detail', job_id=job_request.id)
    
    return render(request, 'jobs/manage_bids.html', {
        'job': job_request,
        'bids': bids,
    })


@login_required
@user_passes_test(is_company)
def assign_cleaner_view(request, job_id, bid_id):
    """View for companies to assign cleaners to accepted bids."""
    job_request = get_object_or_404(JobRequest, id=job_id)
    bid = get_object_or_404(JobBid, id=bid_id, job_request=job_request)
    company_profile = CompanyProfile.objects.get(user=request.user)
    
    # Verify ownership
    if bid.company != company_profile:
        messages.error(request, 'You are not authorized to assign cleaners to this job.')
        return redirect('job_list')
    
    # Verify bid is accepted
    if bid.status != 'accepted':
        messages.error(request, 'You can only assign cleaners to accepted bids.')
        return redirect('job_detail', job_id=job_request.id)
    
    # Check if already assigned
    existing_assignment = JobAssignment.objects.filter(job_request=job_request).first()
    if existing_assignment:
        messages.info(request, 'A cleaner has already been assigned to this job.')
        return redirect('job_detail', job_id=job_request.id)
    
    # Get company's cleaners
    cleaners = CleanerProfile.objects.filter(company=company_profile)
    
    if request.method == 'POST':
        form = JobAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.job_request = job_request
            assignment.bid = bid
            assignment.company = company_profile
            
            cleaner_id = form.cleaned_data['cleaner'].id
            cleaner = get_object_or_404(CleanerProfile, id=cleaner_id, company=company_profile)
            assignment.cleaner = cleaner
            
            assignment.save()
            
            messages.success(request, f'You have assigned {cleaner.user.get_full_name()} to this job.')
            return redirect('job_detail', job_id=job_request.id)
    else:
        # Pre-fill with bid details
        initial_data = {
            'scheduled_start': bid.can_start_at,
            'scheduled_end': bid.can_start_at + timezone.timedelta(hours=bid.estimated_hours),
        }
        form = JobAssignmentForm(initial=initial_data)
        form.fields['cleaner'].queryset = cleaners
    
    return render(request, 'jobs/assign_cleaner.html', {
        'form': form,
        'job': job_request,
        'bid': bid,
        'cleaners': cleaners,
    })


@login_required
@user_passes_test(is_cleaner)
def time_tracking_history_view(request):
    """View for cleaners to see their time tracking history."""
    cleaner_profile = CleanerProfile.objects.get(user=request.user)
    
    # Get all time entries for this cleaner
    time_entries = TimeTracking.objects.filter(cleaner=cleaner_profile).order_by('-clock_in')
    
    # Group by job/week for clarity
    grouped_entries = {}
    for entry in time_entries:
        job_id = entry.assignment.job_request.id
        job_title = entry.assignment.job_request.title
        
        # Get week number
        week_key = entry.clock_in.strftime('%Y-%U')  # Year-WeekNumber
        week_display = f"Week of {entry.clock_in.strftime('%b %d, %Y')}"
        
        if job_id not in grouped_entries:
            grouped_entries[job_id] = {
                'job_title': job_title,
                'weeks': {}
            }
        
        if week_key not in grouped_entries[job_id]['weeks']:
            grouped_entries[job_id]['weeks'][week_key] = {
                'display': week_display,
                'entries': [],
                'total_minutes': 0
            }
        
        grouped_entries[job_id]['weeks'][week_key]['entries'].append(entry)
        
        if entry.total_minutes:
            grouped_entries[job_id]['weeks'][week_key]['total_minutes'] += entry.total_minutes
    
    return render(request, 'jobs/time_tracking_history.html', {
        'grouped_entries': grouped_entries,
    })
