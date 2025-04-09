from django.contrib import admin
from .models import (
    DocumentCategory, Document, DocumentAccess, DocumentComment,
    ChatConversation, ChatMessage
)


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


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ['timestamp', 'is_bot']
    fields = ['message', 'is_bot', 'timestamp']


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'document', 'created_at', 'message_count', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'user__email', 'document__title')
    date_hierarchy = 'created_at'
    inlines = [ChatMessageInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('get_conversation_title', 'get_user', 'is_bot', 'truncated_message', 'timestamp')
    list_filter = ('is_bot', 'timestamp')
    search_fields = ('message', 'conversation__title', 'conversation__user__email')
    date_hierarchy = 'timestamp'
    filter_horizontal = ('referenced_documents',)
    
    def get_conversation_title(self, obj):
        return obj.conversation.title
    get_conversation_title.short_description = 'Conversation'
    
    def get_user(self, obj):
        return obj.conversation.user.email
    get_user.short_description = 'User'
    
    def truncated_message(self, obj):
        if len(obj.message) > 50:
            return f"{obj.message[:50]}..."
        return obj.message
    truncated_message.short_description = 'Message'
