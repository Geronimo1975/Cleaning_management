from django.urls import path
from . import views

app_name = 'contracts'

urlpatterns = [
    # Contract management
    path('', views.contract_list_view, name='list'),
    path('templates/', views.contract_template_list_view, name='template_list'),
    path('templates/create/', views.create_contract_template_view, name='create_template'),
    path('templates/<int:template_id>/', views.contract_template_detail_view, name='template_detail'),
    path('templates/<int:template_id>/edit/', views.edit_contract_template_view, name='edit_template'),
    path('templates/<int:template_id>/delete/', views.delete_contract_template_view, name='delete_template'),
    
    # Contract operations
    path('create/', views.create_contract_view, name='create'),
    path('<int:contract_id>/', views.contract_detail_view, name='detail'),
    path('<int:contract_id>/edit/', views.edit_contract_view, name='edit'),
    path('<int:contract_id>/delete/', views.delete_contract_view, name='delete'),
    path('<int:contract_id>/approve/', views.approve_contract_view, name='approve'),
    path('<int:contract_id>/reject/', views.reject_contract_view, name='reject'),
    path('<int:contract_id>/sign/', views.sign_contract_view, name='sign'),
    path('<int:contract_id>/terminate/', views.terminate_contract_view, name='terminate'),
    
    # Contract addendum operations
    path('<int:contract_id>/addendum/create/', views.create_addendum_view, name='create_addendum'),
    path('addendum/<int:addendum_id>/', views.addendum_detail_view, name='addendum_detail'),
    path('addendum/<int:addendum_id>/edit/', views.edit_addendum_view, name='edit_addendum'),
    path('addendum/<int:addendum_id>/delete/', views.delete_addendum_view, name='delete_addendum'),
    path('addendum/<int:addendum_id>/approve/', views.approve_addendum_view, name='approve_addendum'),
    path('addendum/<int:addendum_id>/reject/', views.reject_addendum_view, name='reject_addendum'),
]