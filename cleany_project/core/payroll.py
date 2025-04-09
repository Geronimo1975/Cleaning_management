"""
German Payroll Calculation Logic

This module contains functions for calculating payroll amounts according to German labor laws.
Note: This is a simplified version and doesn't cover all aspects of German payroll regulations.
For production use, consider using specialized payroll software or consulting with tax professionals.
"""

from decimal import Decimal
import calendar
from datetime import datetime, timedelta


def calculate_income_tax(gross_income, tax_class, children=0, church_tax=False):
    """
    Calculate approximate income tax based on German income tax system.
    This is a simplified calculation and doesn't include all factors.
    
    Args:
        gross_income: Monthly gross income in EUR
        tax_class: German tax class (1-6)
        children: Number of children for tax relief
        church_tax: Whether church tax applies
        
    Returns:
        Approximate income tax amount
    """
    # Convert monthly to annual income
    annual_income = gross_income * Decimal('12')
    
    # Basic tax-free allowance for 2023 (changes yearly)
    basic_allowance = Decimal('10908')
    
    # Adjust for tax class (simplified)
    if tax_class == 3:
        basic_allowance *= Decimal('2')
    elif tax_class == 5:
        basic_allowance *= Decimal('0.5')
    
    # Adjust for children (simplified)
    child_allowance = Decimal('4194') * Decimal(str(children))
    
    # Calculate taxable income
    taxable_income = max(Decimal('0'), annual_income - basic_allowance - child_allowance)
    
    # Progressive tax calculation (simplified 2023 rates)
    if taxable_income <= Decimal('0'):
        tax = Decimal('0')
    elif taxable_income <= Decimal('10908'):
        tax = Decimal('0')
    elif taxable_income <= Decimal('15999'):
        # First progressive zone
        y = (taxable_income - Decimal('10909')) / Decimal('10000')
        tax = (Decimal('1400') * y + Decimal('932.82')) * y
    elif taxable_income <= Decimal('62809'):
        # Second progressive zone
        z = (taxable_income - Decimal('15999')) / Decimal('10000')
        tax = (Decimal('2397') * z + Decimal('1672.56')) * z + Decimal('966.53')
    elif taxable_income <= Decimal('277825'):
        # First linear zone
        tax = Decimal('0.42') * taxable_income - Decimal('9972.98')
    else:
        # Second linear zone
        tax = Decimal('0.45') * taxable_income - Decimal('18307.73')
    
    # Add church tax if applicable (8-9% depending on state, using 9%)
    if church_tax:
        church_tax_amount = tax * Decimal('0.09')
        tax += church_tax_amount
    
    # Convert back to monthly amount
    monthly_tax = tax / Decimal('12')
    
    return monthly_tax


def calculate_social_contributions(gross_income, year=None):
    """
    Calculate German social security contributions.
    
    Args:
        gross_income: Monthly gross income in EUR
        year: Year for which to calculate (defaults to current year)
        
    Returns:
        Dict with different social security contributions
    """
    if year is None:
        year = datetime.now().year
    
    # 2023 thresholds in EUR (these change annually)
    if year == 2023:
        health_threshold = Decimal('59850') / Decimal('12')  # Monthly
        pension_threshold = Decimal('87600') / Decimal('12')  # Monthly
        unemployment_threshold = Decimal('87600') / Decimal('12')  # Monthly
        ltc_threshold = Decimal('59850') / Decimal('12')  # Monthly
    else:
        # Default to 2023 values if year not specified
        health_threshold = Decimal('59850') / Decimal('12')
        pension_threshold = Decimal('87600') / Decimal('12')
        unemployment_threshold = Decimal('87600') / Decimal('12')
        ltc_threshold = Decimal('59850') / Decimal('12')
    
    # Calculate health insurance (employer and employee each pay 7.3%)
    health_base = min(gross_income, health_threshold)
    health_contribution = health_base * Decimal('0.073')
    
    # Calculate additional health insurance contribution (employee only, ~1.3%)
    additional_health = health_base * Decimal('0.013')
    
    # Calculate pension insurance (employer and employee each pay 9.3%)
    pension_base = min(gross_income, pension_threshold)
    pension_contribution = pension_base * Decimal('0.093')
    
    # Calculate unemployment insurance (employer and employee each pay 1.2%)
    unemployment_base = min(gross_income, unemployment_threshold)
    unemployment_contribution = unemployment_base * Decimal('0.012')
    
    # Calculate long-term care insurance (employer and employee pay approx. 1.525% each)
    # Childless employees over 23 pay an additional 0.35%
    ltc_base = min(gross_income, ltc_threshold)
    ltc_contribution = ltc_base * Decimal('0.01525')
    
    # Calculate total employee contribution
    total_contribution = (
        health_contribution + 
        additional_health + 
        pension_contribution + 
        unemployment_contribution + 
        ltc_contribution
    )
    
    return {
        'health_insurance': health_contribution,
        'additional_health': additional_health,
        'pension_insurance': pension_contribution,
        'unemployment_insurance': unemployment_contribution,
        'long_term_care': ltc_contribution,
        'total': total_contribution
    }


