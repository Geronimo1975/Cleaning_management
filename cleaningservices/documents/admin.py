from django.contrib import admin
from .models import DocumentCategory, Document, DocumentAccess, DocumentComment


class DocumentAccessInline(admin.TabularInline):
    model = DocumentAccess
    extra = 0
    readonly_fields = ['accessed_at', 'ip_address']


class DocumentCommentInline(admin.TabularInline):
    model = DocumentComment
    extra = 0


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'document_type', 'access_level', 'created_by', 'created_at')
    list_filter = ('access_level', 'document_type', 'category')
    search_fields = ('title', 'description', 'tags')
    date_hierarchy = 'created_at'
    inlines = [DocumentCommentInline, DocumentAccessInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs


@admin.register(DocumentAccess)
class DocumentAccessAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'accessed_at', 'ip_address')
    list_filter = ('accessed_at',)
    search_fields = ('document__title', 'user__email')
    date_hierarchy = 'accessed_at'
    readonly_fields = ['accessed_at', 'ip_address']


@admin.register(DocumentComment)
class DocumentCommentAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'comment', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('document__title', 'user__email', 'comment')
    date_hierarchy = 'created_at'
