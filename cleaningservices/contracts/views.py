from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from .models import ContractTemplate, Contract, ContractAddendum, ContractNotification
from .forms import ContractForm, ContractTemplateForm, ContractAddendumForm
from accounts.models import User, CompanyProfile, CleanerProfile

# Contract List Views
@login_required
def contract_list_view(request):
    """View for listing all contracts a user has access to."""
    user = request.user
    contracts = []
    
    # Filter contracts based on user role
    if user.is_staff:
        # Admins can see all contracts
        contracts = Contract.objects.all().order_by('-created_at')
        
    elif user.role == User.Role.COMPANY:
        # Companies see their own contracts
        try:
            company = CompanyProfile.objects.get(user=user)
            contracts = Contract.objects.filter(company=company).order_by('-created_at')
        except CompanyProfile.DoesNotExist:
            messages.warning(request, "Please complete your company profile first.")
            
    elif user.role == User.Role.CLEANER:
        # Cleaners see contracts where they're the cleaner
        try:
            cleaner_profile = CleanerProfile.objects.get(user=user)
            contracts = Contract.objects.filter(cleaner=cleaner_profile).order_by('-created_at')
        except CleanerProfile.DoesNotExist:
            messages.warning(request, "Please complete your cleaner profile first.")
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        contracts = contracts.filter(status=status_filter)
    
    context = {
        'title': 'Contracts',
        'section': 'contracts',
        'contracts': contracts,
        'status_filter': status_filter
    }
    return render(request, 'contracts/contract_list.html', context)

@login_required
def contract_template_list_view(request):
    """View for listing contract templates."""
    user = request.user
    templates = []
    
    # Filter templates based on user role
    if user.is_staff:
        # Admins can see all templates
        templates = ContractTemplate.objects.all().order_by('-created_at')
        
    elif user.role == User.Role.COMPANY:
        # Companies see their own templates
        try:
            company = CompanyProfile.objects.get(user=user)
            templates = ContractTemplate.objects.filter(company=company).order_by('-created_at')
        except CompanyProfile.DoesNotExist:
            messages.warning(request, "Please complete your company profile first.")
    
    context = {
        'title': 'Contract Templates',
        'section': 'contracts',
        'templates': templates
    }
    return render(request, 'contracts/template_list.html', context)

# Contract Template CRUD operations
@login_required
@permission_required('contracts.add_contracttemplate')
def create_contract_template_view(request):
    """View for creating a new contract template."""
    # Only company users can create templates
    if request.user.role != User.Role.COMPANY and not request.user.is_staff:
        messages.error(request, "Only company accounts can create contract templates.")
        return redirect('contracts:template_list')
    
    # Get company profile
    try:
        company = CompanyProfile.objects.get(user=request.user)
    except CompanyProfile.DoesNotExist:
        messages.error(request, "Please complete your company profile first.")
        return redirect('contracts:template_list')
    
    if request.method == 'POST':
        form = ContractTemplateForm(request.POST, request.FILES, company=company)
        if form.is_valid():
            template = form.save()
            messages.success(request, f"Contract template '{template.name}' created successfully!")
            return redirect('contracts:template_detail', template_id=template.id)
    else:
        # Initialize with empty form
        form = ContractTemplateForm(company=company)
    
    context = {
        'title': 'Create Contract Template',
        'section': 'contracts',
        'form': form,
    }
    return render(request, 'contracts/template_form.html', context)

@login_required
def contract_template_detail_view(request, template_id):
    """View for viewing details of a contract template."""
    # Get the template
    template = get_object_or_404(ContractTemplate, id=template_id)
    
    # Check if user has access to this template
    user = request.user
    if not user.is_staff and user.role == User.Role.COMPANY:
        # If company user, check if template belongs to their company
        try:
            company = CompanyProfile.objects.get(user=user)
            if template.company != company:
                messages.error(request, "You do not have permission to view this template.")
                return redirect('contracts:template_list')
        except CompanyProfile.DoesNotExist:
            messages.error(request, "Please complete your company profile first.")
            return redirect('contracts:template_list')
    elif not user.is_staff and user.role != User.Role.COMPANY:
        # Only company users and staff can view templates
        messages.error(request, "You do not have permission to view contract templates.")
        return redirect('contracts:list')
    
    # Count contracts using this template
    contracts_count = Contract.objects.filter(template=template).count()
    
    context = {
        'title': 'Contract Template Details',
        'section': 'contracts',
        'template': template,
        'contracts_count': contracts_count,
    }
    return render(request, 'contracts/template_detail.html', context)

