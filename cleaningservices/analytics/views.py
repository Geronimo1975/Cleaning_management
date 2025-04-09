from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q, F
from django.core.paginator import Paginator
import json
from datetime import datetime, timedelta
import csv
import io

from .models import DashboardSavedView, AnalyticsReport
from .forms import DashboardCustomizationForm, ReportForm
from accounts.models import User
from timetracking.models import TimeRecord, Break
from contracts.models import Contract, ContractTemplate, ContractAddendum


@login_required
def dashboard_view(request):
    """Main analytics dashboard view."""
    # Get user's default dashboard view if any
    saved_views = DashboardSavedView.objects.filter(user=request.user)
    default_view = saved_views.filter(is_default=True).first()
    
    # If no default view, create a basic configuration
    if not default_view:
        config = {
            'layout': 'grid',
            'widgets': [
                {'type': 'time_summary', 'position': 1, 'size': 'medium'},
                {'type': 'contract_status', 'position': 2, 'size': 'medium'},
                {'type': 'cleaner_performance', 'position': 3, 'size': 'large'},
                {'type': 'revenue_chart', 'position': 4, 'size': 'large'},
            ]
        }
    else:
        config = default_view.configuration
    
    # Get date range filters
    start_date = request.GET.get('start_date', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', timezone.now().strftime('%Y-%m-%d'))
    
    # Get other filter parameters
    filter_company = request.GET.get('company')
    filter_cleaner = request.GET.get('cleaner')
    
    context = {
        'config': config,
        'saved_views': saved_views,
        'start_date': start_date,
        'end_date': end_date,
        'filter_company': filter_company,
        'filter_cleaner': filter_cleaner,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
def customize_dashboard_view(request):
    """View for customizing dashboard layout and widgets."""
    # Get user's default view or create one
    default_view = DashboardSavedView.objects.filter(user=request.user, is_default=True).first()
    
    if request.method == 'POST':
        form = DashboardCustomizationForm(request.POST)
        if form.is_valid():
            config = form.cleaned_data['configuration']
            
            if default_view:
                default_view.configuration = config
                default_view.save()
            else:
                DashboardSavedView.objects.create(
                    user=request.user,
                    name="Default View",
                    configuration=config,
                    is_default=True
                )
            
            messages.success(request, "Dashboard layout saved successfully.")
            return redirect('analytics:dashboard')
    else:
        # Pre-fill form with existing config if available
        initial_data = {}
        if default_view:
            initial_data['configuration'] = default_view.configuration
        
        form = DashboardCustomizationForm(initial=initial_data)
    
    context = {
        'form': form,
        'available_widgets': [
            {'id': 'time_summary', 'name': 'Time Tracking Summary'},
            {'id': 'contract_status', 'name': 'Contract Status'},
            {'id': 'cleaner_performance', 'name': 'Cleaner Performance'},
            {'id': 'revenue_chart', 'name': 'Revenue Chart'},
            {'id': 'customer_satisfaction', 'name': 'Customer Satisfaction'},
            {'id': 'job_statistics', 'name': 'Job Statistics'},
        ]
    }
    
    return render(request, 'analytics/customize_dashboard.html', context)


@login_required
def save_dashboard_view(request):
    """Save current dashboard view with a name."""
    if request.method == 'POST':
        name = request.POST.get('view_name')
        config = json.loads(request.POST.get('configuration', '{}'))
        is_default = request.POST.get('is_default') == 'true'
        
        if is_default:
            # Clear other default views
            DashboardSavedView.objects.filter(user=request.user, is_default=True).update(is_default=False)
        
        DashboardSavedView.objects.create(
            user=request.user,
            name=name,
            configuration=config,
            is_default=is_default
        )
        
        messages.success(request, f"Dashboard view '{name}' saved successfully.")
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def load_dashboard_view(request, view_id):
    """Load a saved dashboard view."""
    view = get_object_or_404(DashboardSavedView, id=view_id, user=request.user)
    
    if request.GET.get('set_default') == 'true':
        # Clear other default views
        DashboardSavedView.objects.filter(user=request.user, is_default=True).update(is_default=False)
        # Set this view as default
        view.is_default = True
        view.save()
        messages.success(request, f"'{view.name}' set as your default dashboard view.")
    
    return redirect('analytics:dashboard')


@login_required
def delete_dashboard_view(request, view_id):
    """Delete a saved dashboard view."""
    view = get_object_or_404(DashboardSavedView, id=view_id, user=request.user)
    name = view.name
    
    if view.is_default:
        messages.error(request, "Cannot delete your default dashboard view. Please set another view as default first.")
        return redirect('analytics:dashboard')
    
    view.delete()
    messages.success(request, f"Dashboard view '{name}' deleted successfully.")
    return redirect('analytics:dashboard')


@login_required
def chart_data_view(request, chart_type):
    """API endpoint for chart data."""
    # Get date range filters
    start_date = request.GET.get('start_date', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', timezone.now().strftime('%Y-%m-%d'))
    
    # Parse dates
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'})
    
    # Get other filter parameters
    filter_company = request.GET.get('company')
    filter_cleaner = request.GET.get('cleaner')
    
    # Prepare filter conditions
    time_filters = Q(date__gte=start_date, date__lte=end_date)
    if filter_company:
        time_filters &= Q(cleaner__company__id=filter_company)
    if filter_cleaner:
        time_filters &= Q(cleaner__id=filter_cleaner)
    
    data = {}
    
    if chart_type == 'hours_worked':
        # Time records per day
        time_records = TimeRecord.objects.filter(time_filters)
        
        # Group by date and calculate total hours
        by_date = {}
        for record in time_records:
            date_str = record.date.strftime('%Y-%m-%d')
            duration_hours = record.duration_minutes / 60.0
            by_date[date_str] = by_date.get(date_str, 0) + duration_hours
        
        # Create sorted list of date keys
        date_keys = sorted(by_date.keys())
        
        data = {
            'labels': date_keys,
            'datasets': [
                {
                    'label': 'Hours Worked',
                    'data': [by_date[date] for date in date_keys],
                    'borderColor': '#0052CC',
                    'backgroundColor': 'rgba(0, 82, 204, 0.1)',
                    'fill': True,
                }
            ]
        }
    
    elif chart_type == 'contract_status':
        # Contracts by status
        contract_counts = Contract.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).values('status').annotate(count=Count('id'))
        
        status_map = dict(Contract.STATUS_CHOICES)
        
        labels = [status_map.get(item['status'], item['status']) for item in contract_counts]
        counts = [item['count'] for item in contract_counts]
        
        # Generate colors
        colors = ['#0052CC', '#00875A', '#FF5630', '#6554C0', '#FFAB00', '#36B37E']
        
        data = {
            'labels': labels,
            'datasets': [
                {
                    'data': counts,
                    'backgroundColor': colors[:len(counts)],
                }
            ]
        }
    
    # Add more chart types as needed
    
    return JsonResponse(data)


@login_required
def summary_data_view(request):
    """API endpoint for dashboard summary data."""
    # Get date range filters
    start_date = request.GET.get('start_date', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', timezone.now().strftime('%Y-%m-%d'))
    
    # Parse dates
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'})
    
    # Get summary data
    total_time_records = TimeRecord.objects.filter(date__gte=start_date, date__lte=end_date).count()
    total_hours = TimeRecord.objects.filter(date__gte=start_date, date__lte=end_date).aggregate(
        total=Sum('duration_minutes')
    )['total'] or 0
    total_hours = round(total_hours / 60.0, 1)  # Convert minutes to hours
    
    total_contracts = Contract.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date).count()
    active_contracts = Contract.objects.filter(
        status__in=['ACTIVE', 'PENDING'],
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).count()
    
    data = {
        'time_tracking': {
            'total_records': total_time_records,
            'total_hours': total_hours,
        },
        'contracts': {
            'total': total_contracts,
            'active': active_contracts,
        }
    }
    
    return JsonResponse(data)


# Reports views
@login_required
def reports_list_view(request):
    """View for listing saved reports."""
    reports = AnalyticsReport.objects.filter(user=request.user).order_by('-created_at')
    
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'analytics/reports_list.html', context)


@login_required
def create_report_view(request):
    """View for creating a new report."""
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            
            # Generate report data based on parameters
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            report_type = form.cleaned_data['report_type']
            
            # Generate report data
            report_data = generate_report_data(
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                company=form.cleaned_data.get('company'),
                cleaner=form.cleaned_data.get('cleaner')
            )
            
            report.data = report_data
            report.save()
            
            messages.success(request, f"Report '{report.title}' created successfully.")
            return redirect('analytics:report_detail', report_id=report.id)
    else:
        form = ReportForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'analytics/report_form.html', context)


