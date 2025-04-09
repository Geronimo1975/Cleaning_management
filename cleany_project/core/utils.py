from django.utils import timezone
from decimal import Decimal
from .models import Notification


def send_notification(user, title, message, related_job=None):
    """
    Utility function to create a notification for a user.
    
    Args:
        user: User object to send notification to
        title: Title of notification
        message: Body text of notification
        related_job: Optional Job object related to the notification
    """
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        related_job=related_job,
        is_read=False
    )


def calculate_payroll(cleaner, start_date, end_date):
    """
    Calculate payroll amounts for a cleaner for a given period.
    
    Args:
        cleaner: Cleaner object
        start_date: Start date of payroll period
        end_date: End date of payroll period
        
    Returns:
        Dict containing calculated values for payroll
    """
    from .models import Timesheet
    
    # Get approved timesheets for this period
    timesheets = Timesheet.objects.filter(
        cleaner=cleaner,
        date__range=(start_date, end_date),
        approved_by_company=True
    )
    
    # Calculate total regular hours and overtime hours
    total_hours = Decimal('0.00')
    total_regular_hours = Decimal('0.00')
    total_overtime_hours = Decimal('0.00')
    
    for timesheet in timesheets:
        hours = Decimal(str(timesheet.working_hours()))
        total_hours += hours
        
        # In Germany, standard working hours are 8 hours per day
        # Hours beyond that are considered overtime
        if hours > Decimal('8.00'):
            regular_hours = Decimal('8.00')
            overtime_hours = hours - Decimal('8.00')
        else:
            regular_hours = hours
            overtime_hours = Decimal('0.00')
        
        total_regular_hours += regular_hours
        total_overtime_hours += overtime_hours
    
    # Calculate base salary (hourly rate * regular hours)
    hourly_rate = cleaner.hourly_rate
    base_salary = hourly_rate * total_regular_hours
    
    # Calculate overtime pay (hourly rate * 1.25 * overtime hours)
    # German law typically requires a 25% premium for overtime
    overtime_rate = hourly_rate * Decimal('1.25')
    overtime_pay = overtime_rate * total_overtime_hours
    
    # Calculate gross salary
    gross_salary = base_salary + overtime_pay
    
    # Calculate tax deduction (simplified - would be more complex in reality)
    # German income tax ranges from 14% to 45%
    # Using 25% as a simplified average rate
    tax_rate = Decimal('0.25')
    tax_deduction = gross_salary * tax_rate
    
    # Calculate social security contributions (simplified)
    # In Germany, employees pay about 20% of gross salary for social security
    social_security_rate = Decimal('0.20')
    social_security_deduction = gross_salary * social_security_rate
    
    # Calculate net salary
    net_salary = gross_salary - tax_deduction - social_security_deduction
    
    return {
        'total_hours': total_hours,
        'regular_hours': total_regular_hours,
        'overtime_hours': total_overtime_hours,
        'hourly_rate': hourly_rate,
        'overtime_rate': overtime_rate,
        'base_salary': base_salary,
        'overtime_pay': overtime_pay,
        'gross_salary': gross_salary,
        'tax_deduction': tax_deduction,
        'social_security_deduction': social_security_deduction,
        'net_salary': net_salary
    }


def get_time_difference_in_hours(start_time, end_time):
    """
    Calculate the difference between two time objects in hours.
    
    Args:
        start_time: Start time
        end_time: End time
        
    Returns:
        Float representing hours difference
    """
    import datetime
    start = datetime.datetime.combine(datetime.date.today(), start_time)
    end = datetime.datetime.combine(datetime.date.today(), end_time)
    
    # If end time is earlier than start time, assume it's the next day
    if end < start:
        end = end + datetime.timedelta(days=1)
    
    difference = end - start
    return difference.total_seconds() / 3600


def calculate_working_hours(start_time, end_time, break_duration_minutes):
    """
    Calculate working hours excluding break.
    
    Args:
        start_time: Time object for start time
        end_time: Time object for end time
        break_duration_minutes: Break duration in minutes
        
    Returns:
        Float representing working hours
    """
    total_hours = get_time_difference_in_hours(start_time, end_time)
    break_hours = break_duration_minutes / 60
    return max(0, total_hours - break_hours)  # Ensure result is not negative
