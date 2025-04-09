from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User, CompanyProfile


class DocumentCategory(models.Model):
    """Categories for cleaning documents."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Document Categories"
    
    def __str__(self):
        return self.name


class Document(models.Model):
    """Documents related to cleaning procedures and solutions."""
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(DocumentCategory, on_delete=models.CASCADE, related_name='documents')
    
    # Store the actual file
    file = models.FileField(upload_to='documents/')
    
    # Document metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_documents')
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='company_documents', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Access control
    ACCESS_CHOICES = [
        ('public', 'Public - Available to all users'),
        ('company', 'Company - Available to company members only'),
        ('private', 'Private - Available to uploader only'),
    ]
    access_level = models.CharField(max_length=20, choices=ACCESS_CHOICES, default='company')
    
    # Document type
    TYPE_CHOICES = [
        ('procedure', 'Cleaning Procedure'),
        ('solution', 'Cleaning Solution'),
        ('safety', 'Safety Document'),
        ('equipment', 'Equipment Manual'),
        ('training', 'Training Material'),
        ('other', 'Other Document'),
    ]
    document_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='procedure')
    
    # Tags for searchability
    tags = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return self.title


class DocumentAccess(models.Model):
    """Tracks document access by users."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_accesses')
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Document Accesses"
        ordering = ['-accessed_at']
    
    def __str__(self):
        return f"{self.user.email} accessed {self.document.title} at {self.accessed_at}"


class DocumentComment(models.Model):
    """Comments on documents."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.user.email} on {self.document.title}"
