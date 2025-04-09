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
    # Only company users can create contracts
    if request.user.role != User.Role.COMPANY and not request.user.is_staff:
        messages.error(request, "Only company accounts can create contracts.")
        return redirect('contracts:list')
    
    # Get company profile
    try:
        company = CompanyProfile.objects.get(user=request.user)
    except CompanyProfile.DoesNotExist:
        messages.error(request, "Please complete your company profile first.")
        return redirect('contracts:list')
    
    # Check if a template ID was provided
    template_id = request.GET.get('template')
    template = None
    if template_id:
        try:
            template = ContractTemplate.objects.get(id=template_id, company=company)
        except ContractTemplate.DoesNotExist:
            messages.warning(request, "The selected template does not exist or doesn't belong to your company.")
    
    # Generate a unique contract number (YearMonthDay-Company-Number)
    today = timezone.now()
    prefix = f"{today.year}{today.month:02d}{today.day:02d}-{company.id}"
    existing_count = Contract.objects.filter(contract_number__startswith=prefix).count()
    contract_number = f"{prefix}-{existing_count + 1:04d}"
    
    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES, company=company, user=request.user)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.company = company
            contract.created_by = request.user
            
            # If not manually set, provide the generated contract number
            if not contract.contract_number or contract.contract_number == '':
                contract.contract_number = contract_number
                
            # Set initial status
            contract.status = 'draft'
            
            contract.save()
            
            # Create notification for the cleaner
            cleaner_user = contract.cleaner.user
            notification = ContractNotification.objects.create(
                contract=contract,
                user=cleaner_user,
                title="New Contract Created",
                message=f"A new contract has been created for you by {company.company_name}. Please review it.",
                notification_type="contract_created"
            )
            
            messages.success(request, f"Contract '{contract.title}' created successfully! It is now in draft status.")
            return redirect('contracts:detail', contract_id=contract.id)
    else:
        # Initialize form with default values
        initial_data = {
            'contract_number': contract_number,
            'template': template,
        }
        
        # If a template was selected, populate fields from template defaults
        if template:
            # Get default terms from template
            try:
                default_terms = template.default_terms
                
                # Populate form fields from template defaults where applicable
                if 'title' in default_terms:
                    initial_data['title'] = default_terms['title']
                
                if 'description' in default_terms:
                    initial_data['description'] = default_terms['description']
                
                if 'working_hours' in default_terms:
                    initial_data['working_hours_weekly'] = default_terms['working_hours']
                
                if 'hourly_rate' in default_terms:
                    initial_data['hourly_rate'] = default_terms['hourly_rate']
                
                if 'monthly_salary' in default_terms:
                    initial_data['monthly_salary'] = default_terms['monthly_salary']
                
                # Set contract type if specified in template
                if 'contract_type' in default_terms:
                    initial_data['contract_type'] = default_terms['contract_type']
                
                # Set terms and conditions from template
                initial_data['terms_and_conditions'] = default_terms
                
            except (ValueError, KeyError, TypeError):
                # If there's an error parsing the JSON, don't use template defaults
                messages.warning(request, "Could not apply template defaults due to invalid format.")
        
        form = ContractForm(initial=initial_data, company=company, user=request.user)
    
    context = {
        'title': 'Create New Contract',
        'section': 'contracts',
        'form': form,
        'company': company,
        'selected_template': template,
    }
    return render(request, 'contracts/contract_form.html', context)

