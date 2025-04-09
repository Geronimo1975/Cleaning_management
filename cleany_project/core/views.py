from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.db import transaction

from .models import (
    User, Company, Cleaner, Customer, ServiceType, Job, JobApplication,
    Document, Timesheet, Payroll, Rating, Notification
)
from .forms import (
    CustomUserCreationForm, CompanyForm, CleanerForm, CustomerForm,
    ServiceTypeForm, JobForm, JobApplicationForm, DocumentUploadForm,
    TimesheetForm, PayrollForm, RatingForm, UserProfileForm,
    JobStatusUpdateForm, JobCompletionForm, JobAssignmentForm
)
from .utils import calculate_payroll, send_notification


class HomeView(TemplateView):
    """Home page view."""
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service_types'] = ServiceType.objects.all()[:6]
        
        # Get top-rated companies
        top_companies = Company.objects.annotate(
            avg_rating=Avg('user__received_ratings__score'),
            num_ratings=Count('user__received_ratings')
        ).filter(num_ratings__gt=0).order_by('-avg_rating')[:3]
        
        context['top_companies'] = top_companies
        return context


def register_view(request):
    """User registration view."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role')
            
            # Create role-specific profile
            if role == User.Role.CUSTOMER:
                Customer.objects.create(user=user)
            elif role == User.Role.COMPANY:
                # Redirect to company registration form
                login(request, user)
                messages.success(request, "Account created successfully! Please complete your company profile.")
                return redirect('company_registration')
            elif role == User.Role.CLEANER:
                # Redirect to cleaner registration form
                login(request, user)
                messages.success(request, "Account created successfully! Please complete your cleaner profile.")
                return redirect('cleaner_registration')
            
            # Log in the user
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'core/register.html', {'form': form})


@login_required
def dashboard_view(request):
    """
    Main dashboard view that redirects to role-specific dashboards.
    """
    user = request.user
    
    if user.is_customer():
        return redirect('customer_dashboard')
    elif user.is_company():
        return redirect('company_dashboard')
    elif user.is_cleaner():
        return redirect('cleaner_dashboard')
    else:
        # Handle admin or other roles
        return redirect('admin:index')


@login_required
def customer_dashboard(request):
    """Dashboard for customers."""
    try:
        profile = request.user.customer_profile
    except Customer.DoesNotExist:
        messages.error(request, "Customer profile not found.")
        return redirect('home')
    
    # Get active jobs
    active_jobs = Job.objects.filter(
        customer=profile,
        status__in=['OPEN', 'ASSIGNED', 'IN_PROGRESS']
    ).order_by('start_datetime')
    
    # Get completed jobs
    completed_jobs = Job.objects.filter(
        customer=profile,
        status='COMPLETED'
    ).order_by('-end_datetime')[:5]
    
    # Get notifications
    notifications = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).order_by('-created_at')[:5]
    
    context = {
        'profile': profile,
        'active_jobs': active_jobs,
        'completed_jobs': completed_jobs,
        'notifications': notifications,
    }
    
    return render(request, 'core/dashboard_customer.html', context)


@login_required
def company_dashboard(request):
    """Dashboard for cleaning companies."""
    try:
        profile = request.user.company_profile
    except Company.DoesNotExist:
        messages.error(request, "Company profile not found.")
        return redirect('company_registration')
    
    # Get jobs assigned to company
    assigned_jobs = Job.objects.filter(
        company=profile,
        status__in=['ASSIGNED', 'IN_PROGRESS']
    ).order_by('start_datetime')
    
    # Get job applications
    open_applications = JobApplication.objects.filter(
        company=profile, 
        status='PENDING'
    ).order_by('-created_at')
    
    # Get company's cleaners
    cleaners = Cleaner.objects.filter(company=profile)
    
    # Get recent payrolls
    recent_payrolls = Payroll.objects.filter(
        company=profile
    ).order_by('-created_at')[:5]
    
    # Get notifications
    notifications = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).order_by('-created_at')[:5]
    
    context = {
        'profile': profile,
        'assigned_jobs': assigned_jobs,
        'open_applications': open_applications,
        'cleaners': cleaners,
        'recent_payrolls': recent_payrolls,
        'notifications': notifications,
    }
    
    return render(request, 'core/dashboard_company.html', context)


@login_required
def cleaner_dashboard(request):
    """Dashboard for cleaners."""
    try:
        profile = request.user.cleaner_profile
    except Cleaner.DoesNotExist:
        messages.error(request, "Cleaner profile not found.")
        return redirect('cleaner_registration')
    
    # Get assigned jobs
    assigned_jobs = Job.objects.filter(
        cleaner=profile,
        status__in=['ASSIGNED', 'IN_PROGRESS']
    ).order_by('start_datetime')
    
    # Get job applications
    applications = JobApplication.objects.filter(
        cleaner=profile
    ).order_by('-created_at')[:5]
    
    # Get recent timesheets
    recent_timesheets = Timesheet.objects.filter(
        cleaner=profile
    ).order_by('-date')[:5]
    
    # Get recent payrolls
    recent_payrolls = Payroll.objects.filter(
        cleaner=profile
    ).order_by('-created_at')[:5]
    
    # Get notifications
    notifications = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).order_by('-created_at')[:5]
    
    context = {
        'profile': profile,
        'assigned_jobs': assigned_jobs,
        'applications': applications,
        'recent_timesheets': recent_timesheets,
        'recent_payrolls': recent_payrolls,
        'notifications': notifications,
    }
    
    return render(request, 'core/dashboard_cleaner.html', context)


@login_required
def company_registration(request):
    """View for completing company registration."""
    if request.user.role != User.Role.COMPANY:
        messages.error(request, "Only company accounts can register company profiles.")
        return redirect('dashboard')
    
    try:
        # Check if company profile already exists
        profile = request.user.company_profile
        messages.info(request, "Your company profile already exists.")
        return redirect('company_dashboard')
    except Company.DoesNotExist:
        # Continue with registration
        pass
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(commit=False)
            company.user = request.user
            company.save()
            
            messages.success(request, "Company profile created successfully!")
            return redirect('company_dashboard')
    else:
        form = CompanyForm()
    
    return render(request, 'core/register_company.html', {'form': form})


@login_required
def cleaner_registration(request):
    """View for completing cleaner registration."""
    if request.user.role != User.Role.CLEANER:
        messages.error(request, "Only cleaner accounts can register cleaner profiles.")
        return redirect('dashboard')
    
    try:
        # Check if cleaner profile already exists
        profile = request.user.cleaner_profile
        messages.info(request, "Your cleaner profile already exists.")
        return redirect('cleaner_dashboard')
    except Cleaner.DoesNotExist:
        # Continue with registration
        pass
    
    if request.method == 'POST':
        form = CleanerForm(request.POST)
        if form.is_valid():
            cleaner = form.save(commit=False)
            cleaner.user = request.user
            cleaner.save()
            # Save many-to-many data
            form.save_m2m()
            
            messages.success(request, "Cleaner profile created successfully!")
            return redirect('cleaner_dashboard')
    else:
        form = CleanerForm()
    
    # Get list of companies for the form
    companies = Company.objects.all()
    
    return render(request, 'core/register_cleaner.html', {
        'form': form,
        'companies': companies
    })


class JobListView(ListView):
    """View for listing available jobs."""
    model = Job
    template_name = 'core/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Job.objects.filter(status='OPEN')
        
        # Filter by job type if specified
        job_type = self.request.GET.get('job_type')
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        
        # Filter by service type if specified
        service_type = self.request.GET.get('service_type')
        if service_type:
            queryset = queryset.filter(service_type__id=service_type)
        
        # Filter by location if specified
        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        return queryset.order_by('start_datetime')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service_types'] = ServiceType.objects.all()
        return context


class JobDetailView(DetailView):
    """View for job details."""
    model = Job
    template_name = 'core/job_detail.html'
    context_object_name = 'job'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.object
        
        # Add application form for companies and cleaners
        user = self.request.user
        if user.is_authenticated:
            if user.is_company():
                context['application_form'] = JobApplicationForm()
            elif user.is_cleaner() and hasattr(user, 'cleaner_profile'):
                # Check if cleaner already applied to this job
                try:
                    cleaner = user.cleaner_profile
                    application = JobApplication.objects.get(job=job, cleaner=cleaner)
                    context['existing_application'] = application
                except JobApplication.DoesNotExist:
                    context['application_form'] = JobApplicationForm()
        
        # Get job applications if user is job creator or company
        if user.is_authenticated and (
            (user.is_customer() and job.customer.user == user) or
            (user.is_company() and job.company and job.company.user == user)
        ):
            context['applications'] = job.applications.all()
        
        return context


@login_required
def create_job(request):
    """View for creating a new job."""
    if not request.user.is_customer():
        messages.error(request, "Only customers can create jobs.")
        return redirect('dashboard')
    
    try:
        customer = request.user.customer_profile
    except Customer.DoesNotExist:
        Customer.objects.create(user=request.user)
        customer = request.user.customer_profile
    
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.customer = customer
            job.status = Job.Status.OPEN
            job.save()
            
            messages.success(request, "Job created successfully!")
            return redirect('job_detail', pk=job.pk)
    else:
        form = JobForm()
    
    return render(request, 'core/job_create.html', {'form': form})


@login_required
@require_POST
def apply_to_job(request, job_id):
    """View for applying to a job."""
    job = get_object_or_404(Job, pk=job_id, status=Job.Status.OPEN)
    
    # Check if user is a company or cleaner
    user = request.user
    if not (user.is_company() or user.is_cleaner()):
        messages.error(request, "Only companies or cleaners can apply to jobs.")
        return redirect('job_detail', pk=job_id)
    
    form = JobApplicationForm(request.POST)
    
    if form.is_valid():
        application = form.save(commit=False)
        application.job = job
        
        if user.is_company():
            try:
                company = user.company_profile
            except Company.DoesNotExist:
                messages.error(request, "Company profile not found.")
                return redirect('company_registration')
            
            # Company applications don't need a cleaner
            application.company = company
            application.cleaner = None
        
        elif user.is_cleaner():
            try:
                cleaner = user.cleaner_profile
            except Cleaner.DoesNotExist:
                messages.error(request, "Cleaner profile not found.")
                return redirect('cleaner_registration')
            
            # If cleaner is associated with a company, use that company
            application.cleaner = cleaner
            application.company = cleaner.company
            
            if not application.company:
                messages.error(request, "You must be associated with a company to apply to jobs.")
                return redirect('job_detail', pk=job_id)
        
        try:
            # Check for existing application
            existing = JobApplication.objects.get(
                job=job, 
                cleaner=application.cleaner if application.cleaner else None,
                company=application.company
            )
            messages.error(request, "You have already applied to this job.")
            return redirect('job_detail', pk=job_id)
        except JobApplication.DoesNotExist:
            # Save new application
            application.save()
            
            # Send notification to customer
            send_notification(
                job.customer.user,
                f"New Application for {job.title}",
                f"A new application has been received from {application.company.name}.",
                job
            )
            
            messages.success(request, "Application submitted successfully!")
            return redirect('job_detail', pk=job_id)
    
    # If form is invalid
    messages.error(request, "There was an error with your application.")
    return redirect('job_detail', pk=job_id)


@login_required
def accept_application(request, application_id):
    """View for accepting a job application."""
    application = get_object_or_404(JobApplication, pk=application_id, status='PENDING')
    job = application.job
    
    # Check if user is the customer who created the job
    if not request.user.is_customer() or job.customer.user != request.user:
        messages.error(request, "You don't have permission to accept this application.")
        return redirect('job_detail', pk=job.pk)
    
    # Update job and application status
    with transaction.atomic():
        application.status = 'ACCEPTED'
        application.save()
        
        job.company = application.company
        job.cleaner = application.cleaner
        job.status = Job.Status.ASSIGNED
        job.save()
        
        # Reject all other applications
        JobApplication.objects.filter(job=job, status='PENDING').exclude(pk=application.pk).update(status='REJECTED')
        
        # Send notifications
        send_notification(
            application.company.user,
            f"Application Accepted: {job.title}",
            f"Your application for the job '{job.title}' has been accepted.",
            job
        )
        
        if application.cleaner:
            send_notification(
                application.cleaner.user,
                f"Job Assigned: {job.title}",
                f"You have been assigned to the job '{job.title}'.",
                job
            )
    
    messages.success(request, "Application accepted successfully!")
    return redirect('job_detail', pk=job.pk)


@login_required
def reject_application(request, application_id):
    """View for rejecting a job application."""
    application = get_object_or_404(JobApplication, pk=application_id, status='PENDING')
    job = application.job
    
    # Check if user is the customer who created the job
    if not request.user.is_customer() or job.customer.user != request.user:
        messages.error(request, "You don't have permission to reject this application.")
        return redirect('job_detail', pk=job.pk)
    
    # Update application status
    application.status = 'REJECTED'
    application.save()
    
    # Send notification
    send_notification(
        application.company.user,
        f"Application Rejected: {job.title}",
        f"Your application for the job '{job.title}' has been rejected.",
        job
    )
    
    messages.success(request, "Application rejected successfully!")
    return redirect('job_detail', pk=job.pk)


@login_required
def start_job(request, job_id):
    """View for starting a job (changing status to IN_PROGRESS)."""
    job = get_object_or_404(Job, pk=job_id, status=Job.Status.ASSIGNED)
    
    # Check if user is the assigned cleaner
    if not request.user.is_cleaner() or not hasattr(request.user, 'cleaner_profile') or job.cleaner != request.user.cleaner_profile:
        messages.error(request, "You don't have permission to start this job.")
        return redirect('job_detail', pk=job.pk)
    
    # Update job status and actual start time
    job.status = Job.Status.IN_PROGRESS
    job.actual_start_time = timezone.now()
    job.save()
    
    # Send notifications
    send_notification(
        job.customer.user,
        f"Job Started: {job.title}",
        f"Your job '{job.title}' has been started by the cleaner.",
        job
    )
    
    if job.company:
        send_notification(
            job.company.user,
            f"Job Started: {job.title}",
            f"The job '{job.title}' has been started by the cleaner.",
            job
        )
    
    messages.success(request, "Job started successfully!")
    return redirect('job_detail', pk=job.pk)


@login_required
def complete_job(request, job_id):
    """View for completing a job."""
    job = get_object_or_404(Job, pk=job_id, status=Job.Status.IN_PROGRESS)
    
    # Check if user is the assigned cleaner
    if not request.user.is_cleaner() or not hasattr(request.user, 'cleaner_profile') or job.cleaner != request.user.cleaner_profile:
        messages.error(request, "You don't have permission to complete this job.")
        return redirect('job_detail', pk=job.pk)
    
    if request.method == 'POST':
        form = JobCompletionForm(request.POST)
        if form.is_valid():
            # Update job status and actual end time
            job.status = Job.Status.COMPLETED
            job.actual_start_time = form.cleaned_data['actual_start_time']
            job.actual_end_time = form.cleaned_data['actual_end_time']
            job.end_datetime = form.cleaned_data['actual_end_time']
            job.save()
            
            # Create timesheet entry
            Timesheet.objects.create(
                job=job,
                cleaner=job.cleaner,
                date=job.actual_end_time.date(),
                start_time=job.actual_start_time.time(),
                end_time=job.actual_end_time.time(),
                break_duration=0,  # Default to 0, can be updated later
                notes=f"Auto-generated from job completion: {job.title}"
            )
            
            # Send notifications
            send_notification(
                job.customer.user,
                f"Job Completed: {job.title}",
                f"Your job '{job.title}' has been completed by the cleaner.",
                job
            )
            
            if job.company:
                send_notification(
                    job.company.user,
                    f"Job Completed: {job.title}",
                    f"The job '{job.title}' has been completed by the cleaner.",
                    job
                )
            
            messages.success(request, "Job completed successfully!")
            return redirect('job_detail', pk=job.pk)
    else:
        # Pre-fill form with current time data
        initial_data = {}
        if job.actual_start_time:
            initial_data['actual_start_time'] = job.actual_start_time
        else:
            initial_data['actual_start_time'] = job.start_datetime
        
        initial_data['actual_end_time'] = timezone.now()
        form = JobCompletionForm(initial=initial_data)
    
    return render(request, 'core/job_complete.html', {'form': form, 'job': job})


@login_required
def create_timesheet(request, job_id=None):
    """View for creating a timesheet."""
    if not request.user.is_cleaner():
        messages.error(request, "Only cleaners can create timesheets.")
        return redirect('dashboard')
    
    try:
        cleaner = request.user.cleaner_profile
    except Cleaner.DoesNotExist:
        messages.error(request, "Cleaner profile not found.")
        return redirect('cleaner_registration')
    
    initial_data = {}
    if job_id:
        job = get_object_or_404(Job, pk=job_id)
        if job.cleaner != cleaner:
            messages.error(request, "You can only create timesheets for your assigned jobs.")
            return redirect('dashboard')
        initial_data['job'] = job
    
    if request.method == 'POST':
        form = TimesheetForm(request.POST)
        if form.is_valid():
            timesheet = form.save(commit=False)
            timesheet.cleaner = cleaner
            
            if 'job' in initial_data:
                timesheet.job = initial_data['job']
            
            # Check for duplicate timesheet
            if Timesheet.objects.filter(job=timesheet.job, cleaner=cleaner, date=timesheet.date).exists():
                messages.error(request, "A timesheet for this job and date already exists.")
                return redirect('timesheet_list')
            
            timesheet.save()
            
            # Notify company if cleaner is associated with one
            if cleaner.company:
                send_notification(
                    cleaner.company.user,
                    "New Timesheet Submitted",
                    f"A new timesheet has been submitted by {cleaner.user.get_full_name()} for {timesheet.date}.",
                    timesheet.job
                )
            
            messages.success(request, "Timesheet created successfully!")
            return redirect('timesheet_list')
    else:
        form = TimesheetForm(initial=initial_data)
    
    # Get jobs assigned to cleaner
    assigned_jobs = Job.objects.filter(cleaner=cleaner)
    
    return render(request, 'core/timesheet_create.html', {'form': form, 'assigned_jobs': assigned_jobs})


@login_required
def timesheet_list(request):
    """View for listing timesheets."""
    user = request.user
    
    if user.is_cleaner():
        try:
            cleaner = user.cleaner_profile
            timesheets = Timesheet.objects.filter(cleaner=cleaner).order_by('-date')
        except Cleaner.DoesNotExist:
            messages.error(request, "Cleaner profile not found.")
            return redirect('cleaner_registration')
    
    elif user.is_company():
        try:
            company = user.company_profile
            timesheets = Timesheet.objects.filter(
                cleaner__company=company
            ).order_by('-date')
        except Company.DoesNotExist:
            messages.error(request, "Company profile not found.")
            return redirect('company_registration')
    
    else:
        messages.error(request, "Only cleaners and companies can view timesheets.")
        return redirect('dashboard')
    
    # Pagination
    paginator = Paginator(timesheets, 10)
    page = request.GET.get('page')
    timesheets = paginator.get_page(page)
    
    return render(request, 'core/timesheet_list.html', {'timesheets': timesheets})


@login_required
def approve_timesheet(request, timesheet_id):
    """View for approving a timesheet."""
    timesheet = get_object_or_404(Timesheet, pk=timesheet_id)
    
    # Check if user is the company associated with the timesheet
    if not request.user.is_company() or not hasattr(request.user, 'company_profile') or timesheet.cleaner.company != request.user.company_profile:
        messages.error(request, "You don't have permission to approve this timesheet.")
        return redirect('timesheet_list')
    
    timesheet.approved_by_company = True
    timesheet.save()
    
    # Send notification to cleaner
    send_notification(
        timesheet.cleaner.user,
        "Timesheet Approved",
        f"Your timesheet for {timesheet.date} has been approved by the company.",
        timesheet.job
    )
    
    messages.success(request, "Timesheet approved successfully!")
    return redirect('timesheet_list')


@login_required
def document_list(request):
    """View for listing documents."""
    user = request.user
    
    # Base queryset - public documents
    documents = Document.objects.filter(is_public=True)
    
    # Add user-specific documents
    if user.is_authenticated:
        if user.is_customer():
            # Customers can see their own documents and documents from their job providers
            customer_jobs = Job.objects.filter(customer__user=user)
            companies = Company.objects.filter(company_jobs__in=customer_jobs).distinct()
            documents = documents | Document.objects.filter(
                Q(uploaded_by=user) | Q(company__in=companies)
            )
        
        elif user.is_company():
            # Companies can see their documents and documents from companies they work with
            try:
                company = user.company_profile
                documents = documents | Document.objects.filter(
                    Q(uploaded_by=user) | Q(company=company)
                )
            except Company.DoesNotExist:
                pass
        
        elif user.is_cleaner():
            # Cleaners can see their documents and documents from their company
            try:
                cleaner = user.cleaner_profile
                if cleaner.company:
                    documents = documents | Document.objects.filter(
                        Q(uploaded_by=user) | Q(company=cleaner.company)
                    )
                else:
                    documents = documents | Document.objects.filter(uploaded_by=user)
            except Cleaner.DoesNotExist:
                pass
    
    # Remove duplicates and order by creation date
    documents = documents.distinct().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(documents, 10)
    page = request.GET.get('page')
    documents = paginator.get_page(page)
    
    # Document types for filtering
    document_types = Document.DocumentType.choices
    
    return render(request, 'core/document_list.html', {'documents': documents, 'document_types': document_types})


@login_required
def document_upload(request):
    """View for uploading documents."""
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            
            # Set company if user is part of one
            if request.user.is_company():
                try:
                    document.company = request.user.company_profile
                except Company.DoesNotExist:
                    messages.warning(request, "Company profile not found. Document uploaded without company association.")
            
            elif request.user.is_cleaner():
                try:
                    cleaner = request.user.cleaner_profile
                    if cleaner.company:
                        document.company = cleaner.company
                except Cleaner.DoesNotExist:
                    pass
            
            document.save()
            
            messages.success(request, "Document uploaded successfully!")
            return redirect('document_list')
    else:
        form = DocumentUploadForm()
    
    return render(request, 'core/document_upload.html', {'form': form})


@login_required
def document_detail(request, document_id):
    """View for document details."""
    document = get_object_or_404(Document, pk=document_id)
    
    # Check access permissions
    user = request.user
    if not document.is_public:
        if document.uploaded_by != user:
            # Check if user belongs to the document's company
            if document.company:
                if (user.is_company() and hasattr(user, 'company_profile') and user.company_profile == document.company) or \
                   (user.is_cleaner() and hasattr(user, 'cleaner_profile') and user.cleaner_profile.company == document.company):
                    pass  # Allow access
                else:
                    messages.error(request, "You don't have permission to view this document.")
                    return redirect('document_list')
            else:
                messages.error(request, "You don't have permission to view this document.")
                return redirect('document_list')
    
    return render(request, 'core/document_detail.html', {'document': document})


@login_required
def create_payroll(request):
    """View for creating payroll records."""
    if not request.user.is_company():
        messages.error(request, "Only companies can create payroll records.")
        return redirect('dashboard')
    
    try:
        company = request.user.company_profile
    except Company.DoesNotExist:
        messages.error(request, "Company profile not found.")
        return redirect('company_registration')
    
    # Get cleaners associated with the company
    cleaners = Cleaner.objects.filter(company=company)
    
    if request.method == 'POST':
        form = PayrollForm(request.POST)
        if form.is_valid():
            payroll = form.save(commit=False)
            payroll.company = company
            
            # Ensure cleaner belongs to this company
            cleaner = form.cleaned_data['cleaner']
            if cleaner.company != company:
                messages.error(request, "You can only create payroll records for your company's cleaners.")
                return redirect('payroll_list')
            
            # Calculate net amount based on form values
            base_salary = form.cleaned_data['base_salary']
            bonus = form.cleaned_data['bonus'] or 0
            tax_deduction = form.cleaned_data['tax_deduction'] or 0
            social_security_deduction = form.cleaned_data['social_security_deduction'] or 0
            
            payroll.net_amount = base_salary + bonus - tax_deduction - social_security_deduction
            
            payroll.save()
            
            # Send notification to cleaner
            send_notification(
                payroll.cleaner.user,
                "New Payroll Record",
                f"A new payroll record has been created for you for the period {payroll.period_start} to {payroll.period_end}.",
                None
            )
            
            messages.success(request, "Payroll record created successfully!")
            return redirect('payroll_list')
    else:
        form = PayrollForm()
        # Limit cleaner choices to company's cleaners
        form.fields['cleaner'].queryset = cleaners
    
    return render(request, 'core/payroll_create.html', {'form': form, 'cleaners': cleaners})


@login_required
def payroll_list(request):
    """View for listing payroll records."""
    user = request.user
    
    if user.is_company():
        try:
            company = user.company_profile
            payrolls = Payroll.objects.filter(company=company).order_by('-period_end')
        except Company.DoesNotExist:
            messages.error(request, "Company profile not found.")
            return redirect('company_registration')
    
    elif user.is_cleaner():
        try:
            cleaner = user.cleaner_profile
            payrolls = Payroll.objects.filter(cleaner=cleaner).order_by('-period_end')
        except Cleaner.DoesNotExist:
            messages.error(request, "Cleaner profile not found.")
            return redirect('cleaner_registration')
    
    else:
        messages.error(request, "Only companies and cleaners can view payroll records.")
        return redirect('dashboard')
    
    # Pagination
    paginator = Paginator(payrolls, 10)
    page = request.GET.get('page')
    payrolls = paginator.get_page(page)
    
    return render(request, 'core/payroll_list.html', {'payrolls': payrolls})


@login_required
def payroll_detail(request, payroll_id):
    """View for payroll details."""
    payroll = get_object_or_404(Payroll, pk=payroll_id)
    
    # Check access permissions
    user = request.user
    if user.is_company() and hasattr(user, 'company_profile') and user.company_profile == payroll.company:
        pass  # Company can view its payrolls
    elif user.is_cleaner() and hasattr(user, 'cleaner_profile') and user.cleaner_profile == payroll.cleaner:
        pass  # Cleaner can view their payrolls
    else:
        messages.error(request, "You don't have permission to view this payroll record.")
        return redirect('dashboard')
    
    # Get related timesheets
    timesheets = Timesheet.objects.filter(
        cleaner=payroll.cleaner,
        date__range=(payroll.period_start, payroll.period_end),
        approved_by_company=True
    ).order_by('date')
    
    # Calculate total hours
    total_hours = sum(timesheet.working_hours() for timesheet in timesheets)
    
    return render(request, 'core/payroll_detail.html', {
        'payroll': payroll,
        'timesheets': timesheets,
        'total_hours': total_hours
    })


@login_required
def profile_view(request):
    """View for viewing and updating user profile."""
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)
    
    # Get role-specific data
    role_data = None
    if user.is_customer() and hasattr(user, 'customer_profile'):
        role_data = user.customer_profile
    elif user.is_company() and hasattr(user, 'company_profile'):
        role_data = user.company_profile
    elif user.is_cleaner() and hasattr(user, 'cleaner_profile'):
        role_data = user.cleaner_profile
    
    return render(request, 'core/profile.html', {'form': form, 'role_data': role_data})


@login_required
def rate_job(request, job_id):
    """View for rating a completed job."""
    job = get_object_or_404(Job, pk=job_id, status=Job.Status.COMPLETED)
    
    # Check if user is either the customer or the cleaner for this job
    user = request.user
    if (user.is_customer() and job.customer.user == user) or (user.is_cleaner() and job.cleaner and job.cleaner.user == user):
        pass  # User can rate
    else:
        messages.error(request, "You don't have permission to rate this job.")
        return redirect('job_detail', pk=job.pk)
    
    # Determine who to rate
    if user.is_customer():
        # Customer rating the cleaner
        rated_user = job.cleaner.user if job.cleaner else None
        if not rated_user:
            messages.error(request, "No cleaner assigned to this job.")
            return redirect('job_detail', pk=job.pk)
    else:
        # Cleaner rating the customer
        rated_user = job.customer.user
    
    # Check for existing rating
    if Rating.objects.filter(job=job, rated_by=user, rated_user=rated_user).exists():
        messages.error(request, "You have already rated this job.")
        return redirect('job_detail', pk=job.pk)
    
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.job = job
            rating.rated_by = user
            rating.rated_user = rated_user
            rating.save()
            
            messages.success(request, "Rating submitted successfully!")
            return redirect('job_detail', pk=job.pk)
    else:
        form = RatingForm()
    
    return render(request, 'core/rate_job.html', {'form': form, 'job': job, 'rated_user': rated_user})


@login_required
def mark_notification_read(request, notification_id):
    """View for marking a notification as read."""
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    # Redirect back to referring page or dashboard
    next_url = request.GET.get('next', 'dashboard')
    return redirect(next_url)


@login_required
def notifications_list(request):
    """View for listing all notifications."""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page = request.GET.get('page')
    notifications = paginator.get_page(page)
    
    return render(request, 'core/notifications.html', {'notifications': notifications})
