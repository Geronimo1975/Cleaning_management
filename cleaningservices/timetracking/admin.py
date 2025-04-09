from django.contrib import admin
from .models import WorkSchedule, WorkDay, TimeEntry, TimeEntryApproval, Timesheet, TimesheetEntry


class WorkDayInline(admin.TabularInline):
    model = WorkDay
    extra = 0


class TimeEntryApprovalInline(admin.TabularInline):
    model = TimeEntryApproval
    extra = 0


class TimesheetEntryInline(admin.TabularInline):
    model = TimesheetEntry
    extra = 0


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'cleaner', 'company', 'start_date', 'end_date', 'is_approved')
    list_filter = ('is_approved', 'company', 'schedule_type')
    search_fields = ('name', 'cleaner__user__first_name', 'cleaner__user__last_name', 'company__company_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'cleaner', 'company', 'schedule_type', 'is_approved')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Configuration', {
            'fields': ('hours_per_week', 'approved_by', 'approved_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    inlines = [WorkDayInline]


@admin.register(WorkDay)
class WorkDayAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'date', 'start_time', 'end_time')
    list_filter = ('schedule', 'date', 'day_type')
    search_fields = ('schedule__name', 'schedule__cleaner__user__first_name', 'schedule__cleaner__user__last_name')
    fieldsets = (
        (None, {
            'fields': ('schedule', 'date', 'day_type')
        }),
        ('Hours', {
            'fields': ('start_time', 'end_time', 'break_duration')
        }),
        ('Notes', {
            'fields': ('notes',)
        })
    )


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('cleaner', 'company', 'clock_in_time', 'clock_out_time', 'is_active', 'is_verified')
    list_filter = ('is_active', 'is_verified', 'company')
    search_fields = ('cleaner__user__first_name', 'cleaner__user__last_name', 'company__company_name')
    fieldsets = (
        (None, {
            'fields': ('cleaner', 'company', 'job_assignment', 'job_request', 'workday')
        }),
        ('Time Data', {
            'fields': ('clock_in_time', 'clock_out_time', 'is_active', 'is_verified', 'verified_by')
        }),
        ('Break Data', {
            'fields': ('break_start_time', 'break_end_time', 'break_duration_minutes')
        }),
        ('Location Data', {
            'fields': (
                'clock_in_location_lat', 'clock_in_location_lng', 'clock_in_location_address',
                'clock_out_location_lat', 'clock_out_location_lng', 'clock_out_location_address',
            )
        }),
        ('Notes', {
            'fields': ('notes', 'is_manual_entry')
        })
    )
    inlines = [TimeEntryApprovalInline]

    def total_duration_hours(self, obj):
        return obj.total_duration_hours()
    total_duration_hours.short_description = 'Duration (hours)'


@admin.register(TimeEntryApproval)
class TimeEntryApprovalAdmin(admin.ModelAdmin):
    list_display = ('time_entry', 'approved_by', 'status', 'approval_date')
    list_filter = ('status',)
    search_fields = ('time_entry__cleaner__user__first_name', 'time_entry__cleaner__user__last_name', 'approved_by__first_name', 'approved_by__last_name')
    fieldsets = (
        (None, {
            'fields': ('time_entry', 'approved_by', 'status', 'approval_date')
        }),
        ('Details', {
            'fields': ('notes',)
        })
    )


@admin.register(Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
    list_display = ('cleaner', 'company', 'status', 'total_hours')
    list_filter = ('status', 'company', 'timesheet_type')
    search_fields = ('cleaner__user__first_name', 'cleaner__user__last_name', 'company__company_name')
    fieldsets = (
        (None, {
            'fields': ('cleaner', 'company', 'start_date', 'end_date', 'timesheet_type', 'status')
        }),
        ('Approval', {
            'fields': ('submitted_date', 'approved_by', 'approved_date')
        }),
        ('Hours & Compensation', {
            'fields': ('total_hours', 'regular_hours', 'overtime_hours')
        }),
        ('Notes', {
            'fields': ('notes',)
        })
    )
    inlines = [TimesheetEntryInline]


@admin.register(TimesheetEntry)
class TimesheetEntryAdmin(admin.ModelAdmin):
    list_display = ('timesheet', 'time_entry')
    list_filter = ('timesheet',)
    search_fields = ('timesheet__cleaner__user__first_name', 'timesheet__cleaner__user__last_name')