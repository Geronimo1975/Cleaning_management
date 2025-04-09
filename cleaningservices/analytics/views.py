from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q, F
from django.core.paginator import Paginator
import json
import datetime
import random  # Just for demo data, will be replaced with real data

from .models import DashboardSavedView, AnalyticsReport
from .forms import ReportFilterForm, AnalyticsReportForm, DashboardSavedViewForm
from accounts.models import User, CleanerProfile, CompanyProfile, Rating
from contracts.models import Contract, ContractTemplate
from timetracking.models import TimeRecord, Break


@login_required
def dashboard_view(request):
    """Main analytics dashboard view."""
    # Get user's default dashboard view or create a new one
    user = request.user
    default_view = DashboardSavedView.objects.filter(user=user, is_default=True).first()
    
    # Get all saved views for this user
    saved_views = DashboardSavedView.objects.filter(user=user).order_by('name')
    
    # Prepare filter form
    filter_form = ReportFilterForm(request.GET or None)
    
    # Process filter form
    filter_data = {}
    if filter_form.is_valid():
        filter_data = filter_form.cleaned_data
    
    # Initial dashboard configuration
    default_config = {
        'layout': 'grid',  # or 'list'
        'widgets': [
            {'id': 'summary', 'width': 12, 'height': 1, 'position': 0},
            {'id': 'contract_status', 'width': 6, 'height': 2, 'position': 1},
            {'id': 'revenue', 'width': 6, 'height': 2, 'position': 2},
            {'id': 'cleaner_performance', 'width': 6, 'height': 2, 'position': 3},
            {'id': 'time_tracking', 'width': 6, 'height': 2, 'position': 4},
        ]
    }
    
    # User's configuration or default
    dashboard_config = default_config
    if default_view:
        dashboard_config = default_view.configuration
    
    # Prepare context
    context = {
        'title': 'Analytics Dashboard',
        'section': 'analytics',
        'filter_form': filter_form,
        'saved_views': saved_views,
        'current_view': default_view,
        'dashboard_config': json.dumps(dashboard_config),
        'filter_data': json.dumps(filter_data),
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
def customize_dashboard_view(request):
    """View for customizing the dashboard layout."""
    user = request.user
    saved_views = DashboardSavedView.objects.filter(user=user).order_by('name')
    
    # Get current view
    view_id = request.GET.get('view_id')
    current_view = None
    
    if view_id:
        current_view = get_object_or_404(DashboardSavedView, id=view_id, user=user)
    else:
        # Get default view
        current_view = DashboardSavedView.objects.filter(user=user, is_default=True).first()
    
    # Available widgets
    available_widgets = [
        {'id': 'summary', 'name': 'Summary Cards', 'description': 'Key metrics at a glance'},
        {'id': 'contract_status', 'name': 'Contract Status', 'description': 'Overview of contract statuses'},
        {'id': 'revenue', 'name': 'Revenue Analysis', 'description': 'Revenue trends and breakdown'},
        {'id': 'cleaner_performance', 'name': 'Cleaner Performance', 'description': 'Performance metrics for cleaners'},
        {'id': 'customer_satisfaction', 'name': 'Customer Satisfaction', 'description': 'Customer ratings and feedback'},
        {'id': 'time_tracking', 'name': 'Time Tracking', 'description': 'Working hours and attendance'},
        {'id': 'job_statistics', 'name': 'Job Statistics', 'description': 'Job completion and efficiency metrics'},
    ]
    
    # Initial config for new dashboard
    default_config = {
        'layout': 'grid',
        'widgets': [
            {'id': 'summary', 'width': 12, 'height': 1, 'position': 0},
            {'id': 'contract_status', 'width': 6, 'height': 2, 'position': 1},
            {'id': 'revenue', 'width': 6, 'height': 2, 'position': 2},
        ]
    }
    
    # Current configuration
    current_config = default_config
    if current_view:
        current_config = current_view.configuration
    
    # Form for saving view
    form = DashboardSavedViewForm(instance=current_view)
    
    context = {
        'title': 'Customize Dashboard',
        'section': 'analytics',
        'form': form,
        'saved_views': saved_views,
        'current_view': current_view,
        'available_widgets': available_widgets,
        'current_config': json.dumps(current_config),
    }
    
    return render(request, 'analytics/customize_dashboard.html', context)


@login_required
def save_dashboard_view(request):
    """AJAX endpoint to save a dashboard view configuration."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'})
    
    try:
        data = json.loads(request.body)
        view_id = data.get('view_id')
        name = data.get('name')
        configuration = data.get('configuration')
        is_default = data.get('is_default', False)
        
        if not name or not configuration:
            return JsonResponse({'status': 'error', 'message': 'Name and configuration are required'})
        
        user = request.user
        
        # If setting as default, remove default from others
        if is_default:
            DashboardSavedView.objects.filter(user=user, is_default=True).update(is_default=False)
        
        # Update existing or create new
        if view_id:
            view = get_object_or_404(DashboardSavedView, id=view_id, user=user)
            view.name = name
            view.configuration = configuration
            view.is_default = is_default
            view.save()
            message = 'Dashboard view updated successfully'
        else:
            view = DashboardSavedView.objects.create(
                user=user,
                name=name,
                configuration=configuration,
                is_default=is_default
            )
            message = 'Dashboard view saved successfully'
        
        return JsonResponse({
            'status': 'success', 
            'message': message,
            'view_id': view.id,
            'name': view.name,
            'is_default': view.is_default
        })
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def load_dashboard_view(request, view_id):
    """Load a saved dashboard view."""
    view = get_object_or_404(DashboardSavedView, id=view_id, user=request.user)
    return redirect('analytics:dashboard')


@login_required
def delete_dashboard_view(request, view_id):
    """Delete a saved dashboard view."""
    view = get_object_or_404(DashboardSavedView, id=view_id, user=request.user)
    
    # Don't delete the last view
    if DashboardSavedView.objects.filter(user=request.user).count() <= 1:
        messages.error(request, "Cannot delete the only dashboard view")
        return redirect('analytics:customize_dashboard')
    
    # If deleting default view, set another as default
    if view.is_default:
        other_view = DashboardSavedView.objects.filter(user=request.user).exclude(id=view_id).first()
        if other_view:
            other_view.is_default = True
            other_view.save()
    
    view.delete()
    messages.success(request, "Dashboard view deleted successfully")
    return redirect('analytics:customize_dashboard')


@login_required
def chart_data_view(request, chart_type):
    """API endpoint that returns data for different chart types."""
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    company_id = request.GET.get('company')
    cleaner_id = request.GET.get('cleaner')
    
    # Convert string dates to date objects
    try:
        if start_date:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'})
    
    # Define chart data based on chart_type
    if chart_type == 'contract_status':
        data = get_contract_status_data(request.user, start_date, end_date, company_id, cleaner_id)
    elif chart_type == 'revenue':
        data = get_revenue_data(request.user, start_date, end_date, company_id, cleaner_id)
    elif chart_type == 'cleaner_performance':
        data = get_cleaner_performance_data(request.user, start_date, end_date, company_id, cleaner_id)
    elif chart_type == 'customer_satisfaction':
        data = get_customer_satisfaction_data(request.user, start_date, end_date, company_id, cleaner_id)
    elif chart_type == 'time_tracking':
        data = get_time_tracking_data(request.user, start_date, end_date, company_id, cleaner_id)
    elif chart_type == 'job_statistics':
        data = get_job_statistics_data(request.user, start_date, end_date, company_id, cleaner_id)
    else:
        data = {'error': 'Invalid chart type'}
    
    return JsonResponse(data)


@login_required
def summary_data_view(request):
    """API endpoint for summary dashboard cards."""
    user = request.user
    
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    company_id = request.GET.get('company')
    cleaner_id = request.GET.get('cleaner')
    
    # Convert string dates to date objects
    try:
        if start_date:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'})
    
    # Generate summary data based on user role
    if user.role == User.Role.ADMIN:
        # Admin sees global data
        data = get_admin_summary_data(start_date, end_date, company_id, cleaner_id)
    elif user.role == User.Role.COMPANY:
        # Company sees their own data
        data = get_company_summary_data(user, start_date, end_date, cleaner_id)
    elif user.role == User.Role.CLEANER:
        # Cleaner sees their own performance
        data = get_cleaner_summary_data(user, start_date, end_date)
    else:
        # Customer sees basic info
        data = get_customer_summary_data(user, start_date, end_date)
    
    return JsonResponse(data)


# Reports views
@login_required
def reports_list_view(request):
    """View for listing all reports."""
    user = request.user
    
    # Get reports for this user
    reports = AnalyticsReport.objects.filter(user=user)
    
    # Apply filters
    report_type = request.GET.get('report_type')
    if report_type:
        reports = reports.filter(report_type=report_type)
    
    period = request.GET.get('period')
    if period:
        reports = reports.filter(period=period)
    
    # Pagination
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Analytics Reports',
        'section': 'analytics',
        'page_obj': page_obj,
        'report_types': AnalyticsReport.REPORT_TYPES,
        'period_choices': AnalyticsReport.PERIOD_CHOICES,
    }
    
    return render(request, 'analytics/reports_list.html', context)


@login_required
def create_report_view(request):
    """View for creating a new analytics report."""
    if request.method == 'POST':
        form = AnalyticsReportForm(request.POST, user=request.user)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.save()
            
            messages.success(request, "Report created successfully")
            return redirect('analytics:report_detail', report_id=report.id)
    else:
        form = AnalyticsReportForm(user=request.user)
    
    context = {
        'title': 'Create Analytics Report',
        'section': 'analytics',
        'form': form,
    }
    
    return render(request, 'analytics/report_form.html', context)


@login_required
def report_detail_view(request, report_id):
    """View for viewing a report's details and generated data."""
    report = get_object_or_404(AnalyticsReport, id=report_id, user=request.user)
    
    context = {
        'title': f'Report: {report.title}',
        'section': 'analytics',
        'report': report,
        'report_data': json.dumps(report.data),
    }
    
    return render(request, 'analytics/report_detail.html', context)


@login_required
def edit_report_view(request, report_id):
    """View for editing an existing report."""
    report = get_object_or_404(AnalyticsReport, id=report_id, user=request.user)
    
    if request.method == 'POST':
        form = AnalyticsReportForm(request.POST, instance=report, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Report updated successfully")
            return redirect('analytics:report_detail', report_id=report.id)
    else:
        form = AnalyticsReportForm(instance=report, user=request.user)
    
    context = {
        'title': f'Edit Report: {report.title}',
        'section': 'analytics',
        'form': form,
        'report': report,
    }
    
    return render(request, 'analytics/report_form.html', context)


@login_required
def delete_report_view(request, report_id):
    """View for deleting a report."""
    report = get_object_or_404(AnalyticsReport, id=report_id, user=request.user)
    
    if request.method == 'POST':
        report.delete()
        messages.success(request, "Report deleted successfully")
        return redirect('analytics:reports_list')
    
    context = {
        'title': f'Delete Report: {report.title}',
        'section': 'analytics',
        'report': report,
    }
    
    return render(request, 'analytics/report_delete.html', context)


@login_required
def generate_report_pdf_view(request, report_id):
    """Generate a PDF version of the report."""
    report = get_object_or_404(AnalyticsReport, id=report_id, user=request.user)
    
    # TODO: Implement actual PDF generation
    # For now, we'll just return a message
    messages.info(request, "PDF generation is not implemented yet")
    return redirect('analytics:report_detail', report_id=report.id)


@login_required
def schedule_report_view(request, report_id):
    """Schedule a report for automatic generation."""
    report = get_object_or_404(AnalyticsReport, id=report_id, user=request.user)
    
    if request.method == 'POST':
        # Toggle scheduled status
        report.is_scheduled = not report.is_scheduled
        
        if report.is_scheduled:
            # Set frequency if it's being enabled
            frequency = request.POST.get('schedule_frequency')
            if frequency:
                report.schedule_frequency = frequency
                
            # Calculate next run time
            now = timezone.now()
            if report.schedule_frequency == 'daily':
                next_run = now + datetime.timedelta(days=1)
            elif report.schedule_frequency == 'weekly':
                next_run = now + datetime.timedelta(days=7)
            elif report.schedule_frequency == 'monthly':
                # Add roughly one month
                next_run = now + datetime.timedelta(days=30)
            elif report.schedule_frequency == 'quarterly':
                # Add roughly one quarter
                next_run = now + datetime.timedelta(days=90)
            else:
                next_run = now + datetime.timedelta(days=1)
                
            report.next_run = next_run
        
        report.save()
        
        status = "enabled" if report.is_scheduled else "disabled"
        messages.success(request, f"Report scheduling {status} successfully")
        
    return redirect('analytics:report_detail', report_id=report.id)


# Widget views for partial loading
@login_required
def cleaner_performance_widget_view(request):
    """Partial view for cleaner performance widget."""
    context = {
        'widget_id': 'cleaner_performance',
    }
    return render(request, 'analytics/widgets/cleaner_performance.html', context)


@login_required
def company_revenue_widget_view(request):
    """Partial view for company revenue widget."""
    context = {
        'widget_id': 'revenue',
    }
    return render(request, 'analytics/widgets/company_revenue.html', context)


@login_required
def job_statistics_widget_view(request):
    """Partial view for job statistics widget."""
    context = {
        'widget_id': 'job_statistics',
    }
    return render(request, 'analytics/widgets/job_statistics.html', context)


@login_required
def contract_status_widget_view(request):
    """Partial view for contract status widget."""
    context = {
        'widget_id': 'contract_status',
    }
    return render(request, 'analytics/widgets/contract_status.html', context)


@login_required
def customer_satisfaction_widget_view(request):
    """Partial view for customer satisfaction widget."""
    context = {
        'widget_id': 'customer_satisfaction',
    }
    return render(request, 'analytics/widgets/customer_satisfaction.html', context)


@login_required
def time_tracking_widget_view(request):
    """Partial view for time tracking widget."""
    context = {
        'widget_id': 'time_tracking',
    }
    return render(request, 'analytics/widgets/time_tracking.html', context)


# Helper functions for chart data
def get_contract_status_data(user, start_date=None, end_date=None, company_id=None, cleaner_id=None):
    """Get data for contract status chart."""
    # Apply filters based on user role
    contracts_query = Contract.objects.all()
    
    if user.role == User.Role.COMPANY:
        try:
            company = CompanyProfile.objects.get(user=user)
            contracts_query = contracts_query.filter(company=company)
        except CompanyProfile.DoesNotExist:
            return {'error': 'Company profile not found'}
    
    elif user.role == User.Role.CLEANER:
        try:
            cleaner = CleanerProfile.objects.get(user=user)
            contracts_query = contracts_query.filter(cleaner=cleaner)
        except CleanerProfile.DoesNotExist:
            return {'error': 'Cleaner profile not found'}
    
    # Apply date filters
    if start_date:
        contracts_query = contracts_query.filter(Q(start_date__gte=start_date) | Q(created_at__date__gte=start_date))
    if end_date:
        contracts_query = contracts_query.filter(Q(end_date__lte=end_date) | Q(created_at__date__lte=end_date))
    
    # Apply additional filters
    if company_id:
        contracts_query = contracts_query.filter(company_id=company_id)
    if cleaner_id:
        contracts_query = contracts_query.filter(cleaner_id=cleaner_id)
    
    # Get contract counts by status
    status_counts = contracts_query.values('status').annotate(count=Count('id'))
    
    # Prepare data for chart
    labels = []
    data = []
    colors = []
    
    status_map = {
        'draft': {'label': 'Draft', 'color': '#6c757d'},  # gray
        'pending_cleaner': {'label': 'Pending Cleaner', 'color': '#ffc107'},  # yellow
        'pending_company': {'label': 'Pending Company', 'color': '#fd7e14'},  # orange
        'active': {'label': 'Active', 'color': '#28a745'},  # green
        'expired': {'label': 'Expired', 'color': '#dc3545'},  # red
        'terminated': {'label': 'Terminated', 'color': '#6f42c1'},  # purple
    }
    
    for status in status_counts:
        status_key = status['status']
        count = status['count']
        
        if status_key in status_map:
            labels.append(status_map[status_key]['label'])
            data.append(count)
            colors.append(status_map[status_key]['color'])
    
    return {
        'chart_type': 'pie',
        'labels': labels,
        'datasets': [{
            'data': data,
            'backgroundColor': colors,
        }],
        'title': 'Contract Status Distribution'
    }


def get_revenue_data(user, start_date=None, end_date=None, company_id=None, cleaner_id=None):
    """Get data for revenue charts."""
    # TODO: Implement real revenue calculations based on contracts and timetracking
    # For now, return dummy data
    
    # Months for the chart
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Generate some reasonable looking data
    current_month = datetime.datetime.now().month
    revenue_data = []
    trend_data = []
    
    for i in range(12):
        # More revenue in recent months with some randomness
        factor = 1.0 + (i / 12)
        if i >= current_month - 1:
            factor = 0.8  # Future months have less data
            
        base = 5000 * factor
        revenue = round(base + random.uniform(-base*0.2, base*0.2))
        revenue_data.append(revenue)
        
        # Trend is smoother
        trend = round(base)
        trend_data.append(trend)
    
    return {
        'chart_type': 'line',
        'labels': months,
        'datasets': [
            {
                'label': 'Revenue',
                'data': revenue_data,
                'borderColor': '#0052CC',
                'backgroundColor': 'rgba(0, 82, 204, 0.1)',
                'fill': True,
            },
            {
                'label': 'Trend',
                'data': trend_data,
                'borderColor': '#00875A',
                'borderDash': [5, 5],
                'fill': False,
            }
        ],
        'title': 'Monthly Revenue'
    }


def get_cleaner_performance_data(user, start_date=None, end_date=None, company_id=None, cleaner_id=None):
    """Get data for cleaner performance charts."""
    # For now, return dummy data
    # In a real implementation, this would calculate metrics like:
    # - Jobs completed
    # - Average rating
    # - On-time percentage
    # - Hours worked
    
    # Labels will be cleaner names
    if user.role == User.Role.COMPANY:
        try:
            company = CompanyProfile.objects.get(user=user)
            cleaners_query = CleanerProfile.objects.filter(company=company)
        except CompanyProfile.DoesNotExist:
            cleaners_query = CleanerProfile.objects.none()
    elif user.role == User.Role.ADMIN:
        cleaners_query = CleanerProfile.objects.all()
        if company_id:
            cleaners_query = cleaners_query.filter(company_id=company_id)
    else:
        # Cleaner sees only their data
        cleaners_query = CleanerProfile.objects.filter(user=user)
    
    if cleaner_id:
        cleaners_query = cleaners_query.filter(id=cleaner_id)
    
    # Limit to 10 cleaners to avoid overcrowding the chart
    cleaners = cleaners_query[:10]
    
    labels = []
    ratings_data = []
    jobs_data = []
    
    for cleaner in cleaners:
        labels.append(cleaner.user.get_full_name())
        
        # Get average rating (placeholder)
        avg_rating = random.uniform(3.5, 5.0)
        ratings_data.append(round(avg_rating, 1))
        
        # Get jobs completed (placeholder)
        jobs_completed = random.randint(5, 50)
        jobs_data.append(jobs_completed)
    
    return {
        'chart_type': 'bar',
        'labels': labels,
        'datasets': [
            {
                'label': 'Average Rating',
                'data': ratings_data,
                'backgroundColor': '#0052CC',
                'yAxisID': 'y',
            },
            {
                'label': 'Jobs Completed',
                'data': jobs_data,
                'backgroundColor': '#00875A',
                'yAxisID': 'y1',
            }
        ],
        'title': 'Cleaner Performance Metrics',
        'options': {
            'scales': {
                'y': {
                    'type': 'linear',
                    'position': 'left',
                    'title': {
                        'display': True,
                        'text': 'Rating (0-5)'
                    },
                    'min': 0,
                    'max': 5
                },
                'y1': {
                    'type': 'linear',
                    'position': 'right',
                    'title': {
                        'display': True,
                        'text': 'Jobs Completed'
                    },
                    'min': 0
                }
            }
        }
    }


def get_customer_satisfaction_data(user, start_date=None, end_date=None, company_id=None, cleaner_id=None):
    """Get data for customer satisfaction charts."""
    # Query ratings data
    ratings_query = Rating.objects.all()
    
    # Apply filters based on user role
    if user.role == User.Role.COMPANY:
        # Companies see ratings for their cleaners
        try:
            company = CompanyProfile.objects.get(user=user)
            company_cleaners = CleanerProfile.objects.filter(company=company).values_list('user_id', flat=True)
            ratings_query = ratings_query.filter(rated_user_id__in=company_cleaners)
        except CompanyProfile.DoesNotExist:
            return {'error': 'Company profile not found'}
    elif user.role == User.Role.CLEANER:
        # Cleaners see only their ratings
        ratings_query = ratings_query.filter(rated_user=user)
    
    # Apply date filters
    if start_date:
        ratings_query = ratings_query.filter(created_at__date__gte=start_date)
    if end_date:
        ratings_query = ratings_query.filter(created_at__date__lte=end_date)
    
    # Apply additional filters
    if company_id:
        company_cleaners = CleanerProfile.objects.filter(company_id=company_id).values_list('user_id', flat=True)
        ratings_query = ratings_query.filter(rated_user_id__in=company_cleaners)
    if cleaner_id:
        cleaner = CleanerProfile.objects.filter(id=cleaner_id).first()
        if cleaner:
            ratings_query = ratings_query.filter(rated_user=cleaner.user)
    
    # Get distribution of ratings
    rating_counts = [0, 0, 0, 0, 0]  # 1-5 star counts
    
    for rating in ratings_query:
        if 1 <= rating.rating <= 5:
            rating_counts[rating.rating - 1] += 1
    
    # For now, if we don't have enough real data, supplement with dummy data
    if sum(rating_counts) < 5:
        rating_counts = [
            random.randint(0, 3),  # 1 star
            random.randint(1, 5),  # 2 star
            random.randint(3, 8),  # 3 star
            random.randint(10, 20),  # 4 star
            random.randint(15, 30),  # 5 star
        ]
    
    return {
        'chart_type': 'bar',
        'labels': ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'],
        'datasets': [{
            'label': 'Number of Ratings',
            'data': rating_counts,
            'backgroundColor': [
                '#dc3545',  # red for 1 star
                '#fd7e14',  # orange for 2 stars
                '#ffc107',  # yellow for 3 stars
                '#20c997',  # teal for 4 stars
                '#28a745',  # green for 5 stars
            ]
        }],
        'title': 'Customer Satisfaction Ratings',
        'options': {
            'scales': {
                'y': {
                    'beginAtZero': True,
                    'title': {
                        'display': True,
                        'text': 'Number of Ratings'
                    }
                }
            }
        }
    }


def get_time_tracking_data(user, start_date=None, end_date=None, company_id=None, cleaner_id=None):
    """Get data for time tracking charts."""
    # Query time records
    time_records_query = TimeRecord.objects.all()
    
    # Apply filters based on user role
    if user.role == User.Role.COMPANY:
        # Companies see time records for their cleaners
        try:
            company = CompanyProfile.objects.get(user=user)
            company_cleaners = CleanerProfile.objects.filter(company=company).values_list('user_id', flat=True)
            time_records_query = time_records_query.filter(user_id__in=company_cleaners)
        except CompanyProfile.DoesNotExist:
            return {'error': 'Company profile not found'}
    elif user.role == User.Role.CLEANER:
        # Cleaners see only their time records
        time_records_query = time_records_query.filter(user=user)
    
    # Apply date filters
    if start_date:
        time_records_query = time_records_query.filter(date__gte=start_date)
    if end_date:
        time_records_query = time_records_query.filter(date__lte=end_date)
    
    # Apply additional filters
    if company_id:
        company_cleaners = CleanerProfile.objects.filter(company_id=company_id).values_list('user_id', flat=True)
        time_records_query = time_records_query.filter(user_id__in=company_cleaners)
    if cleaner_id:
        cleaner = CleanerProfile.objects.filter(id=cleaner_id).first()
        if cleaner:
            time_records_query = time_records_query.filter(user=cleaner.user)
    
    # Group by date and get total hours
    date_hours = {}
    
    for record in time_records_query:
        date_str = record.date.strftime('%Y-%m-%d')
        if date_str not in date_hours:
            date_hours[date_str] = 0
        
        # Calculate hours worked
        if record.clock_out:
            duration = record.clock_out - record.clock_in
            hours = duration.total_seconds() / 3600
            date_hours[date_str] += hours
    
    # For now, if we don't have enough real data, supplement with dummy data
    if len(date_hours) < 7:
        # Generate last 7 days of data
        today = datetime.date.today()
        for i in range(7):
            date = today - datetime.timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in date_hours:
                date_hours[date_str] = round(random.uniform(3, 8), 1)
    
    # Sort by date
    sorted_dates = sorted(date_hours.keys())
    labels = []
    hours_data = []
    
    for date_str in sorted_dates:
        # Format date for display
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        labels.append(date_obj.strftime('%b %d'))
        hours_data.append(date_hours[date_str])
    
    return {
        'chart_type': 'line',
        'labels': labels,
        'datasets': [{
            'label': 'Hours Worked',
            'data': hours_data,
            'borderColor': '#0052CC',
            'backgroundColor': 'rgba(0, 82, 204, 0.1)',
            'fill': True
        }],
        'title': 'Daily Hours Worked',
        'options': {
            'scales': {
                'y': {
                    'beginAtZero': True,
                    'title': {
                        'display': True,
                        'text': 'Hours'
                    }
                }
            }
        }
    }


def get_job_statistics_data(user, start_date=None, end_date=None, company_id=None, cleaner_id=None):
    """Get data for job statistics charts."""
    # TODO: Implement real job statistics
    # For now, return dummy data
    
    # Labels for job categories
    job_categories = ['Residential', 'Commercial', 'Deep Clean', 'Move-in/out', 'Window', 'Carpet']
    
    # Generate reasonable job counts for each category
    job_counts = []
    for _ in job_categories:
        job_counts.append(random.randint(5, 50))
    
    return {
        'chart_type': 'polarArea',
        'labels': job_categories,
        'datasets': [{
            'data': job_counts,
            'backgroundColor': [
                'rgba(0, 82, 204, 0.5)',  # blue
                'rgba(0, 135, 90, 0.5)',  # green
                'rgba(105, 0, 199, 0.5)',  # purple
                'rgba(212, 100, 0, 0.5)',  # orange
                'rgba(199, 0, 57, 0.5)',  # red
                'rgba(0, 157, 174, 0.5)',  # teal
            ]
        }],
        'title': 'Job Distribution by Type'
    }


# Helper functions for summary data
def get_admin_summary_data(start_date=None, end_date=None, company_id=None, cleaner_id=None):
    """Get summary data for admin dashboard."""
    # Count active users by role
    total_customers = User.objects.filter(role=User.Role.CUSTOMER, is_active=True).count()
    total_companies = User.objects.filter(role=User.Role.COMPANY, is_active=True).count()
    total_cleaners = User.objects.filter(role=User.Role.CLEANER, is_active=True).count()
    
    # Count contracts by status
    total_contracts = Contract.objects.count()
    active_contracts = Contract.objects.filter(status='active').count()
    
    # Calculate average rating
    avg_rating = Rating.objects.aggregate(avg=Avg('rating'))['avg'] or 0
    avg_rating = round(avg_rating, 1)
    
    return {
        'cards': [
            {
                'title': 'Companies',
                'value': total_companies,
                'icon': 'fa-building',
                'color': 'primary'
            },
            {
                'title': 'Cleaners',
                'value': total_cleaners,
                'icon': 'fa-user-tie',
                'color': 'success'
            },
            {
                'title': 'Customers',
                'value': total_customers,
                'icon': 'fa-users',
                'color': 'info'
            },
            {
                'title': 'Active Contracts',
                'value': active_contracts,
                'icon': 'fa-file-contract',
                'color': 'warning'
            },
            {
                'title': 'Total Contracts',
                'value': total_contracts,
                'icon': 'fa-file-signature',
                'color': 'secondary'
            },
            {
                'title': 'Avg. Rating',
                'value': avg_rating,
                'icon': 'fa-star',
                'color': 'danger'
            }
        ]
    }


def get_company_summary_data(user, start_date=None, end_date=None, cleaner_id=None):
    """Get summary data for company dashboard."""
    try:
        company = CompanyProfile.objects.get(user=user)
    except CompanyProfile.DoesNotExist:
        return {'error': 'Company profile not found'}
    
    # Count cleaners in this company
    total_cleaners = CleanerProfile.objects.filter(company=company).count()
    
    # Count contracts by status
    total_contracts = Contract.objects.filter(company=company).count()
    active_contracts = Contract.objects.filter(company=company, status='active').count()
    
    # Calculate average rating for company's cleaners
    company_cleaners = CleanerProfile.objects.filter(company=company).values_list('user_id', flat=True)
    avg_rating = Rating.objects.filter(rated_user_id__in=company_cleaners).aggregate(avg=Avg('rating'))['avg'] or 0
    avg_rating = round(avg_rating, 1)
    
    # Total working hours (placeholder)
    total_hours = random.randint(50, 500)
    
    return {
        'cards': [
            {
                'title': 'Cleaners',
                'value': total_cleaners,
                'icon': 'fa-user-tie',
                'color': 'primary'
            },
            {
                'title': 'Active Contracts',
                'value': active_contracts,
                'icon': 'fa-file-contract',
                'color': 'success'
            },
            {
                'title': 'Total Contracts',
                'value': total_contracts,
                'icon': 'fa-file-signature',
                'color': 'info'
            },
            {
                'title': 'Avg. Rating',
                'value': avg_rating,
                'icon': 'fa-star',
                'color': 'warning'
            },
            {
                'title': 'Total Hours',
                'value': total_hours,
                'icon': 'fa-clock',
                'color': 'danger'
            },
            {
                'title': 'Revenue',
                'value': f"€{random.randint(5000, 50000)}",
                'icon': 'fa-euro-sign',
                'color': 'secondary'
            }
        ]
    }


def get_cleaner_summary_data(user, start_date=None, end_date=None):
    """Get summary data for cleaner dashboard."""
    try:
        cleaner = CleanerProfile.objects.get(user=user)
    except CleanerProfile.DoesNotExist:
        return {'error': 'Cleaner profile not found'}
    
    # Get contract info
    total_contracts = Contract.objects.filter(cleaner=cleaner).count()
    active_contract = Contract.objects.filter(cleaner=cleaner, status='active').exists()
    
    # Calculate average rating
    avg_rating = Rating.objects.filter(rated_user=user).aggregate(avg=Avg('rating'))['avg'] or 0
    avg_rating = round(avg_rating, 1)
    
    # Total working hours (placeholder)
    total_hours = random.randint(20, 200)
    
    # Earnings (placeholder)
    earnings = random.randint(1000, 5000)
    
    return {
        'cards': [
            {
                'title': 'Status',
                'value': 'Active' if active_contract else 'Inactive',
                'icon': 'fa-toggle-on',
                'color': 'success' if active_contract else 'danger'
            },
            {
                'title': 'Contracts',
                'value': total_contracts,
                'icon': 'fa-file-signature',
                'color': 'primary'
            },
            {
                'title': 'Rating',
                'value': avg_rating,
                'icon': 'fa-star',
                'color': 'warning'
            },
            {
                'title': 'Hours Worked',
                'value': total_hours,
                'icon': 'fa-clock',
                'color': 'info'
            },
            {
                'title': 'Earnings',
                'value': f"€{earnings}",
                'icon': 'fa-euro-sign',
                'color': 'secondary'
            }
        ]
    }


def get_customer_summary_data(user, start_date=None, end_date=None):
    """Get summary data for customer dashboard."""
    # For customers, we show basic service stats
    
    # Placeholder service stats for customers
    total_services = random.randint(1, 20)
    upcoming_services = random.randint(0, 5)
    
    return {
        'cards': [
            {
                'title': 'Services Booked',
                'value': total_services,
                'icon': 'fa-calendar-check',
                'color': 'primary'
            },
            {
                'title': 'Upcoming',
                'value': upcoming_services,
                'icon': 'fa-calendar-alt',
                'color': 'success'
            },
            {
                'title': 'Cleaner Rating',
                'value': f"{round(random.uniform(4.0, 5.0), 1)}",
                'icon': 'fa-star',
                'color': 'warning'
            }
        ]
    }