def generate_report_data(report_type, start_date, end_date, company=None, cleaner=None):
    """Generate report data based on parameters."""
    data = {}
    
    # Apply filters
    filters = Q(date__gte=start_date, date__lte=end_date)
    if company:
        filters &= Q(cleaner__company=company)
    if cleaner:
        filters &= Q(cleaner=cleaner)
    
    if report_type == 'time_tracking':
        # Time tracking report
        time_records = TimeRecord.objects.filter(filters)
        
        # Group by date
        by_date = {}
        for record in time_records:
            date_str = record.date.strftime('%Y-%m-%d')
            duration_hours = record.duration_minutes / 60.0
            
            if date_str not in by_date:
                by_date[date_str] = {
                    'hours': 0,
                    'breaks': 0,
                    'records': 0
                }
            
            by_date[date_str]['hours'] += duration_hours
            by_date[date_str]['records'] += 1
            by_date[date_str]['breaks'] += Break.objects.filter(time_record=record).count()
        
        data = {
            'daily_summary': by_date,
            'total_hours': sum(item['hours'] for item in by_date.values()),
            'total_records': sum(item['records'] for item in by_date.values()),
            'total_breaks': sum(item['breaks'] for item in by_date.values()),
        }
    
    elif report_type == 'contract':
        # Contract report
        contract_filters = Q(created_at__date__gte=start_date, created_at__date__lte=end_date)
        
        if company:
            contract_filters &= Q(company=company)
        if cleaner:
            contract_filters &= Q(cleaner=cleaner)
        
        contracts = Contract.objects.filter(contract_filters)
        
        # Count by status
        by_status = {}
        for contract in contracts:
            status = contract.get_status_display()
            by_status[status] = by_status.get(status, 0) + 1
        
        data = {
            'status_summary': by_status,
            'total_contracts': contracts.count(),
            'by_template': dict(Contract.objects.filter(contract_filters).values('template__name').annotate(count=Count('id')).values_list('template__name', 'count')),
        }
    
    # Add more report types as needed
    
    return data


