from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta

from accounts.models import User, CustomerProfile, CompanyProfile, CleanerProfile
from jobs.models import JobRequest, JobBid, JobAssignment, TimeTracking
from documents.models import Document
from payroll.models import Payslip


def is_customer(user):
    """Check if the user is a customer."""
    return user.is_authenticated and user.role == User.Role.CUSTOMER


def is_company(user):
    """Check if the user is a company."""
    return user.is_authenticated and user.role == User.Role.COMPANY


def is_cleaner(user):
    """Check if the user is a cleaner."""
    return user.is_authenticated and user.role == User.Role.CLEANER


@login_required
@user_passes_test(is_customer)
def customer_dashboard(request):
    """Dashboard for customers."""
    customer_profile = CustomerProfile.objects.get(user=request.user)
    
    # Get recent job requests
    recent_jobs = JobRequest.objects.filter(customer=customer_profile).order_by('-created_at')[:5]
    
    # Get statistics
    total_jobs = JobRequest.objects.filter(customer=customer_profile).count()
    completed_jobs = JobRequest.objects.filter(customer=customer_profile, status='completed').count()
    active_jobs = JobRequest.objects.filter(customer=customer_profile, status__in=['published', 'assigned', 'in_progress']).count()
    
    # Get recent bids on jobs
    recent_bids = JobBid.objects.filter(
        job_request__customer=customer_profile,
        status='pending'
    ).order_by('-created_at')[:5]
    
    # Get upcoming scheduled jobs
    today = timezone.now().date()
    upcoming_jobs = JobRequest.objects.filter(
        customer=customer_profile,
        status='assigned',
        assignment__scheduled_start__gte=today
    ).order_by('assignment__scheduled_start')[:5]
    
    # Get average rating given by customer
    avg_rating = JobRequest.objects.filter(
        customer=customer_profile,
        status='completed',
        assignment__completion__customer_rating__isnull=False
    ).aggregate(avg_rating=Avg('assignment__completion__customer_rating'))['avg_rating'] or 0
    
    context = {
        'recent_jobs': recent_jobs,
        'total_jobs': total_jobs,
        'completed_jobs': completed_jobs,
        'active_jobs': active_jobs,
        'recent_bids': recent_bids,
        'upcoming_jobs': upcoming_jobs,
        'avg_rating': avg_rating,
    }
    
    return render(request, 'dashboard/customer.html', context)


@login_required
@user_passes_test(is_company)
def company_dashboard(request):
    """Dashboard for cleaning companies."""
    company_profile = CompanyProfile.objects.get(user=request.user)
    
    # Get statistics
    total_bids = JobBid.objects.filter(company=company_profile).count()
    accepted_bids = JobBid.objects.filter(company=company_profile, status='accepted').count()
    active_jobs = JobAssignment.objects.filter(company=company_profile, status__in=['scheduled', 'in_progress']).count()
    completed_jobs = JobAssignment.objects.filter(company=company_profile, status='completed').count()
    
    # Get cleaners count
    total_cleaners = CleanerProfile.objects.filter(company=company_profile).count()
    active_cleaners = CleanerProfile.objects.filter(
        company=company_profile,
        job_assignments__status__in=['scheduled', 'in_progress']
    ).distinct().count()
    
    # Get average job rating
    avg_rating = JobAssignment.objects.filter(
        company=company_profile,
        status='completed',
        completion__customer_rating__isnull=False
    ).aggregate(avg_rating=Avg('completion__customer_rating'))['avg_rating'] or 0
    
    # Get recent job assignments
    recent_assignments = JobAssignment.objects.filter(
        company=company_profile
    ).order_by('-created_at')[:5]
    
    # Get new job opportunities
    new_opportunities = JobRequest.objects.filter(
        status='published'
    ).exclude(
        bids__company=company_profile
    ).order_by('-created_at')[:5]
    
    # Get documents that need attention
    recent_documents = Document.objects.filter(
        company=company_profile
    ).order_by('-created_at')[:5]
    
    # Get recent time entries
    recent_time_entries = TimeTracking.objects.filter(
        assignment__company=company_profile
    ).order_by('-clock_in')[:10]
    
    # Calculate revenue for current month
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    
    monthly_revenue = JobAssignment.objects.filter(
        company=company_profile,
        status='completed',
        completion__completed_at__gte=first_day_of_month
    ).aggregate(
        total=Sum('bid__price')
    )['total'] or 0
    
    context = {
        'total_bids': total_bids,
        'accepted_bids': accepted_bids,
        'active_jobs': active_jobs,
        'completed_jobs': completed_jobs,
        'total_cleaners': total_cleaners,
        'active_cleaners': active_cleaners,
        'avg_rating': avg_rating,
        'recent_assignments': recent_assignments,
        'new_opportunities': new_opportunities,
        'recent_documents': recent_documents,
        'recent_time_entries': recent_time_entries,
        'monthly_revenue': monthly_revenue,
    }
    
    return render(request, 'dashboard/company.html', context)