@login_required
@permission_required('contracts.change_contracttemplate')
def edit_contract_template_view(request, template_id):
    """View for editing a contract template."""
    # Get the template
    template = get_object_or_404(ContractTemplate, id=template_id)
    
    # Check if user has permission to edit this template
    user = request.user
    if not user.is_staff and user.role == User.Role.COMPANY:
        # If company user, check if template belongs to their company
        try:
            company = CompanyProfile.objects.get(user=user)
            if template.company != company:
                messages.error(request, "You do not have permission to edit this template.")
                return redirect('contracts:template_list')
        except CompanyProfile.DoesNotExist:
            messages.error(request, "Please complete your company profile first.")
            return redirect('contracts:template_list')
    elif not user.is_staff and user.role != User.Role.COMPANY:
        # Only company users and staff can edit templates
        messages.error(request, "You do not have permission to edit contract templates.")
        return redirect('contracts:list')
    
    # Get the company
    if user.role == User.Role.COMPANY:
        company = CompanyProfile.objects.get(user=user)
    else:
        # For staff users, use the template's existing company
        company = template.company
    
    if request.method == 'POST':
        form = ContractTemplateForm(request.POST, request.FILES, instance=template, company=company)
        if form.is_valid():
            updated_template = form.save()
            messages.success(request, f"Contract template '{updated_template.name}' updated successfully!")
            return redirect('contracts:template_detail', template_id=updated_template.id)
    else:
        # Initialize form with existing template data
        form = ContractTemplateForm(instance=template, company=company)
    
    context = {
        'title': 'Edit Contract Template',
        'section': 'contracts',
        'form': form,
        'template': template,
    }
    return render(request, 'contracts/template_form.html', context)

@login_required
@permission_required('contracts.delete_contracttemplate')
def delete_contract_template_view(request, template_id):
    """View for deleting a contract template."""
    template = get_object_or_404(ContractTemplate, id=template_id)
    
    # Check if user has permission to delete this template
    user = request.user
    if not user.is_staff and user.role == User.Role.COMPANY:
        # If company user, check if template belongs to their company
        try:
            company = CompanyProfile.objects.get(user=user)
            if template.company != company:
                messages.error(request, "You do not have permission to delete this template.")
                return redirect('contracts:template_list')
        except CompanyProfile.DoesNotExist:
            messages.error(request, "Please complete your company profile first.")
            return redirect('contracts:template_list')
    elif not user.is_staff and user.role != User.Role.COMPANY:
        # Only company users and staff can delete templates
        messages.error(request, "You do not have permission to delete contract templates.")
        return redirect('contracts:list')
    
    # Count contracts using this template
    contract_count = Contract.objects.filter(template=template).count()
    
    if request.method == 'POST':
        template_name = template.name
        
        # Delete the template
        template.delete()
        
        # Show success message
        messages.success(request, f"Contract template '{template_name}' was deleted successfully. Note that {contract_count} contracts previously using this template will no longer be linked to it.")
        
        return redirect('contracts:template_list')
    
    # If not POST, redirect to detail page (deletion should be via POST from the detail page)
    return redirect('contracts:template_detail', template_id=template_id)

# Contract CRUD operations
@login_required
@permission_required('contracts.add_contract')
def create_contract_view(request):
    """View for creating a new contract."""
    context = {
        'title': 'Create New Contract',
        'section': 'contracts',
    }
    return render(request, 'contracts/contract_form.html', context)

@login_required
def contract_detail_view(request, contract_id):
    """View for viewing details of a contract."""
    context = {
        'title': 'Contract Details',
        'section': 'contracts',
    }
    return render(request, 'contracts/contract_detail.html', context)

@login_required
@permission_required('contracts.change_contract')
def edit_contract_view(request, contract_id):
    """View for editing a contract."""
    context = {
        'title': 'Edit Contract',
        'section': 'contracts',
    }
    return render(request, 'contracts/contract_form.html', context)

@login_required
@permission_required('contracts.delete_contract')
def delete_contract_view(request, contract_id):
    """View for deleting a contract."""
    return redirect('contracts:list')

# Contract workflow actions
@login_required
def approve_contract_view(request, contract_id):
    """View for approving a contract."""
    return redirect('contracts:detail', contract_id=contract_id)

@login_required
def reject_contract_view(request, contract_id):
    """View for rejecting a contract."""
    return redirect('contracts:detail', contract_id=contract_id)

@login_required
def sign_contract_view(request, contract_id):
    """View for signing a contract."""
    return redirect('contracts:detail', contract_id=contract_id)

@login_required
def terminate_contract_view(request, contract_id):
    """View for terminating a contract."""
    return redirect('contracts:detail', contract_id=contract_id)

# Contract addendum operations
@login_required
@permission_required('contracts.add_contractaddendum')
def create_addendum_view(request, contract_id):
    """View for creating a new contract addendum."""
    context = {
        'title': 'Create Addendum',
        'section': 'contracts',
    }
    return render(request, 'contracts/addendum_form.html', context)

@login_required
def addendum_detail_view(request, addendum_id):
    """View for viewing details of a contract addendum."""
    context = {
        'title': 'Addendum Details',
        'section': 'contracts',
    }
    return render(request, 'contracts/addendum_detail.html', context)

@login_required
@permission_required('contracts.change_contractaddendum')
def edit_addendum_view(request, addendum_id):
    """View for editing a contract addendum."""
    context = {
        'title': 'Edit Addendum',
        'section': 'contracts',
    }
    return render(request, 'contracts/addendum_form.html', context)

@login_required
@permission_required('contracts.delete_contractaddendum')
def delete_addendum_view(request, addendum_id):
    """View for deleting a contract addendum."""
    return redirect('contracts:list')

@login_required
def approve_addendum_view(request, addendum_id):
    """View for approving a contract addendum."""
    return redirect('contracts:addendum_detail', addendum_id=addendum_id)

@login_required
def reject_addendum_view(request, addendum_id):
    """View for rejecting a contract addendum."""
    return redirect('contracts:addendum_detail', addendum_id=addendum_id)