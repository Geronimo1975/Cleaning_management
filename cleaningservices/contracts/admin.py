from django.contrib import admin
from .models import ContractTemplate, Contract, ContractAddendum, ContractNotification


class ContractAddendumInline(admin.TabularInline):
    model = ContractAddendum
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


class ContractNotificationInline(admin.TabularInline):
    model = ContractNotification
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'created_at')
    list_filter = ('company',)
    search_fields = ('name', 'description', 'company__company_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'company')
        }),
        ('Content', {
            'fields': ('template_content', 'default_terms', 'template_file')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'title', 'cleaner', 'company', 'start_date', 'status')
    list_filter = ('status', 'contract_type', 'is_cleaner_approved', 'is_company_approved')
    search_fields = ('title', 'contract_number', 'cleaner__user__first_name', 'cleaner__user__last_name', 'company__company_name')
    readonly_fields = ('created_at', 'updated_at', 'cleaner_signed_date', 'company_signed_date')
    fieldsets = (
        (None, {
            'fields': ('contract_number', 'title', 'description', 'cleaner', 'company', 'template', 'contract_type')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Working Terms', {
            'fields': ('working_hours_weekly', 'hourly_rate', 'monthly_salary', 'terms_and_conditions', 'contract_file')
        }),
        ('Approval Status', {
            'fields': ('status', 'is_cleaner_approved', 'cleaner_signed_date', 'is_company_approved', 'company_signed_date', 'company_signatory')
        }),
        ('Termination', {
            'fields': ('termination_date', 'termination_reason')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by')
        }),
    )
    inlines = [ContractAddendumInline, ContractNotificationInline]


@admin.register(ContractAddendum)
class ContractAddendumAdmin(admin.ModelAdmin):
    list_display = ('title', 'contract', 'status', 'effective_date')
    list_filter = ('status', 'is_cleaner_approved', 'is_company_approved')
    search_fields = ('title', 'contract__title', 'contract__contract_number')
    readonly_fields = ('created_at', 'updated_at', 'cleaner_approved_date', 'company_approved_date')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'contract', 'effective_date')
        }),
        ('Changes', {
            'fields': ('changes', 'document_file')
        }),
        ('Approval Status', {
            'fields': ('status', 'is_cleaner_approved', 'cleaner_approved_date', 'is_company_approved', 'company_approved_date', 'company_approver')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by')
        }),
    )


@admin.register(ContractNotification)
class ContractNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'contract', 'user', 'notification_type', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('title', 'message', 'contract__title', 'user__email')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('contract', 'user', 'title', 'message', 'notification_type')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )