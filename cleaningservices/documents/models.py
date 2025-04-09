from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User, CompanyProfile
from django.utils import timezone


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


class ChatConversation(models.Model):
    """Tracks chatbot conversations with users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_conversations')
    title = models.CharField(max_length=255, default="New Conversation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Optional reference to related document if conversation is specific to a document
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, 
                                related_name='conversations', null=True, blank=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation with {self.user.email} on {self.created_at.strftime('%Y-%m-%d')}"
    
    @property
    def message_count(self):
        return self.messages.count()
    
    @property
    def last_message(self):
        return self.messages.order_by('-timestamp').first()
    
    def mark_inactive(self):
        self.is_active = False
        self.save()
        
    def update_title_from_first_message(self):
        """Set conversation title based on first user message if available."""
        first_message = self.messages.filter(is_bot=False).order_by('timestamp').first()
        if first_message:
            # Truncate long messages
            title = first_message.message[:50]
            if len(first_message.message) > 50:
                title += "..."
            self.title = title
            self.save()


class ChatMessage(models.Model):
    """Individual messages in a chatbot conversation."""
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_bot = models.BooleanField(default=False)
    
    # Optional reference to documents that were referenced in this message
    referenced_documents = models.ManyToManyField(Document, related_name='referenced_in_messages', blank=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        sender = "Bot" if self.is_bot else self.conversation.user.email
        return f"Message from {sender} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
