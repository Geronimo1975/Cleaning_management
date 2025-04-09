from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q
from datetime import timedelta

from accounts.models import User, CompanyProfile, CleanerProfile
from jobs.models import TimeTracking, JobAssignment
from .models import PayPeriod, Payslip, PayslipTimeEntry, Contract, SocialSecurity, TaxClass
from .forms import (
    PayPeriodForm, PayslipForm, ContractForm, TaxClassForm, 
    SocialSecurityForm, PayScaleForm
)


def is_company(user):
    """Check if the user is a company."""
    return user.is_authenticated and user.role == User.Role.COMPANY


def is_cleaner(user):
    """Check if the user is a cleaner."""
    return user.is_authenticated and user.role == User.Role.CLEANER


@login_required
@user_passes_test(is_company)
def payroll_overview(request):
    """View for company payroll overview."""
    company_profile = CompanyProfile.objects.get(user=request.user)
    
    # Get pay periods
    pay_periods = PayPeriod.objects.filter(company=company_profile).order_by('-start_date')
    
    # Get active contracts
    active_contracts = Contract.objects.filter(
        company=company_profile,
        is_active=True
    ).select_related('cleaner__user')
    
    # Get recent payslips
    recent_payslips = Payslip.objects.filter(
        pay_period__company=company_profile
    ).order_by('-created_at')[:10]
    
    # Get recent time entries for verification
    unverified_time_entries = TimeTracking.objects.filter(
        assignment__company=company_profile,
        status='completed'
    ).order_by('-clock_in')[:20]
    
    return render(request, 'payroll/overview.html', {
        'pay_periods': pay_periods,
        'active_contracts': active_contracts,
        'recent_payslips': recent_payslips,
        'unverified_time_entries': unverified_time_entries,
    })


@login_required
@user_passes_test(is_company)
def create_pay_period(request):
    """View to create a new pay period."""
    company_profile = CompanyProfile.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = PayPeriodForm(request.POST)
        if form.is_valid():
            pay_period = form.save(commit=False)
            pay_period.company = company_profile
            pay_period.status = 'open'
            pay_period.save()
            
            messages.success(request, 'Pay period created successfully!')
            return redirect('pay_period_detail', period_id=pay_period.id)
    else:
        # Default to current month
        today = timezone.now()
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year+1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month+1, day=1) - timedelta(days=1)
        
        form = PayPeriodForm(initial={
            'start_date': start_date,
            'end_date': end_date,
        })
    
    return render(request, 'payroll/create_pay_period.html', {
        'form': form,
    })


