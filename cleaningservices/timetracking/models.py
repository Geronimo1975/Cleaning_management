from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User, CleanerProfile, CompanyProfile
from jobs.models import JobRequest, JobAssignment


class WorkSchedule(models.Model):
    """Work schedules for cleaners."""
    cleaner = models.ForeignKey(CleanerProfile, on_delete=models.CASCADE, related_name='work_schedules')
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='employee_schedules', null=True, blank=True)
    
    # Schedule name and period
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Schedule type
    SCHEDULE_TYPE_CHOICES = [
        ('regular', 'Regular Schedule'),
        ('shift', 'Shift Schedule'),
        ('flexible', 'Flexible Hours'),
    ]
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPE_CHOICES, default='regular')
    
    # Working hours configuration 
    hours_per_week = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Approval status
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_schedules')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"Schedule: {self.name} for {self.cleaner.user.get_full_name()}"


class WorkDay(models.Model):
    """Individual work days in a schedule."""
    schedule = models.ForeignKey(WorkSchedule, on_delete=models.CASCADE, related_name='workdays')
    
    # Day details
    date = models.DateField()
    
    # Day type
    DAY_TYPE_CHOICES = [
        ('work', 'Work Day'),
        ('off', 'Day Off'),
        ('vacation', 'Vacation'),
        ('sick', 'Sick Leave'),
        ('holiday', 'Public Holiday'),
    ]
    day_type = models.CharField(max_length=20, choices=DAY_TYPE_CHOICES, default='work')
    
    # Working hours for this day
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    break_duration = models.PositiveIntegerField(default=0, help_text="Break duration in minutes")
    
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['date']
        unique_together = ('schedule', 'date')
    
    def __str__(self):
        return f"Work day: {self.date} - {self.get_day_type_display()}"
    
    def scheduled_hours(self):
        """Calculate scheduled hours for the day."""
        if self.day_type != 'work' or not self.start_time or not self.end_time:
            return 0
        
        import datetime
        start = datetime.datetime.combine(datetime.date.today(), self.start_time)
        end = datetime.datetime.combine(datetime.date.today(), self.end_time)
        
        # Handle overnight shifts
        if end < start:
            end = end + datetime.timedelta(days=1)
        
        duration_minutes = (end - start).total_seconds() / 60
        # Subtract break
        working_minutes = duration_minutes - self.break_duration
        
        return working_minutes / 60  # Convert to hours


class TimeEntry(models.Model):
    """Individual time clock entries for cleaners."""
    cleaner = models.ForeignKey(CleanerProfile, on_delete=models.CASCADE, related_name='timetracking_entries')
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='timetracking_employee_entries', null=True, blank=True)
    
    # Related job (optional)
    job_request = models.ForeignKey(JobRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='timetracking_entries')
    job_assignment = models.ForeignKey(JobAssignment, on_delete=models.SET_NULL, null=True, blank=True, related_name='timetracking_entries')
    workday = models.ForeignKey(WorkDay, on_delete=models.SET_NULL, null=True, blank=True, related_name='time_entries')
    
    # Clock times
    clock_in_time = models.DateTimeField()
    clock_out_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text="Whether this is an active time entry (not clocked out yet)")
    
    # Break tracking
    break_start_time = models.DateTimeField(null=True, blank=True)
    break_end_time = models.DateTimeField(null=True, blank=True)
    break_duration_minutes = models.PositiveIntegerField(default=0)
    
    # Location data
    clock_in_location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_in_location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_in_location_address = models.CharField(max_length=255, blank=True, null=True)
    
    clock_out_location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_out_location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_out_location_address = models.CharField(max_length=255, blank=True, null=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='timetracking_verified_entries')
    verification_date = models.DateTimeField(null=True, blank=True)
    
    # Manual entry flag
    is_manual_entry = models.BooleanField(default=False, help_text="Whether this was manually entered (vs. clocked in real-time)")
    
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-clock_in_time']
        verbose_name = "Time Entry"
        verbose_name_plural = "Time Entries"
    
    def __str__(self):
        return f"Time Entry: {self.cleaner.user.get_full_name()} - {self.clock_in_time.date()}"
    
    def total_duration_minutes(self):
        """Calculate total duration in minutes."""
        if not self.clock_out_time:
            return 0
        
        total_minutes = (self.clock_out_time - self.clock_in_time).total_seconds() / 60
        return total_minutes - self.break_duration_minutes
    
    def total_duration_hours(self):
        """Calculate total duration in hours."""
        return self.total_duration_minutes() / 60
    
    def is_on_break(self):
        """Check if currently on break."""
        return self.break_start_time is not None and self.break_end_time is None
    
    def start_break(self):
        """Start a break."""
        if self.is_active and not self.is_on_break():
            self.break_start_time = timezone.now()
            self.save()
    
    def end_break(self):
        """End a break and calculate duration."""
        if self.is_active and self.is_on_break():
            self.break_end_time = timezone.now()
            break_duration = (self.break_end_time - self.break_start_time).total_seconds() / 60
            self.break_duration_minutes += int(break_duration)
            self.save()
    
    def clock_out(self, latitude=None, longitude=None, address=None):
        """Clock out the user."""
        if self.is_active:
            # End any active break first
            if self.is_on_break():
                self.end_break()
            
            self.clock_out_time = timezone.now()
            self.is_active = False
            self.clock_out_location_lat = latitude
            self.clock_out_location_lng = longitude
            self.clock_out_location_address = address
            self.save()


