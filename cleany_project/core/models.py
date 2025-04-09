from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
import uuid


class User(AbstractUser):
    """Extended User model with role-based access."""
    
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', _('Customer')
        COMPANY = 'COMPANY', _('Cleaning Company')
        CLEANER = 'CLEANER', _('Cleaner')
        ADMIN = 'ADMIN', _('Administrator')
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    
    def is_customer(self):
        return self.role == self.Role.CUSTOMER
    
    def is_company(self):
        return self.role == self.Role.COMPANY
    
    def is_cleaner(self):
        return self.role == self.Role.CLEANER
    
    def is_admin(self):
        return self.role == self.Role.ADMIN


class Company(models.Model):
    """Model for cleaning companies."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    name = models.CharField(max_length=100)
    description = models.TextField()
    registration_number = models.CharField(max_length=100, unique=True)
    tax_id = models.CharField(max_length=50, unique=True)
    founding_date = models.DateField()
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    website = models.URLField(blank=True)
    
    class Meta:
        verbose_name_plural = "companies"
    
    def __str__(self):
        return self.name


class Cleaner(models.Model):
    """Model for cleaners working with companies."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cleaner_profile')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='cleaners')
    bio = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)
    specializations = models.ManyToManyField('ServiceType', blank=True, related_name='specialized_cleaners')
    tax_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    social_security_number = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company.name if self.company else 'Freelance'}"


class Customer(models.Model):
    """Model for customers seeking cleaning services."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    payment_info = models.TextField(blank=True)  # This would be better managed with a proper payment system
    
    def __str__(self):
        return self.user.get_full_name()


class ServiceType(models.Model):
    """Types of cleaning services offered."""
    name = models.CharField(max_length=100)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=8, decimal_places=2)
    
    def __str__(self):
        return self.name


class Job(models.Model):
    """Model for cleaning jobs."""
    
    class JobType(models.TextChoices):
        CONTRACT = 'CONTRACT', _('Regular Contract')
        PART_TIME = 'PART_TIME', _('One-time Service')
    
    class Status(models.TextChoices):
        OPEN = 'OPEN', _('Open')
        ASSIGNED = 'ASSIGNED', _('Assigned')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='jobs')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_jobs', null=True, blank=True)
    cleaner = models.ForeignKey(Cleaner, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_jobs')
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='jobs')
    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.PART_TIME)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    description = models.TextField()
    location = models.CharField(max_length=255)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    recurring_frequency = models.PositiveIntegerField(default=0, help_text="Days between recurring jobs (0 for non-recurring)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def is_recurring(self):
        return self.recurring_frequency > 0


class JobApplication(models.Model):
    """Model for cleaners applying to jobs."""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    cleaner = models.ForeignKey(Cleaner, on_delete=models.CASCADE, related_name='job_applications')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='job_applications')
    cover_letter = models.TextField()
    price_offer = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('ACCEPTED', 'Accepted'),
            ('REJECTED', 'Rejected'),
        ],
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('job', 'cleaner')
    
    def __str__(self):
        return f"Application by {self.cleaner.user.get_full_name()} for {self.job.title}"


class Document(models.Model):
    """Model for document management."""
    
    class DocumentType(models.TextChoices):
        PROCEDURE = 'PROCEDURE', _('Cleaning Procedure')
        SOLUTION = 'SOLUTION', _('Cleaning Solution')
        CONTRACT = 'CONTRACT', _('Contract')
        REPORT = 'REPORT', _('Report')
        OTHER = 'OTHER', _('Other')
    
    title = models.CharField(max_length=100)
    description = models.TextField()
    file = models.FileField(upload_to='documents/')
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_documents')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='company_documents')
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title


class Timesheet(models.Model):
    """Model for tracking working hours."""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='timesheets')
    cleaner = models.ForeignKey(Cleaner, on_delete=models.CASCADE, related_name='timesheets')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_duration = models.PositiveIntegerField(default=0, help_text="Break duration in minutes")
    notes = models.TextField(blank=True)
    approved_by_company = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('job', 'cleaner', 'date')
    
    def __str__(self):
        return f"Timesheet - {self.cleaner.user.get_full_name()} - {self.date}"
    
    def working_hours(self):
        """Calculate working hours excluding break."""
        import datetime
        start = datetime.datetime.combine(datetime.date.today(), self.start_time)
        end = datetime.datetime.combine(datetime.date.today(), self.end_time)
        if end < start:  # Handle overnight shifts
            end = end + datetime.timedelta(days=1)
        
        duration = end - start
        break_minutes = datetime.timedelta(minutes=self.break_duration)
        working_duration = duration - break_minutes
        
        # Convert to decimal hours
        return working_duration.total_seconds() / 3600


class Payroll(models.Model):
    """Model for payroll processing."""
    cleaner = models.ForeignKey(Cleaner, on_delete=models.CASCADE, related_name='payrolls')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payrolls')
    period_start = models.DateField()
    period_end = models.DateField()
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    social_security_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('APPROVED', 'Approved'),
            ('PAID', 'Paid'),
        ],
        default='DRAFT'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payroll - {self.cleaner.user.get_full_name()} - {self.period_start} to {self.period_end}"


class Rating(models.Model):
    """Model for ratings and reviews."""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='ratings')
    rated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    rated_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)], help_text="Rating from 1 to 5")
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('job', 'rated_by', 'rated_user')
        
    def __str__(self):
        return f"Rating for {self.rated_user.get_full_name()} by {self.rated_by.get_full_name()}"


class Notification(models.Model):
    """Model for system notifications."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()}"