def calculate_net_income(gross_income, tax_class=1, children=0, church_tax=False):
    """
    Calculate net income from gross income after tax and social contributions.
    
    Args:
        gross_income: Monthly gross income in EUR
        tax_class: German tax class (1-6)
        children: Number of children for tax relief
        church_tax: Whether church tax applies
        
    Returns:
        Net income amount
    """
    # Calculate income tax
    income_tax = calculate_income_tax(gross_income, tax_class, children, church_tax)
    
    # Calculate social security contributions
    social_contributions = calculate_social_contributions(gross_income)
    total_social = social_contributions['total']
    
    # Calculate net income
    net_income = gross_income - income_tax - total_social
    
    return {
        'gross_income': gross_income,
        'income_tax': income_tax,
        'social_contributions': social_contributions,
        'net_income': net_income
    }


def calculate_working_days(year, month):
    """
    Calculate the number of working days in a month (excluding weekends and German holidays).
    
    Args:
        year: Year (e.g., 2023)
        month: Month (1-12)
        
    Returns:
        Number of working days
    """
    # Get all days in the month
    num_days = calendar.monthrange(year, month)[1]
    working_days = 0
    
    for day in range(1, num_days + 1):
        date = datetime(year, month, day)
        # Check if the day is a weekday (0=Monday, 6=Sunday)
        if date.weekday() < 5:  # Monday to Friday
            # Check if it's not a German holiday (simplified)
            if not is_german_holiday(date):
                working_days += 1
    
    return working_days


def is_german_holiday(date):
    """
    Check if a date is a German national holiday.
    Note: This is simplified and only includes national holidays, not state-specific ones.
    
    Args:
        date: datetime object
        
    Returns:
        Boolean indicating if it's a holiday
    """
    year = date.year
    month = date.month
    day = date.day
    
    # Fixed holidays
    if (month == 1 and day == 1) or  # New Year's Day
       (month == 5 and day == 1) or  # Labor Day
       (month == 10 and day == 3) or  # German Unity Day
       (month == 12 and day == 25) or  # Christmas Day
       (month == 12 and day == 26):  # St. Stephen's Day
        return True
    
    # Calculate Easter Sunday (simplified algorithm)
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    easter_month = (h + l - 7 * m + 114) // 31
    easter_day = ((h + l - 7 * m + 114) % 31) + 1
    easter_date = datetime(year, easter_month, easter_day)
    
    # Good Friday (Easter Sunday - 2 days)
    good_friday = easter_date - timedelta(days=2)
    if date.month == good_friday.month and date.day == good_friday.day:
        return True
    
    # Easter Monday (Easter Sunday + 1 day)
    easter_monday = easter_date + timedelta(days=1)
    if date.month == easter_monday.month and date.day == easter_monday.day:
        return True
    
    # Ascension Day (Easter Sunday + 39 days)
    ascension = easter_date + timedelta(days=39)
    if date.month == ascension.month and date.day == ascension.day:
        return True
    
    # Whit Monday (Easter Sunday + 50 days)
    whit_monday = easter_date + timedelta(days=50)
    if date.month == whit_monday.month and date.day == whit_monday.day:
        return True
    
    return False


def calculate_overtime_pay(base_hourly_rate, overtime_hours, overtime_factor=1.25):
    """
    Calculate overtime pay with German overtime regulations.
    
    Args:
        base_hourly_rate: Regular hourly rate in EUR
        overtime_hours: Number of overtime hours
        overtime_factor: Multiplier for overtime (typically 1.25 or 1.5)
        
    Returns:
        Overtime pay amount
    """
    # German labor law doesn't mandate overtime premiums, but
    # many collective agreements specify 25-50% premium
    overtime_rate = base_hourly_rate * Decimal(str(overtime_factor))
    overtime_pay = overtime_rate * Decimal(str(overtime_hours))
    
    return {
        'base_hourly_rate': base_hourly_rate,
        'overtime_rate': overtime_rate,
        'overtime_hours': overtime_hours,
        'overtime_pay': overtime_pay
    }


def calculate_vacation_entitlement(employment_duration_years, weekly_working_days=5):
    """
    Calculate vacation entitlement according to German labor law.
    
    Args:
        employment_duration_years: Years of employment
        weekly_working_days: Number of working days per week
        
    Returns:
        Number of vacation days per year
    """
    # Minimum vacation entitlement in Germany is 20 working days (based on 5-day work week)
    # Many employers offer more (24-30 days)
    base_entitlement = 20
    
    # Additional days based on seniority (not mandated by law, but common practice)
    if employment_duration_years >= 5:
        additional_days = 2
    elif employment_duration_years >= 10:
        additional_days = 5
    else:
        additional_days = 0
    
    # Total entitlement
    total_days = base_entitlement + additional_days
    
    # Adjust for work schedule different from 5 days/week
    if weekly_working_days != 5:
        total_days = total_days * weekly_working_days / 5
    
    return int(total_days)