@login_required
@user_passes_test(is_company)
def pay_period_detail(request, period_id):
    """View details of a pay period and manage payslips."""
    company_profile = CompanyProfile.objects.get(user=request.user)
    pay_period = get_object_or_404(PayPeriod, id=period_id, company=company_profile)
    
    # Get all cleaners working for this company
    cleaners = CleanerProfile.objects.filter(
        Q(company=company_profile) | 
        Q(job_assignments__company=company_profile)
    ).distinct()
    
    # Get existing payslips for this period
    payslips = Payslip.objects.filter(pay_period=pay_period)
    
    # Check which cleaners already have payslips
    cleaners_with_payslips = payslips.values_list('cleaner_id', flat=True)
    
    # Get cleaners without payslips
    cleaners_without_payslips = cleaners.exclude(id__in=cleaners_with_payslips)
    
    if request.method == 'POST':
        if 'generate_payslips' in request.POST:
            # Generate payslips for all cleaners who don't have one
            for cleaner in cleaners_without_payslips:
                # Get active contract
                contract = Contract.objects.filter(
                    cleaner=cleaner,
                    company=company_profile,
                    is_active=True
                ).first()
                
                if not contract:
                    continue
                
                # Get time entries for this period
                time_entries = TimeTracking.objects.filter(
                    cleaner=cleaner,
                    clock_in__gte=pay_period.start_date,
                    clock_in__lte=pay_period.end_date,
                    status__in=['completed', 'verified']
                )
                
                if not time_entries:
                    continue
                
                # Calculate hours
                regular_hours = 0
                overtime_hours = 0
                weekend_hours = 0
                night_hours = 0
                holiday_hours = 0
                
                for entry in time_entries:
                    if not entry.total_minutes:
                        continue
                    
                    hours = entry.total_minutes / 60
                    
                    # Check if weekend
                    if entry.clock_in.weekday() >= 5:  # 5=Saturday, 6=Sunday
                        weekend_hours += hours
                    # Check if night (10pm-6am)
                    elif entry.clock_in.hour >= 22 or entry.clock_in.hour < 6:
                        night_hours += hours
                    else:
                        # Add to regular hours (simplified - would be more complex in reality)
                        regular_hours += hours
                
                # Create new payslip
                payslip = Payslip(
                    pay_period=pay_period,
                    cleaner=cleaner,
                    contract=contract,
                    regular_hours=regular_hours,
                    overtime_hours=overtime_hours,
                    weekend_hours=weekend_hours,
                    night_hours=night_hours,
                    holiday_hours=holiday_hours,
                    hourly_rate=contract.hourly_rate or 0
                )
                
                # Save to calculate derived fields
                payslip.save()
                
                # Link time entries to payslip
                for entry in time_entries:
                    PayslipTimeEntry.objects.create(
                        payslip=payslip,
                        time_entry=entry
                    )
            
            messages.success(request, 'Payslips generated successfully!')
            return redirect('pay_period_detail', period_id=pay_period.id)
        
        elif 'close_period' in request.POST:
            # Close the pay period
            pay_period.status = 'closed'
            pay_period.save()
            
            messages.success(request, 'Pay period closed successfully!')
            return redirect('payroll_overview')
        
        elif 'mark_paid' in request.POST:
            # Mark all payslips as paid
            payment_date = timezone.now().date()
            payment_reference = f"Payroll-{pay_period.id}-{payment_date}"
            
            payslips.update(
                is_paid=True,
                payment_date=payment_date,
                payment_reference=payment_reference
            )
            
            # Update pay period
            pay_period.status = 'paid'
            pay_period.payment_date = payment_date
            pay_period.save()
            
            messages.success(request, 'Payslips marked as paid successfully!')
            return redirect('payroll_overview')
    
    return render(request, 'payroll/pay_period_detail.html', {
        'pay_period': pay_period,
        'payslips': payslips,
        'cleaners_without_payslips': cleaners_without_payslips,
    })


@login_required
@user_passes_test(is_company)
def payslip_detail(request, payslip_id):
    """View and edit a payslip."""
    company_profile = CompanyProfile.objects.get(user=request.user)
    payslip = get_object_or_404(
        Payslip, 
        id=payslip_id, 
        pay_period__company=company_profile
    )
    
    # Get linked time entries
    time_entries = TimeTracking.objects.filter(
        payslip_entries__payslip=payslip
    ).order_by('clock_in')
    
    if request.method == 'POST':
        form = PayslipForm(request.POST, instance=payslip)
        if form.is_valid():
            payslip = form.save()
            messages.success(request, 'Payslip updated successfully!')
            return redirect('payslip_detail', payslip_id=payslip.id)
    else:
        form = PayslipForm(instance=payslip)
    
    return render(request, 'payroll/payslip_detail.html', {
        'payslip': payslip,
        'form': form,
        'time_entries': time_entries,
    })


@login_required
@user_passes_test(is_company)
def manage_contracts(request):
    """View to manage employee contracts."""
    company_profile = CompanyProfile.objects.get(user=request.user)
    
    # Get active contracts
    active_contracts = Contract.objects.filter(
        company=company_profile,
        is_active=True
    ).select_related('cleaner__user', 'pay_scale', 'tax_class')
    
    # Get inactive contracts
    inactive_contracts = Contract.objects.filter(
        company=company_profile,
        is_active=False
    ).select_related('cleaner__user', 'pay_scale', 'tax_class')
    
    return render(request, 'payroll/manage_contracts.html', {
        'active_contracts': active_contracts,
        'inactive_contracts': inactive_contracts,
    })


