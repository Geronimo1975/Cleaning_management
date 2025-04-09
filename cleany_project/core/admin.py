from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Company, Cleaner, Customer, ServiceType, Job, JobApplication,
    Document, Timesheet, Payroll, Rating, Notification
)

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'address', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'address', 'profile_picture')}),
    )


class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'registration_number', 'tax_id', 'founding_date')
    search_fields = ('name', 'registration_number')


class CleanerAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'company', 'experience_years', 'hourly_rate', 'is_available')
    list_filter = ('is_available', 'company')
    search_fields = ('user__first_name', 'user__last_name', 'company__name')
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_email')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'


class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price')
    search_fields = ('name',)


class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'customer', 'company', 'cleaner', 'service_type', 'job_type', 'status', 'start_datetime')
    list_filter = ('status', 'job_type', 'service_type')
    search_fields = ('title', 'description', 'customer__user__first_name', 'customer__user__last_name')
    date_hierarchy = 'start_datetime'


class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'cleaner', 'company', 'price_offer', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('job__title', 'cleaner__user__first_name', 'cleaner__user__last_name')


class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'uploaded_by', 'company', 'is_public', 'created_at')
    list_filter = ('document_type', 'is_public', 'company')
    search_fields = ('title', 'description', 'uploaded_by__first_name', 'uploaded_by__last_name')
    date_hierarchy = 'created_at'


class TimesheetAdmin(admin.ModelAdmin):
    list_display = ('cleaner', 'job', 'date', 'start_time', 'end_time', 'break_duration', 'approved_by_company')
    list_filter = ('approved_by_company', 'date')
    search_fields = ('cleaner__user__first_name', 'cleaner__user__last_name', 'job__title')
    date_hierarchy = 'date'


class PayrollAdmin(admin.ModelAdmin):
    list_display = ('cleaner', 'company', 'period_start', 'period_end', 'net_amount', 'payment_date', 'status')
    list_filter = ('status', 'payment_date')
    search_fields = ('cleaner__user__first_name', 'cleaner__user__last_name', 'company__name')
    date_hierarchy = 'period_end'


class RatingAdmin(admin.ModelAdmin):
    list_display = ('job', 'rated_by', 'rated_user', 'score', 'created_at')
    list_filter = ('score',)
    search_fields = ('comment', 'rated_by__first_name', 'rated_by__last_name', 'rated_user__first_name', 'rated_user__last_name')


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('title', 'message', 'user__first_name', 'user__last_name')
    date_hierarchy = 'created_at'


# Register models
admin.site.register(User, CustomUserAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Cleaner, CleanerAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(ServiceType, ServiceTypeAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(JobApplication, JobApplicationAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Timesheet, TimesheetAdmin)
admin.site.register(Payroll, PayrollAdmin)
admin.site.register(Rating, RatingAdmin)
admin.site.register(Notification, NotificationAdmin)
