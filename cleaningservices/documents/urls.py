from django.urls import path
from . import views

urlpatterns = [
    path('', views.document_list_view, name='document_list'),
    path('<int:document_id>/', views.document_detail_view, name='document_detail'),
    path('<int:document_id>/download/', views.document_download_view, name='document_download'),
    path('upload/', views.upload_document_view, name='upload_document'),
    path('<int:document_id>/edit/', views.edit_document_view, name='edit_document'),
    path('<int:document_id>/delete/', views.delete_document_view, name='delete_document'),
    path('categories/', views.manage_categories_view, name='manage_categories'),
]