@login_required
def contract_detail_view(request, contract_id):
    """View for viewing details of a contract."""
    # Get the contract
    contract = get_object_or_404(Contract, id=contract_id)
    
    # Check if user has access to this contract
    user = request.user
    if not user.is_staff:
        if user.role == User.Role.COMPANY:
            # If company user, check if contract belongs to their company
            try:
                company = CompanyProfile.objects.get(user=user)
                if contract.company != company:
                    messages.error(request, "You do not have permission to view this contract.")
                    return redirect('contracts:list')
            except CompanyProfile.DoesNotExist:
                messages.error(request, "Please complete your company profile first.")
                return redirect('contracts:list')
        elif user.role == User.Role.CLEANER:
            # If cleaner user, check if contract belongs to them
            try:
                cleaner_profile = CleanerProfile.objects.get(user=user)
                if contract.cleaner != cleaner_profile:
                    messages.error(request, "You do not have permission to view this contract.")
                    return redirect('contracts:list')
            except CleanerProfile.DoesNotExist:
                messages.error(request, "Please complete your cleaner profile first.")
                return redirect('contracts:list')
        else:
            # Customer users shouldn't access contracts
            messages.error(request, "You do not have permission to view contracts.")
            return redirect('dashboard')
    
    # Get addenda for this contract
    addenda = ContractAddendum.objects.filter(contract=contract).order_by('-created_at')
    
    # Handle contract actions
    action = request.GET.get('action')
    if action == 'submit' and request.user.role == User.Role.COMPANY and contract.status == 'draft':
        # Submit contract for cleaner approval
        contract.status = 'pending_cleaner'
        contract.save()
        
        # Create notification for the cleaner
        cleaner_user = contract.cleaner.user
        notification = ContractNotification.objects.create(
            contract=contract,
            user=cleaner_user,
            title="Contract Ready for Review",
            message=f"A contract from {contract.company.company_name} is ready for your review and approval.",
            notification_type="contract_updated"
        )
        
        messages.success(request, "Contract has been submitted for cleaner approval.")
        return redirect('contracts:detail', contract_id=contract.id)
    
    context = {
        'title': 'Contract Details',
        'section': 'contracts',
        'contract': contract,
        'addenda': addenda,
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
    # Get the contract
    contract = get_object_or_404(Contract, id=contract_id)
    
    # Verify user has rights to delete this contract
    user = request.user
    if not user.is_staff and user.role == User.Role.COMPANY:
        # Company users can only delete their own contracts in draft state
        try:
            company = CompanyProfile.objects.get(user=user)
            if contract.company != company:
                messages.error(request, "You do not have permission to delete this contract.")
                return redirect('contracts:list')
            if contract.status != 'draft':
                messages.error(request, "You can only delete contracts that are in draft status.")
                return redirect('contracts:detail', contract_id=contract.id)
        except CompanyProfile.DoesNotExist:
            messages.error(request, "Please complete your company profile first.")
            return redirect('contracts:list')
    elif not user.is_staff:
        # Non-staff, non-company users can't delete contracts
        messages.error(request, "You do not have permission to delete contracts.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Store information for confirmation message
        contract_number = contract.contract_number
        contract_title = contract.title
        cleaner_name = contract.cleaner.user.get_full_name()
        
        # Delete the contract
        contract.delete()
        
        messages.success(request, f"Contract {contract_number}: '{contract_title}' with {cleaner_name} was successfully deleted.")
        return redirect('contracts:list')
    
    # If not a POST request, redirect to contract detail (deletion should be via POST from the detail page)
    return redirect('contracts:detail', contract_id=contract_id)

# Contract workflow actions
@login_required
def approve_contract_view(request, contract_id):
    """View for approving a contract."""
    # Get the contract
    contract = get_object_or_404(Contract, id=contract_id)
    user = request.user
    
    # Verify user has rights to approve this contract
    if user.is_staff:
        # Admin can approve any contract
        pass
    elif user.role == User.Role.COMPANY:
        # Company can approve if it's their contract and it's pending company approval
        try:
            company = CompanyProfile.objects.get(user=user)
            if contract.company != company:
                messages.error(request, "You do not have permission to approve this contract.")
                return redirect('contracts:list')
            if contract.status != 'pending_company':
                messages.error(request, "This contract is not pending company approval.")
                return redirect('contracts:detail', contract_id=contract.id)
        except CompanyProfile.DoesNotExist:
            messages.error(request, "Please complete your company profile first.")
            return redirect('contracts:list')
    elif user.role == User.Role.CLEANER:
        # Cleaner can approve if they're the cleaner and it's pending cleaner approval
        try:
            cleaner_profile = CleanerProfile.objects.get(user=user)
            if contract.cleaner != cleaner_profile:
                messages.error(request, "You do not have permission to approve this contract.")
                return redirect('contracts:list')
            if contract.status != 'pending_cleaner':
                messages.error(request, "This contract is not pending your approval.")
                return redirect('contracts:detail', contract_id=contract.id)
        except CleanerProfile.DoesNotExist:
            messages.error(request, "Please complete your cleaner profile first.")
            return redirect('contracts:list')
    else:
        messages.error(request, "You do not have permission to approve contracts.")
        return redirect('dashboard')
    
    # Process the approval
    if user.role == User.Role.COMPANY or user.is_staff:
        contract.is_company_approved = True
        contract.company_signed_date = timezone.now()
        contract.company_signatory = user
        
        # If both parties approved, mark as active
        if contract.is_cleaner_approved:
            contract.status = 'active'
            notification_message = "Contract has been fully approved and is now active."
        else:
            # If only company approved, set to pending cleaner
            contract.status = 'pending_cleaner'
            notification_message = "Contract has been approved by the company and is pending cleaner approval."
    
    elif user.role == User.Role.CLEANER:
        contract.is_cleaner_approved = True
        contract.cleaner_signed_date = timezone.now()
        
        # If both parties approved, mark as active
        if contract.is_company_approved:
            contract.status = 'active'
            notification_message = "Contract has been fully approved and is now active."
        else:
            # If only cleaner approved, set to pending company
            contract.status = 'pending_company'
            notification_message = "Contract has been approved by the cleaner and is pending company approval."
    
    contract.save()
    
    # Create notifications for both parties
    cleaner_user = contract.cleaner.user
    company_user = contract.company.user
    
    # Notification for the company
    ContractNotification.objects.create(
        contract=contract,
        user=company_user,
        title="Contract Update",
        message=notification_message,
        notification_type="contract_signed"
    )
    
    # Notification for the cleaner
    if cleaner_user != company_user:  # Avoid duplicate notifications
        ContractNotification.objects.create(
            contract=contract,
            user=cleaner_user,
            title="Contract Update",
            message=notification_message,
            notification_type="contract_signed"
        )
    
    messages.success(request, "Contract approved successfully. " + notification_message)
    return redirect('contracts:detail', contract_id=contract.id)

@login_required
def reject_contract_view(request, contract_id):
    """View for rejecting a contract."""
    # Get the contract
    contract = get_object_or_404(Contract, id=contract_id)
    user = request.user
    
    # Verify user has rights to reject this contract
    if user.is_staff:
        # Admin can reject any contract
        pass
    elif user.role == User.Role.COMPANY:
        # Company can reject if it's their contract
        try:
            company = CompanyProfile.objects.get(user=user)
            if contract.company != company:
                messages.error(request, "You do not have permission to reject this contract.")
                return redirect('contracts:list')
            if contract.status not in ['pending_company', 'draft']:
                messages.error(request, "You can only reject contracts that are in draft or pending company approval.")
                return redirect('contracts:detail', contract_id=contract.id)
        except CompanyProfile.DoesNotExist:
            messages.error(request, "Please complete your company profile first.")
            return redirect('contracts:list')
    elif user.role == User.Role.CLEANER:
        # Cleaner can reject if they're the cleaner and it's pending cleaner approval
        try:
            cleaner_profile = CleanerProfile.objects.get(user=user)
            if contract.cleaner != cleaner_profile:
                messages.error(request, "You do not have permission to reject this contract.")
                return redirect('contracts:list')
            if contract.status != 'pending_cleaner':
                messages.error(request, "You can only reject contracts that are pending your approval.")
                return redirect('contracts:detail', contract_id=contract.id)
        except CleanerProfile.DoesNotExist:
            messages.error(request, "Please complete your cleaner profile first.")
            return redirect('contracts:list')
    else:
        messages.error(request, "You do not have permission to reject contracts.")
        return redirect('dashboard')
    
    # Get the reason for rejection (optional)
    reason = request.GET.get('reason', 'No reason provided.')
    
    # Process the rejection
    if user.role == User.Role.COMPANY or user.is_staff:
        # If company rejects, set back to draft
        contract.status = 'draft'
        contract.is_company_approved = False
        contract.company_signed_date = None
        notification_message = f"Contract has been rejected by the company. Reason: {reason}"
    
    elif user.role == User.Role.CLEANER:
        # If cleaner rejects, set back to draft
        contract.status = 'draft'
        contract.is_cleaner_approved = False
        contract.cleaner_signed_date = None
        notification_message = f"Contract has been rejected by the cleaner. Reason: {reason}"
    
    contract.save()
    
    # Create notifications for both parties
    cleaner_user = contract.cleaner.user
    company_user = contract.company.user
    
    # Notification for the company
    ContractNotification.objects.create(
        contract=contract,
        user=company_user,
        title="Contract Rejected",
        message=notification_message,
        notification_type="contract_updated"
    )
    
    # Notification for the cleaner
    if cleaner_user != company_user:  # Avoid duplicate notifications
        ContractNotification.objects.create(
            contract=contract,
            user=cleaner_user,
            title="Contract Rejected",
            message=notification_message,
            notification_type="contract_updated"
        )
    
    messages.warning(request, "Contract rejected. " + notification_message)
    return redirect('contracts:detail', contract_id=contract.id)

@login_required
def sign_contract_view(request, contract_id):
    """View for signing a contract."""
    return redirect('contracts:detail', contract_id=contract_id)

@login_required
def terminate_contract_view(request, contract_id):
    """View for terminating a contract."""
    # Get the contract
    contract = get_object_or_404(Contract, id=contract_id)
    
    # Verify user has rights to terminate this contract
    user = request.user
    if not user.is_staff and user.role == User.Role.COMPANY:
        # Company users can terminate their own active contracts
        try:
            company = CompanyProfile.objects.get(user=user)
            if contract.company != company:
                messages.error(request, "You do not have permission to terminate this contract.")
                return redirect('contracts:list')
            if contract.status != 'active':
                messages.error(request, "You can only terminate active contracts.")
                return redirect('contracts:detail', contract_id=contract.id)
        except CompanyProfile.DoesNotExist:
            messages.error(request, "Please complete your company profile first.")
            return redirect('contracts:list')
    elif not user.is_staff:
        # Non-staff, non-company users can't terminate contracts
        messages.error(request, "You do not have permission to terminate contracts.")
        return redirect('dashboard')
    
    # Handle form submission for termination
    if request.method == 'POST':
        reason = request.POST.get('termination_reason', 'No reason provided.')
        termination_date = request.POST.get('termination_date')
        
        try:
            # Set termination date and reason
            contract.termination_date = termination_date
            contract.termination_reason = reason
            contract.status = 'terminated'
            contract.save()
            
            # Create notifications for both parties
            cleaner_user = contract.cleaner.user
            company_user = contract.company.user
            
            notification_message = f"Contract has been terminated effective {termination_date}. Reason: {reason}"
            
            # Notification for the company
            ContractNotification.objects.create(
                contract=contract,
                user=company_user,
                title="Contract Terminated",
                message=notification_message,
                notification_type="contract_updated"
            )
            
            # Notification for the cleaner
            if cleaner_user != company_user:  # Avoid duplicate notifications
                ContractNotification.objects.create(
                    contract=contract,
                    user=cleaner_user,
                    title="Contract Terminated",
                    message=notification_message,
                    notification_type="contract_updated"
                )
            
            messages.warning(request, f"Contract has been terminated. {notification_message}")
            return redirect('contracts:detail', contract_id=contract.id)
            
        except Exception as e:
            messages.error(request, f"Error terminating contract: {str(e)}")
            return redirect('contracts:detail', contract_id=contract.id)
    
    # If not a POST request, show termination form on the contract detail page
    return redirect('contracts:detail', contract_id=contract.id)

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