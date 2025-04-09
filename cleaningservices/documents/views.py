from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
import mimetypes

from accounts.models import User, CompanyProfile
from .models import Document, DocumentCategory, DocumentAccess, DocumentComment
from .forms import DocumentForm, DocumentCategoryForm, DocumentCommentForm, DocumentSearchForm


def is_company_or_admin(user):
    """Check if user is a company or admin."""
    return user.is_authenticated and (user.role == User.Role.COMPANY or user.is_staff)


@login_required
def document_list_view(request):
    """View for listing documents with search and filtering."""
    user = request.user
    
    # Initial queryset based on access level
    if user.is_staff:
        # Admins can see all documents
        queryset = Document.objects.all()
    elif user.role == User.Role.COMPANY:
        # Companies can see their own documents and public ones
        company = CompanyProfile.objects.get(user=user)
        queryset = Document.objects.filter(
            Q(access_level='public') | 
            Q(company=company) |
            Q(created_by=user)
        ).distinct()
    else:
        # Regular users can only see public documents and their own
        queryset = Document.objects.filter(
            Q(access_level='public') |
            Q(created_by=user)
        ).distinct()
    
    # Search and filter functionality
    form = DocumentSearchForm(request.GET)
    if form.is_valid():
        # Apply search query
        query = form.cleaned_data.get('query')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__contains=[query])
            )
        
        # Filter by category
        category = form.cleaned_data.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by document type
        document_type = form.cleaned_data.get('document_type')
        if document_type:
            queryset = queryset.filter(document_type=document_type)
    
    # Order results
    queryset = queryset.order_by('-created_at')
    
    # Paginate results
    paginator = Paginator(queryset, 12)
    page = request.GET.get('page')
    
    try:
        documents = paginator.page(page)
    except PageNotAnInteger:
        documents = paginator.page(1)
    except EmptyPage:
        documents = paginator.page(paginator.num_pages)
    
    # Get categories for sidebar
    categories = DocumentCategory.objects.all()
    
    return render(request, 'documents/list.html', {
        'documents': documents,
        'categories': categories,
        'form': form,
    })


@login_required
def document_detail_view(request, document_id):
    """View for displaying document details."""
    document = get_object_or_404(Document, id=document_id)
    user = request.user
    
    # Check access permissions
    if document.access_level == 'private' and document.created_by != user:
        messages.error(request, 'You do not have permission to view this document.')
        return redirect('document_list')
    elif document.access_level == 'company':
        if user.role != User.Role.COMPANY and not user.is_staff:
            # Non-company users can't access company documents
            messages.error(request, 'You do not have permission to view this document.')
            return redirect('document_list')
        elif user.role == User.Role.COMPANY:
            # Companies can only view their own company documents
            company = CompanyProfile.objects.get(user=user)
            if document.company != company and document.created_by != user:
                messages.error(request, 'You do not have permission to view this document.')
                return redirect('document_list')
    
    # Record document access
    DocumentAccess.objects.create(
        document=document,
        user=user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Handle comments
    if request.method == 'POST':
        comment_form = DocumentCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.document = document
            comment.user = user
            comment.save()
            messages.success(request, 'Your comment has been added successfully.')
            return redirect('document_detail', document_id=document.id)
    else:
        comment_form = DocumentCommentForm()
    
    # Get comments for this document
    comments = DocumentComment.objects.filter(document=document).order_by('-created_at')
    
    # Related documents (same category or tags)
    if document.tags:
        related_documents = Document.objects.filter(
            Q(category=document.category) | 
            Q(tags__overlap=document.tags)
        ).exclude(id=document.id)[:5]
    else:
        related_documents = Document.objects.filter(
            category=document.category
        ).exclude(id=document.id)[:5]
    
    return render(request, 'documents/detail.html', {
        'document': document,
        'comments': comments,
        'comment_form': comment_form,
        'related_documents': related_documents,
    })


@login_required
def document_download_view(request, document_id):
    """View for downloading document files."""
    document = get_object_or_404(Document, id=document_id)
    user = request.user
    
    # Check access permissions (similar to detail view)
    if document.access_level == 'private' and document.created_by != user:
        messages.error(request, 'You do not have permission to download this document.')
        return redirect('document_list')
    elif document.access_level == 'company':
        if user.role != User.Role.COMPANY and not user.is_staff:
            messages.error(request, 'You do not have permission to download this document.')
            return redirect('document_list')
        elif user.role == User.Role.COMPANY:
            company = CompanyProfile.objects.get(user=user)
            if document.company != company and document.created_by != user:
                messages.error(request, 'You do not have permission to download this document.')
                return redirect('document_list')
    
    # Record document access
    DocumentAccess.objects.create(
        document=document,
        user=user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Prepare file for download
    file_path = document.file.path
    file_name = document.file.name.split('/')[-1]
    
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read())
    
    content_type, encoding = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = 'application/octet-stream'
    
    response['Content-Type'] = content_type
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    
    return response


@login_required
@user_passes_test(is_company_or_admin)
def upload_document_view(request):
    """View for uploading new documents."""
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.created_by = request.user
            
            # If company user, associate with company
            if request.user.role == User.Role.COMPANY:
                document.company = CompanyProfile.objects.get(user=request.user)
            
            document.save()
            messages.success(request, 'Document uploaded successfully!')
            return redirect('document_detail', document_id=document.id)
    else:
        form = DocumentForm()
    
    return render(request, 'documents/upload.html', {
        'form': form,
    })


@login_required
@user_passes_test(is_company_or_admin)
def edit_document_view(request, document_id):
    """View for editing existing documents."""
    document = get_object_or_404(Document, id=document_id)
    
    # Check ownership
    if document.created_by != request.user and not request.user.is_staff:
        if request.user.role == User.Role.COMPANY:
            company = CompanyProfile.objects.get(user=request.user)
            if document.company != company:
                messages.error(request, 'You do not have permission to edit this document.')
                return redirect('document_detail', document_id=document.id)
        else:
            messages.error(request, 'You do not have permission to edit this document.')
            return redirect('document_detail', document_id=document.id)
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, 'Document updated successfully!')
            return redirect('document_detail', document_id=document.id)
    else:
        form = DocumentForm(instance=document)
    
    return render(request, 'documents/edit.html', {
        'form': form,
        'document': document,
    })


@login_required
@user_passes_test(is_company_or_admin)
def delete_document_view(request, document_id):
    """View for deleting documents."""
    document = get_object_or_404(Document, id=document_id)
    
    # Check ownership
    if document.created_by != request.user and not request.user.is_staff:
        if request.user.role == User.Role.COMPANY:
            company = CompanyProfile.objects.get(user=request.user)
            if document.company != company:
                messages.error(request, 'You do not have permission to delete this document.')
                return redirect('document_detail', document_id=document.id)
        else:
            messages.error(request, 'You do not have permission to delete this document.')
            return redirect('document_detail', document_id=document.id)
    
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted successfully!')
        return redirect('document_list')
    
    return render(request, 'documents/delete.html', {
        'document': document,
    })


@login_required
@user_passes_test(is_company_or_admin)
def manage_categories_view(request):
    """View for managing document categories."""
    categories = DocumentCategory.objects.all()
    
    if request.method == 'POST':
        form = DocumentCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('manage_categories')
    else:
        form = DocumentCategoryForm()
    
    return render(request, 'documents/manage_categories.html', {
        'categories': categories,
        'form': form,
    })