@login_required
@user_passes_test(is_cleaner)
def cleaner_dashboard(request):
    """Dashboard for cleaners."""
    cleaner_profile = CleanerProfile.objects.get(user=request.user)
    
    # Get stats about jobs
    total_jobs = JobAssignment.objects.filter(cleaner=cleaner_profile).count()
    completed_jobs = JobAssignment.objects.filter(cleaner=cleaner_profile, status='completed').count()
    upcoming_jobs = JobAssignment.objects.filter(
        cleaner=cleaner_profile,
        status='scheduled',
        scheduled_start__gte=timezone.now()
    ).count()
    
    # Get upcoming assignments
    upcoming_assignments = JobAssignment.objects.filter(
        cleaner=cleaner_profile,
        status='scheduled',
        scheduled_start__gte=timezone.now()
    ).order_by('scheduled_start')[:5]
    
    # Get recent time entries
    recent_time_entries = TimeTracking.objects.filter(
        cleaner=cleaner_profile
    ).order_by('-clock_in')[:10]
    
    # Calculate hours worked this month
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    
    monthly_hours = TimeTracking.objects.filter(
        cleaner=cleaner_profile,
        clock_in__date__gte=first_day_of_month,
        clock_out__isnull=False
    ).aggregate(
        total_minutes=Sum('total_minutes')
    )['total_minutes'] or 0
    
    monthly_hours = monthly_hours / 60  # Convert to hours
    
    # Get recent payslips
    recent_payslips = Payslip.objects.filter(
        cleaner=cleaner_profile
    ).order_by('-pay_period__end_date')[:3]
    
    # Get active time tracking entry if any
    active_time_entry = TimeTracking.objects.filter(
        cleaner=cleaner_profile,
        clock_out__isnull=True
    ).first()
    
    context = {
        'total_jobs': total_jobs,
        'completed_jobs': completed_jobs,
        'upcoming_jobs': upcoming_jobs,
        'upcoming_assignments': upcoming_assignments,
        'recent_time_entries': recent_time_entries,
        'monthly_hours': monthly_hours,
        'recent_payslips': recent_payslips,
        'active_time_entry': active_time_entry,
    }
    
    return render(request, 'dashboard/cleaner.html', context)


@login_required
def dashboard(request):
    """Main dashboard router that redirects to the appropriate dashboard."""
    user = request.user
    
    if not user.is_profile_complete:
        # If profile is not complete, redirect to complete profile
        return redirect('complete_profile')
    
    if user.role == User.Role.CUSTOMER:
        return redirect('customer_dashboard')
    elif user.role == User.Role.COMPANY:
        return redirect('company_dashboard')
    elif user.role == User.Role.CLEANER:
        return redirect('cleaner_dashboard')
    else:
        # Fallback for admin or undefined roles
        return redirect('home')