@login_required
@user_passes_test(is_company)
def create_contract(request):
    """View to create a new employee contract."""
    company_profile = CompanyProfile.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES, company=company_profile)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.company = company_profile
            contract.save()
            
            messages.success(request, 'Contract created successfully!')
            return redirect('manage_contracts')
    else:
        form = ContractForm(company=company_profile)
    
    return render(request, 'payroll/contract_form.html', {
        'form': form,
        'action': 'Create',
    })


@login_required
@user_passes_test(is_company)
def edit_contract(request, contract_id):
    """View to edit an employee contract."""
    company_profile = CompanyProfile.objects.get(user=request.user)
    contract = get_object_or_404(Contract, id=contract_id, company=company_profile)
    
    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES, instance=contract, company=company_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contract updated successfully!')
            return redirect('manage_contracts')
    else:
        form = ContractForm(instance=contract, company=company_profile)
    
    return render(request, 'payroll/contract_form.html', {
        'form': form,
        'contract': contract,
        'action': 'Edit',
    })


@login_required
@user_passes_test(is_cleaner)
def cleaner_payslips(request):
    """View for cleaners to see their payslips."""
    cleaner_profile = CleanerProfile.objects.get(user=request.user)
    
    # Get all payslips for this cleaner
    payslips = Payslip.objects.filter(
        cleaner=cleaner_profile
    ).order_by('-pay_period__start_date')
    
    return render(request, 'payroll/cleaner_payslips.html', {
        'payslips': payslips,
    })


@login_required
@user_passes_test(is_cleaner)
def cleaner_payslip_detail(request, payslip_id):
    """View for cleaners to see details of a specific payslip."""
    cleaner_profile = CleanerProfile.objects.get(user=request.user)
    payslip = get_object_or_404(Payslip, id=payslip_id, cleaner=cleaner_profile)
    
    # Get linked time entries
    time_entries = TimeTracking.objects.filter(
        payslip_entries__payslip=payslip
    ).order_by('clock_in')
    
    return render(request, 'payroll/detail.html', {
        'payslip': payslip,
        'time_entries': time_entries,
    })


@login_required
@user_passes_test(is_company)
def payroll_settings(request):
    """View to manage payroll settings."""
    # Get the current social security rates
    social_security = SocialSecurity.objects.order_by('-year').first()
    
    # Get tax classes
    tax_classes = TaxClass.objects.all()
    
    if request.method == 'POST':
        if 'update_social_security' in request.POST:
            ss_form = SocialSecurityForm(request.POST, instance=social_security)
            if ss_form.is_valid():
                ss_form.save()
                messages.success(request, 'Social security rates updated successfully!')
                return redirect('payroll_settings')
        
        elif 'add_tax_class' in request.POST:
            tax_form = TaxClassForm(request.POST)
            if tax_form.is_valid():
                tax_form.save()
                messages.success(request, 'Tax class added successfully!')
                return redirect('payroll_settings')
        
        elif 'add_pay_scale' in request.POST:
            pay_scale_form = PayScaleForm(request.POST)
            if pay_scale_form.is_valid():
                pay_scale_form.save()
                messages.success(request, 'Pay scale added successfully!')
                return redirect('payroll_settings')
    
    # Initialize forms
    ss_form = SocialSecurityForm(instance=social_security)
    tax_form = TaxClassForm()
    pay_scale_form = PayScaleForm()
    
    return render(request, 'payroll/settings.html', {
        'ss_form': ss_form,
        'tax_form': tax_form,
        'pay_scale_form': pay_scale_form,
        'tax_classes': tax_classes,
    })