@login_required
def report_detail_view(request, report_id):
    """View a specific report."""
    report = get_object_or_404(AnalyticsReport, id=report_id, user=request.user)
    
    context = {
        'report': report,
    }
    
    return render(request, 'analytics/report_detail.html', context)


@login_required
def edit_report_view(request, report_id):
    """Edit an existing report."""
    report = get_object_or_404(AnalyticsReport, id=report_id, user=request.user)
    
    if request.method == 'POST':
        form = ReportForm(request.POST, instance=report)
        if form.is_valid():
            updated_report = form.save(commit=False)
            
            # Regenerate report data
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            report_type = form.cleaned_data['report_type']
            
            report_data = generate_report_data(
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                company=form.cleaned_data.get('company'),
                cleaner=form.cleaned_data.get('cleaner')
            )
            
            updated_report.data = report_data
            updated_report.save()
            
            messages.success(request, f"Report '{updated_report.title}' updated successfully.")
            return redirect('analytics:report_detail', report_id=report.id)
    else:
        form = ReportForm(instance=report)
    
    context = {
        'form': form,
        'report': report,
    }
    
    return render(request, 'analytics/report_form.html', context)


@login_required
def delete_report_view(request, report_id):
    """Delete an existing report."""
    report = get_object_or_404(AnalyticsReport, id=report_id, user=request.user)
    
    if request.method == 'POST':
        title = report.title
        report.delete()
        messages.success(request, f"Report '{title}' deleted successfully.")
        return redirect('analytics:reports_list')
    
    context = {
        'report': report,
    }
    
    return render(request, 'analytics/report_confirm_delete.html', context)


@login_required
def generate_report_pdf_view(request, report_id):
    """Generate PDF for a report."""
    report = get_object_or_404(AnalyticsReport, id=report_id, user=request.user)
    
    # In a real implementation, this would generate a PDF file
    # and save it to report.pdf_report field
    
    messages.success(request, f"PDF report for '{report.title}' generated successfully.")
    return redirect('analytics:report_detail', report_id=report.id)


