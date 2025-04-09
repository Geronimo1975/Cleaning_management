from django.contrib import admin
from .models import (
    ServiceCategory, JobRequest, JobBid, JobAssignment, 
    TimeTracking, JobCompletion
)

class JobBidInline(admin.TabularInline):
    model = JobBid
    extra = 0

class TimeTrackingInline(admin.TabularInline):
    model = TimeTracking
    extra = 0
    readonly_fields = ['total_minutes']

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)

@admin.register(JobRequest)
class JobRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'customer', 'service_category', 'job_type', 'status', 'created_at')
    list_filter = ('status', 'job_type', 'service_category')
    search_fields = ('title', 'description', 'customer__user__email', 'customer__user__first_name')
    date_hierarchy = 'created_at'
    inlines = [JobBidInline]

@admin.register(JobBid)
class JobBidAdmin(admin.ModelAdmin):
    list_display = ('job_request', 'company', 'price', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('job_request__title', 'company__company_name')
    date_hierarchy = 'created_at'

@admin.register(JobAssignment)
class JobAssignmentAdmin(admin.ModelAdmin):
    list_display = ('job_request', 'company', 'cleaner', 'status', 'scheduled_start')
    list_filter = ('status',)
    search_fields = ('job_request__title', 'company__company_name', 'cleaner__user__email')
    date_hierarchy = 'scheduled_start'
    inlines = [TimeTrackingInline]

@admin.register(TimeTracking)
class TimeTrackingAdmin(admin.ModelAdmin):
    list_display = ('cleaner', 'assignment', 'clock_in', 'clock_out', 'total_minutes', 'status')
    list_filter = ('status',)
    search_fields = ('cleaner__user__email', 'cleaner__user__first_name', 'assignment__job_request__title')
    date_hierarchy = 'clock_in'
    readonly_fields = ['total_minutes']

@admin.register(JobCompletion)
class JobCompletionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'completed_at', 'tasks_completed', 'customer_rating')
    list_filter = ('tasks_completed',)
    search_fields = ('assignment__job_request__title',)
    date_hierarchy = 'completed_at'
