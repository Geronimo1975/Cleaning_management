from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib import messages
from .models import ContractTemplate, Contract, ContractAddendum, ContractNotification

# Contract List Views
@login_required
def contract_list_view(request):
    """View for listing all contracts a user has access to."""
    context = {
        'title': 'Contracts',
        'section': 'contracts',
    }
    return render(request, 'contracts/contract_list.html', context)

@login_required
def contract_template_list_view(request):
    """View for listing contract templates."""
    context = {
        'title': 'Contract Templates',
        'section': 'contracts',
    }
    return render(request, 'contracts/template_list.html', context)

# Contract Template CRUD operations
@login_required
@permission_required('contracts.add_contracttemplate')
def create_contract_template_view(request):
    """View for creating a new contract template."""
    context = {
        'title': 'Create Contract Template',
        'section': 'contracts',
    }
    return render(request, 'contracts/template_form.html', context)

@login_required
def contract_template_detail_view(request, template_id):
    """View for viewing details of a contract template."""
    context = {
        'title': 'Contract Template Details',
        'section': 'contracts',
    }
    return render(request, 'contracts/template_detail.html', context)

@login_required
@permission_required('contracts.change_contracttemplate')
def edit_contract_template_view(request, template_id):
    """View for editing a contract template."""
    context = {
        'title': 'Edit Contract Template',
        'section': 'contracts',
    }
    return render(request, 'contracts/template_form.html', context)

@login_required
@permission_required('contracts.delete_contracttemplate')
def delete_contract_template_view(request, template_id):
    """View for deleting a contract template."""
    return redirect('contracts:template_list')

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