@login_required
def schedule_report_view(request, report_id):
    """Schedule a report for periodic generation."""
    report = get_object_or_404(AnalyticsReport, id=report_id, user=request.user)
    
    if request.method == 'POST':
        frequency = request.POST.get('frequency')
        if frequency:
            report.is_scheduled = True
            report.schedule_frequency = frequency
            report.next_run = calculate_next_run(frequency)
            report.save()
            
            messages.success(request, f"Report '{report.title}' scheduled for {frequency} generation.")
        else:
            messages.error(request, "Please select a frequency.")
        
        return redirect('analytics:report_detail', report_id=report.id)
    
    context = {
        'report': report,
        'frequency_choices': AnalyticsReport.FREQUENCY_CHOICES,
    }
    
    return render(request, 'analytics/schedule_report.html', context)


def calculate_next_run(frequency):
    """Calculate the next run date based on frequency."""
    now = timezone.now()
    
    if frequency == 'DAILY':
        return now + timedelta(days=1)
    elif frequency == 'WEEKLY':
        return now + timedelta(weeks=1)
    elif frequency == 'MONTHLY':
        # Approximate month as 30 days
        return now + timedelta(days=30)
    elif frequency == 'QUARTERLY':
        # Approximate quarter as 90 days
        return now + timedelta(days=90)
    
    return now


# Widget views for partial loading
@login_required
def cleaner_performance_widget_view(request):
    """Widget for cleaner performance metrics."""
    # Get date range filters
    start_date = request.GET.get('start_date', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', timezone.now().strftime('%Y-%m-%d'))
    
    # Parse dates
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'})
    
    # Get cleaner performance data
    cleaner_data = []
    
    # In a real implementation, this would fetch actual cleaner performance metrics
    
    context = {
        'cleaner_data': cleaner_data,
    }
    
    return render(request, 'analytics/widgets/cleaner_performance.html', context)


@login_required
def company_revenue_widget_view(request):
    """Widget for company revenue data."""
    # This is a placeholder for a real revenue calculation
    
    context = {
        'revenue_data': [],
    }
    
    return render(request, 'analytics/widgets/company_revenue.html', context)


@login_required
def job_statistics_widget_view(request):
    """Widget for job statistics."""
    # This is a placeholder for job statistics
    
    context = {
        'job_data': [],
    }
    
    return render(request, 'analytics/widgets/job_statistics.html', context)


@login_required
def contract_status_widget_view(request):
    """Widget for contract status breakdown."""
    # Get date range filters
    start_date = request.GET.get('start_date', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', timezone.now().strftime('%Y-%m-%d'))
    
    # Parse dates
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'})
    
    # Get contract status counts
    status_counts = Contract.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).values('status').annotate(count=Count('id'))
    
    status_map = dict(Contract.STATUS_CHOICES)
    status_data = [
        {'label': status_map.get(item['status'], item['status']), 'count': item['count']}
        for item in status_counts
    ]
    
    context = {
        'status_data': status_data,
    }
    
    return render(request, 'analytics/widgets/contract_status.html', context)


@login_required
def customer_satisfaction_widget_view(request):
    """Widget for customer satisfaction metrics."""
    # This is a placeholder for customer satisfaction data
    
    context = {
        'satisfaction_data': [],
    }
    
    return render(request, 'analytics/widgets/customer_satisfaction.html', context)


@login_required
def time_tracking_widget_view(request):
    """Widget for time tracking summary."""
    # Get date range filters
    start_date = request.GET.get('start_date', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', timezone.now().strftime('%Y-%m-%d'))
    
    # Parse dates
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'})
    
    # Get time tracking data
    total_hours = TimeRecord.objects.filter(
        date__gte=start_date, 
        date__lte=end_date
    ).aggregate(
        total=Sum('duration_minutes')
    )['total'] or 0
    
    total_hours = round(total_hours / 60.0, 1)  # Convert minutes to hours
    
    context = {
        'total_hours': total_hours,
        'average_daily_hours': round(total_hours / max(1, (end_date - start_date).days), 1),
    }
    
    return render(request, 'analytics/widgets/time_tracking.html', context)