from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom user model with role-based access."""
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        CUSTOMER = 'CUSTOMER', _('Customer')
        COMPANY = 'COMPANY', _('Cleaning Company')
        CLEANER = 'CLEANER', _('Cleaner')
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # Added field to identify users who have completed their profile
    is_profile_complete = models.BooleanField(default=False)
    
    # Set email as the required login field instead of username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"


class CustomerProfile(models.Model):
    """Profile for customers who need cleaning services."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Germany')
    
    def __str__(self):
        return f"Customer Profile: {self.user.get_full_name()}"


class CompanyProfile(models.Model):
    """Profile for cleaning companies offering services."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    company_name = models.CharField(max_length=255)
    business_registration_number = models.CharField(max_length=50)
    tax_id = models.CharField(max_length=50)
    description = models.TextField()
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    website = models.URLField(blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Germany')
    
    def __str__(self):
        return f"Company Profile: {self.company_name}"


class CleanerProfile(models.Model):
    """Profile for individual cleaners who perform the jobs."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cleaner_profile')
    company = models.ForeignKey(CompanyProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='cleaners')
    is_freelancer = models.BooleanField(default=False)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    social_security_number = models.CharField(max_length=50, blank=True, null=True)
    experience_years = models.PositiveIntegerField(default=0)
    
    # Cleaner specializations
    SPECIALIZATION_CHOICES = [
        ('residential', 'Residential Cleaning'),
        ('commercial', 'Commercial Cleaning'),
        ('deep', 'Deep Cleaning'),
        ('window', 'Window Cleaning'),
        ('carpet', 'Carpet Cleaning'),
        ('move_in_out', 'Move-in/Move-out Cleaning'),
    ]
    specializations = models.JSONField(default=list)
    
    # Employment type
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
    ]
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        default='full_time',
    )
    
    # availability calendar integration
    availability = models.JSONField(default=dict, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Germany')
    
    def __str__(self):
        return f"Cleaner Profile: {self.user.get_full_name()}"


class Rating(models.Model):
    """Ratings for cleaners or companies."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    rated_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_received')
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'rated_user')
    
    def __str__(self):
        return f"Rating: {self.rating} stars by {self.user.get_full_name()} for {self.rated_user.get_full_name()}"
