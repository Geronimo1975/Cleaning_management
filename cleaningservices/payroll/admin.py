from django.contrib import admin
from .models import (
    TaxClass, SocialSecurity, PayScale, Contract, 
    PayPeriod, Payslip, PayslipTimeEntry
)


class PayslipTimeEntryInline(admin.TabularInline):
    model = PayslipTimeEntry
    extra = 0
    readonly_fields = ['time_entry']


@admin.register(TaxClass)
class TaxClassAdmin(admin.ModelAdmin):
    list_display = ('class_number', 'description')
    ordering = ('class_number',)


@admin.register(SocialSecurity)
class SocialSecurityAdmin(admin.ModelAdmin):
    list_display = ('year', 'health_insurance_rate', 'pension_insurance_rate', 
                  'unemployment_insurance_rate', 'care_insurance_rate')
    ordering = ('-year',)


@admin.register(PayScale)
class PayScaleAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_hourly_rate', 'weekend_premium', 'night_premium', 'holiday_premium')
    search_fields = ('name', 'description')


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('cleaner', 'company', 'contract_type', 'start_date', 'end_date', 'is_active')
    list_filter = ('contract_type', 'is_active', 'company')
    search_fields = ('cleaner__user__first_name', 'cleaner__user__last_name', 'company__company_name')
    date_hierarchy = 'start_date'


@admin.register(PayPeriod)
class PayPeriodAdmin(admin.ModelAdmin):
    list_display = ('company', 'start_date', 'end_date', 'status', 'payment_date')
    list_filter = ('status', 'company')
    search_fields = ('company__company_name',)
    date_hierarchy = 'start_date'


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ('cleaner', 'pay_period', 'gross_earnings', 'net_pay', 'is_paid', 'payment_date')
    list_filter = ('is_paid', 'pay_period__company')
    search_fields = ('cleaner__user__first_name', 'cleaner__user__last_name', 'pay_period__company__company_name')
    inlines = [PayslipTimeEntryInline]
    readonly_fields = ('gross_earnings', 'net_pay', 
                      'tax_deduction', 'health_insurance', 
                      'pension_insurance', 'unemployment_insurance', 
                      'care_insurance')
    fieldsets = (
        ('Employee Information', {
            'fields': ('pay_period', 'cleaner', 'contract')
        }),
        ('Hours', {
            'fields': ('regular_hours', 'overtime_hours', 'weekend_hours', 'night_hours', 'holiday_hours')
        }),
        ('Compensation', {
            'fields': ('hourly_rate', 'bonus', 'reimbursements', 'gross_earnings')
        }),
        ('Deductions', {
            'fields': ('tax_deduction', 'health_insurance', 'pension_insurance', 
                      'unemployment_insurance', 'care_insurance', 'other_deductions')
        }),
        ('Payment', {
            'fields': ('net_pay', 'is_paid', 'payment_date', 'payment_reference', 'notes')
        }),
    )


@admin.register(PayslipTimeEntry)
class PayslipTimeEntryAdmin(admin.ModelAdmin):
    list_display = ('payslip', 'time_entry')
    list_filter = ('payslip__pay_period',)
    search_fields = ('payslip__cleaner__user__first_name', 'payslip__cleaner__user__last_name')
