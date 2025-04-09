from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from accounts.models import User, CompanyProfile, CleanerProfile
from jobs.models import JobAssignment, TimeTracking


class TaxClass(models.Model):
    """German tax classes (Steuerklasse)."""
    class_number = models.PositiveSmallIntegerField(unique=True)
    description = models.CharField(max_length=255)
    
    def __str__(self):
        return f"Tax Class {self.class_number} - {self.description}"


class SocialSecurity(models.Model):
    """German social security rates."""
    year = models.PositiveIntegerField()
    
    # Rates as percentages (e.g., 14.6 for 14.6%)
    health_insurance_rate = models.DecimalField(max_digits=5, decimal_places=2)
    pension_insurance_rate = models.DecimalField(max_digits=5, decimal_places=2)
    unemployment_insurance_rate = models.DecimalField(max_digits=5, decimal_places=2)
    care_insurance_rate = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Additional rates for specific cases
    additional_health_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    additional_care_rate_no_children = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Income thresholds in Euro
    health_insurance_threshold = models.DecimalField(max_digits=10, decimal_places=2)
    pension_insurance_threshold = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Social Security Rates for {self.year}"


class PayScale(models.Model):
    """Pay scales for cleaners based on experience and region."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Basic hourly rate
    base_hourly_rate = models.DecimalField(max_digits=6, decimal_places=2)
    
    # Experience level adjustments (in percent)
    experience_premium_1 = models.DecimalField(max_digits=5, decimal_places=2, default=5.00,
                                           help_text="Premium % for 1-2 years experience")
    experience_premium_3 = models.DecimalField(max_digits=5, decimal_places=2, default=10.00,
                                           help_text="Premium % for 3-5 years experience")
    experience_premium_5 = models.DecimalField(max_digits=5, decimal_places=2, default=15.00,
                                           help_text="Premium % for 5+ years experience")
    
    # Special conditions premiums (in percent)
    weekend_premium = models.DecimalField(max_digits=5, decimal_places=2, default=25.00,
                                      help_text="Premium % for weekend work")
    night_premium = models.DecimalField(max_digits=5, decimal_places=2, default=25.00,
                                    help_text="Premium % for night work (10pm-6am)")
    holiday_premium = models.DecimalField(max_digits=5, decimal_places=2, default=100.00,
                                      help_text="Premium % for holiday work")
    
    class Meta:
        verbose_name_plural = "Pay Scales"
    
    def __str__(self):
        return self.name
    
    def calculate_hourly_rate(self, experience_years, is_weekend=False, is_night=False, is_holiday=False):
        """Calculate the hourly rate based on experience and conditions."""
        rate = self.base_hourly_rate
        
        # Apply experience premium
        if experience_years >= 5:
            rate += rate * (self.experience_premium_5 / 100)
        elif experience_years >= 3:
            rate += rate * (self.experience_premium_3 / 100)
        elif experience_years >= 1:
            rate += rate * (self.experience_premium_1 / 100)
        
        # Apply condition premiums
        if is_holiday:
            rate += rate * (self.holiday_premium / 100)
        elif is_weekend:
            rate += rate * (self.weekend_premium / 100)
        elif is_night:
            rate += rate * (self.night_premium / 100)
        
        return rate


class Contract(models.Model):
    """Employment contracts for cleaners."""
    cleaner = models.ForeignKey(CleanerProfile, on_delete=models.CASCADE, related_name='contracts')
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='employee_contracts')
    
    # Contract details
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    
    CONTRACT_TYPE_CHOICES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('mini_job', 'Mini-job'),
        ('freelance', 'Freelance/Self-employed'),
    ]
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES)
    
    # Work hours
    weekly_hours = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    # Payment details
    pay_scale = models.ForeignKey(PayScale, on_delete=models.SET_NULL, null=True, blank=True, related_name='contracts')
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                   help_text="Monthly salary for full/part-time employees")
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                   help_text="Hourly rate for hourly employees")
    
    # Tax and social security
    tax_class = models.ForeignKey(TaxClass, on_delete=models.SET_NULL, null=True, blank=True)
    health_insurance_type = models.CharField(max_length=20, choices=[
        ('public', 'Public Health Insurance'),
        ('private', 'Private Health Insurance'),
    ], default='public')
    has_children = models.BooleanField(default=False, help_text="Affects care insurance rate")
    
    # Document references
    contract_document = models.FileField(upload_to='contracts/', blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Contract: {self.cleaner.user.get_full_name()} - {self.get_contract_type_display()}"


class PayPeriod(models.Model):
    """Pay periods for payroll calculations."""
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='pay_periods')
    
    # Period info
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Status
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('processing', 'Processing'),
        ('closed', 'Closed'),
        ('paid', 'Paid'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Payment date
    payment_date = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"Pay Period: {self.start_date} - {self.end_date}"


class Payslip(models.Model):
    """Individual employee payslips."""
    pay_period = models.ForeignKey(PayPeriod, on_delete=models.CASCADE, related_name='payslips')
    cleaner = models.ForeignKey(CleanerProfile, on_delete=models.CASCADE, related_name='payslips')
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, related_name='payslips')
    
    # Gross earnings
    regular_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    weekend_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    night_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    holiday_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2)
    
    # Additional payments
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reimbursements = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Calculated amounts
    gross_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Deductions
    tax_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    health_insurance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pension_insurance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unemployment_insurance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    care_insurance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Net pay
    net_pay = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payslip: {self.cleaner.user.get_full_name()} - {self.pay_period.start_date} to {self.pay_period.end_date}"
    
    def calculate_gross_earnings(self):
        """Calculate gross earnings based on hours and rates."""
        # Base hourly rate
        rate = self.hourly_rate
        
        # Calculate regular earnings
        regular_earnings = self.regular_hours * rate
        
        # Get premium rates from contract pay scale if available
        if self.contract and self.contract.pay_scale:
            pay_scale = self.contract.pay_scale
            experience_years = self.cleaner.experience_years
            
            # Calculate premium hours
            weekend_rate = pay_scale.calculate_hourly_rate(experience_years, is_weekend=True)
            night_rate = pay_scale.calculate_hourly_rate(experience_years, is_night=True)
            holiday_rate = pay_scale.calculate_hourly_rate(experience_years, is_holiday=True)
            
            overtime_rate = rate * Decimal('1.25')  # 25% overtime premium
            
            overtime_earnings = self.overtime_hours * overtime_rate
            weekend_earnings = self.weekend_hours * weekend_rate
            night_earnings = self.night_hours * night_rate
            holiday_earnings = self.holiday_hours * holiday_rate
        else:
            # Use simple premiums if no pay scale is available
            overtime_rate = rate * Decimal('1.25')
            weekend_rate = rate * Decimal('1.25')
            night_rate = rate * Decimal('1.25')
            holiday_rate = rate * Decimal('2.00')
            
            overtime_earnings = self.overtime_hours * overtime_rate
            weekend_earnings = self.weekend_hours * weekend_rate
            night_earnings = self.night_hours * night_rate
            holiday_earnings = self.holiday_hours * holiday_rate
        
        # Calculate total gross earnings
        total = (regular_earnings + overtime_earnings + weekend_earnings + 
                night_earnings + holiday_earnings + self.bonus + self.reimbursements)
        
        return total
    
    def calculate_deductions(self, social_security_rates=None):
        """Calculate deductions based on German regulations."""
        # Get the most recent social security rates if not provided
        if not social_security_rates:
            social_security_rates = SocialSecurity.objects.order_by('-year').first()
        
        if not social_security_rates:
            # If no rates are available, use default values
            health_rate = Decimal('7.3')  # Default employer share
            pension_rate = Decimal('9.3')
            unemployment_rate = Decimal('1.2')
            care_rate = Decimal('1.525')
            if self.contract and not self.contract.has_children:
                care_rate += Decimal('0.35')  # Additional for childless employees
        else:
            # Use rates from the database
            health_rate = social_security_rates.health_insurance_rate / 2  # Split with employer
            pension_rate = social_security_rates.pension_insurance_rate / 2
            unemployment_rate = social_security_rates.unemployment_insurance_rate / 2
            care_rate = social_security_rates.care_insurance_rate / 2
            
            if self.contract and not self.contract.has_children:
                care_rate += social_security_rates.additional_care_rate_no_children
        
        # Calculate deductions
        health_insurance = (self.gross_earnings * health_rate) / 100
        pension_insurance = (self.gross_earnings * pension_rate) / 100
        unemployment_insurance = (self.gross_earnings * unemployment_rate) / 100
        care_insurance = (self.gross_earnings * care_rate) / 100
        
        # Apply a simplified tax calculation (this would be more complex in reality)
        if self.contract and self.contract.tax_class:
            tax_class = self.contract.tax_class.class_number
            if tax_class == 1:
                tax_rate = Decimal('20')
            elif tax_class == 2:
                tax_rate = Decimal('18')
            elif tax_class == 3:
                tax_rate = Decimal('15')
            elif tax_class == 4:
                tax_rate = Decimal('20')
            elif tax_class == 5:
                tax_rate = Decimal('25')
            else:
                tax_rate = Decimal('20')
        else:
            tax_rate = Decimal('20')  # Default tax rate for class 1
        
        tax_deduction = (self.gross_earnings * tax_rate) / 100
        
        # For mini-jobs (450 EUR/month), different rules apply
        if self.contract and self.contract.contract_type == 'mini_job':
            if self.gross_earnings <= Decimal('450'):
                # Employer pays all social security
                health_insurance = Decimal('0')
                pension_insurance = Decimal('0')
                unemployment_insurance = Decimal('0')
                care_insurance = Decimal('0')
                tax_deduction = Decimal('0')
        
        return {
            'tax_deduction': tax_deduction,
            'health_insurance': health_insurance,
            'pension_insurance': pension_insurance,
            'unemployment_insurance': unemployment_insurance,
            'care_insurance': care_insurance,
        }
    
    def save(self, *args, **kwargs):
        # Calculate gross earnings
        self.gross_earnings = self.calculate_gross_earnings()
        
        # Calculate deductions
        deductions = self.calculate_deductions()
        self.tax_deduction = deductions['tax_deduction']
        self.health_insurance = deductions['health_insurance']
        self.pension_insurance = deductions['pension_insurance']
        self.unemployment_insurance = deductions['unemployment_insurance']
        self.care_insurance = deductions['care_insurance']
        
        # Calculate net pay
        total_deductions = (self.tax_deduction + self.health_insurance + 
                           self.pension_insurance + self.unemployment_insurance + 
                           self.care_insurance + self.other_deductions)
        
        self.net_pay = self.gross_earnings - total_deductions
        
        super().save(*args, **kwargs)


class PayslipTimeEntry(models.Model):
    """Links time entries to payslips for reference."""
    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='time_entries')
    time_entry = models.ForeignKey(TimeTracking, on_delete=models.CASCADE, related_name='payslip_entries')
    
    def __str__(self):
        return f"Payslip Time Entry: {self.time_entry} for {self.payslip}"