class TimeEntryApproval(models.Model):
    """Approval records for time entries by managers/supervisors."""
    time_entry = models.OneToOneField(TimeEntry, on_delete=models.CASCADE, related_name='approval')
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approved_time_entries')
    approval_date = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('pending_changes', 'Pending Changes'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Approval: {self.time_entry} - {self.get_status_display()}"


class Timesheet(models.Model):
    """Weekly or monthly timesheet aggregating time entries."""
    cleaner = models.ForeignKey(CleanerProfile, on_delete=models.CASCADE, related_name='timesheets')
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='employee_timesheets', null=True, blank=True)
    
    # Period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Type
    TIMESHEET_TYPE_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
    ]
    timesheet_type = models.CharField(max_length=20, choices=TIMESHEET_TYPE_CHOICES, default='weekly')
    
    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Approval
    submitted_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_timesheets')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Summary data (cached for performance)
    total_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    regular_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        unique_together = ('cleaner', 'start_date', 'end_date')
    
    def __str__(self):
        return f"Timesheet: {self.cleaner.user.get_full_name()} ({self.start_date} to {self.end_date})"
    
    def update_hours(self):
        """Update the hour totals based on linked time entries."""
        from decimal import Decimal
        
        time_entries = TimeEntry.objects.filter(
            cleaner=self.cleaner,
            clock_in_time__date__gte=self.start_date,
            clock_in_time__date__lte=self.end_date,
            is_verified=True
        )
        
        total_hours = sum(entry.total_duration_hours() for entry in time_entries)
        self.total_hours = Decimal(total_hours)
        
        # Calculate regular and overtime hours based on contract terms
        # This is a simplified example - real calculation would depend on contract
        standard_weekly_hours = 40  # This should come from the cleaner's contract
        
        if self.total_hours > standard_weekly_hours:
            self.regular_hours = Decimal(standard_weekly_hours)
            self.overtime_hours = self.total_hours - self.regular_hours
        else:
            self.regular_hours = self.total_hours
            self.overtime_hours = Decimal('0.00')
        
        self.save()


class TimesheetEntry(models.Model):
    """Link between time entries and timesheets."""
    timesheet = models.ForeignKey(Timesheet, on_delete=models.CASCADE, related_name='entries')
    time_entry = models.ForeignKey(TimeEntry, on_delete=models.CASCADE, related_name='timesheet_entries')
    
    class Meta:
        unique_together = ('timesheet', 'time_entry')
    
    def __str__(self):
        return f"Timesheet Entry: {self.time_entry} in {self.timesheet}"


class TimeRecord(models.Model):
    """Model for time records used by analytics."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_records')
    date = models.DateField()
    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    
    # Additional fields
    job_assignment = models.ForeignKey('jobs.JobAssignment', on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-date', '-clock_in']
        
    def __str__(self):
        return f"Time Record: {self.user.get_full_name()} - {self.date}"
    
    def save(self, *args, **kwargs):
        # Calculate duration if clock_out exists
        if self.clock_out and self.clock_in:
            self.duration = self.clock_out - self.clock_in
        super().save(*args, **kwargs)


class Break(models.Model):
    """Model for breaks within time records."""
    time_record = models.ForeignKey(TimeRecord, on_delete=models.CASCADE, related_name='breaks')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    
    class Meta:
        ordering = ['start_time']
        
    def __str__(self):
        return f"Break for {self.time_record}"
    
    def save(self, *args, **kwargs):
        # Calculate duration if end_time exists
        if self.end_time and self.start_time:
            self.duration = self.end_time - self.start_time
        super().save(*args, **kwargs)