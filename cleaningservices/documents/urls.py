from django.urls import path
from . import views

urlpatterns = [
    # Document management
    path('', views.document_list_view, name='document_list'),
    path('<int:document_id>/', views.document_detail_view, name='document_detail'),
    path('<int:document_id>/download/', views.document_download_view, name='document_download'),
    path('upload/', views.upload_document_view, name='upload_document'),
    path('<int:document_id>/edit/', views.edit_document_view, name='edit_document'),
    path('<int:document_id>/delete/', views.delete_document_view, name='delete_document'),
    path('categories/', views.manage_categories_view, name='manage_categories'),
    
    # Chatbot functionality
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('chatbot/new/', views.new_conversation_view, name='new_conversation'),
    path('chatbot/conversation/<int:conversation_id>/', views.chatbot_conversation_view, name='chatbot_conversation'),
    path('chatbot/document/<int:document_id>/', views.chatbot_document_view, name='chatbot_document'),
    path('chatbot/send-message/', views.send_message_view, name='send_message'),
    path('chatbot/get-messages/<int:conversation_id>/', views.get_conversation_messages_view, name='get_conversation_messages'),
    path('chatbot/close-conversation/<int:conversation_id>/', views.close_conversation_view, name='close_conversation'),
]
