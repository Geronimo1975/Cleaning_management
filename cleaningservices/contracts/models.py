from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User, CleanerProfile, CompanyProfile


class ContractTemplate(models.Model):
    """Templates for different types of contracts."""
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='contract_templates')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    template_file = models.FileField(upload_to='contract_templates/', null=True, blank=True)
    template_content = models.TextField(help_text="HTML template with placeholders for contract fields")
    
    # Default terms
    default_terms = models.JSONField(default=dict, help_text="Default terms as JSON")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.company.company_name}"


class Contract(models.Model):
    """Legal contracts between cleaners and cleaning companies."""
    
    # Contract parties
    cleaner = models.ForeignKey(CleanerProfile, on_delete=models.CASCADE, related_name='company_contracts')
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='cleaner_contracts')
    template = models.ForeignKey(ContractTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Contract details
    contract_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # Contract dates
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Contract type (similar to employment type)
    CONTRACT_TYPE_CHOICES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('mini_job', 'Mini-job'),
        ('freelance', 'Freelance/Self-employed'),
    ]
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES)
    
    # Working terms
    working_hours_weekly = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Contractual clauses
    terms_and_conditions = models.JSONField(default=dict, help_text="Contract terms as JSON")
    
    # Contract documents
    contract_file = models.FileField(upload_to='contracts/', blank=True, null=True)
    
    # Approval and signatures
    is_company_approved = models.BooleanField(default=False)
    company_signed_date = models.DateTimeField(null=True, blank=True)
    company_signatory = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='signed_contracts_as_company'
    )
    
    is_cleaner_approved = models.BooleanField(default=False)
    cleaner_signed_date = models.DateTimeField(null=True, blank=True)
    
    # Contract status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_cleaner', 'Pending Cleaner Approval'),
        ('pending_company', 'Pending Company Approval'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    termination_date = models.DateField(null=True, blank=True)
    termination_reason = models.TextField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_contracts')
    
    def __str__(self):
        return f"Contract {self.contract_number}: {self.cleaner.user.get_full_name()} - {self.company.company_name}"
    
    def is_fully_signed(self):
        """Check if the contract is signed by both parties."""
        return self.is_company_approved and self.is_cleaner_approved


class ContractAddendum(models.Model):
    """Changes or additions to existing contracts."""
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='addenda')
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Dates
    effective_date = models.DateField()
    
    # Changes to contract
    changes = models.JSONField(default=dict, help_text="Changes to contract terms as JSON")
    
    # Approval
    is_company_approved = models.BooleanField(default=False)
    company_approved_date = models.DateTimeField(null=True, blank=True)
    company_approver = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_addenda_as_company'
    )
    
    is_cleaner_approved = models.BooleanField(default=False)
    cleaner_approved_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Document
    document_file = models.FileField(upload_to='contract_addenda/', blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_addenda')
    
    def __str__(self):
        return f"Addendum to {self.contract}: {self.title}"


class ContractNotification(models.Model):
    """Notifications related to contracts (expiring soon, terms changed, etc.)."""
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='notifications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contract_notifications')
    
    title = models.CharField(max_length=100)
    message = models.TextField()
    
    # Notification type
    NOTIFICATION_TYPE_CHOICES = [
        ('contract_created', 'Contract Created'),
        ('contract_updated', 'Contract Updated'),
        ('contract_signed', 'Contract Signed'),
        ('contract_expiring', 'Contract Expiring'),
        ('addendum_created', 'Addendum Created'),
        ('addendum_approved', 'Addendum Approved'),
    ]
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Contract Notification: {self.title} for {self.user.get_full_name()}"