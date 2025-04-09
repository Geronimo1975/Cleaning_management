from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User, CustomerProfile, CompanyProfile, CleanerProfile


class ServiceCategory(models.Model):
    """Categories of cleaning services offered."""
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class")
    
    class Meta:
        verbose_name_plural = "Service Categories"
    
    def __str__(self):
        return self.name


class JobRequest(models.Model):
    """Cleaning job requests created by customers."""
    # Basic information
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='job_requests')
    service_category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Location details
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Germany')
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Job details
    area_size = models.PositiveIntegerField(help_text="Size in square meters")
    estimated_duration = models.PositiveIntegerField(help_text="Estimated duration in hours")
    
    # Job type and scheduling
    JOB_TYPE_CHOICES = [
        ('one_time', 'One-time Service'),
        ('recurring', 'Recurring Service'),
        ('contract', 'Contract Service'),
    ]
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    
    # For one-time and initial recurring services
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    
    # For recurring services
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
    ]
    recurring_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, blank=True, null=True)
    
    # For contract services
    contract_start_date = models.DateField(blank=True, null=True)
    contract_end_date = models.DateField(blank=True, null=True)
    
    # Budget and payment details
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    
    # Status tracking
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Special requirements
    special_requirements = models.TextField(blank=True, null=True)
    supply_requirements = models.TextField(blank=True, null=True, help_text="Any cleaning supplies required")
    
    def __str__(self):
        return f"{self.title} - {self.customer.user.get_full_name()}"


class JobBid(models.Model):
    """Bids submitted by cleaning companies for job requests."""
    job_request = models.ForeignKey(JobRequest, on_delete=models.CASCADE, related_name='bids')
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='bids')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_hours = models.PositiveIntegerField()
    message = models.TextField()
    can_start_at = models.DateTimeField()
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Bid by {self.company.company_name} for {self.job_request.title}"


class JobAssignment(models.Model):
    """Assignment of a cleaner to a job."""
    job_request = models.OneToOneField(JobRequest, on_delete=models.CASCADE, related_name='assignment')
    bid = models.OneToOneField(JobBid, on_delete=models.CASCADE, related_name='assignment', null=True, blank=True)
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='job_assignments')
    cleaner = models.ForeignKey(CleanerProfile, on_delete=models.CASCADE, related_name='job_assignments')
    
    # Scheduling details (can be different from the job request preferred dates)
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    
    # Status tracking
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Assignment: {self.cleaner.user.get_full_name()} for {self.job_request.title}"


class TimeTracking(models.Model):
    """Time tracking for job assignments."""
    assignment = models.ForeignKey(JobAssignment, on_delete=models.CASCADE, related_name='time_entries')
    cleaner = models.ForeignKey(CleanerProfile, on_delete=models.CASCADE, related_name='time_entries')
    
    # Clock in/out times
    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(null=True, blank=True)
    
    # Break tracking
    break_start = models.DateTimeField(null=True, blank=True)
    break_end = models.DateTimeField(null=True, blank=True)
    
    # Location verification
    clock_in_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_in_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_out_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_out_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    total_minutes = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    # Status and verification
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('disputed', 'Disputed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_time_entries')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Time Entry for {self.cleaner.user.get_full_name()} on {self.clock_in.date()}"
    
    def calculate_duration(self):
        """Calculate total working time in minutes, excluding breaks."""
        if not self.clock_out:
            return None
        
        total_seconds = (self.clock_out - self.clock_in).total_seconds()
        
        # Subtract break time if applicable
        if self.break_start and self.break_end:
            break_seconds = (self.break_end - self.break_start).total_seconds()
            total_seconds -= break_seconds
        
        return int(total_seconds / 60)  # Convert to minutes


class JobCompletion(models.Model):
    """Records job completion details."""
    assignment = models.OneToOneField(JobAssignment, on_delete=models.CASCADE, related_name='completion')
    completed_at = models.DateTimeField()
    
    # Job details verification
    tasks_completed = models.BooleanField(default=False)
    customer_signature = models.TextField(blank=True, null=True)  # Store signature data
    cleaner_signature = models.TextField(blank=True, null=True)  # Store signature data
    
    # Customer feedback
    customer_rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    customer_feedback = models.TextField(blank=True, null=True)
    
    # Any issues reported
    issues_reported = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Completion for {self.assignment.job_request.title}"
