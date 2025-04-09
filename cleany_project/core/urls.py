from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path('', views.HomeView.as_view(), name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Profile and Registration
    path('profile/', views.profile_view, name='profile'),
    path('register/company/', views.company_registration, name='company_registration'),
    path('register/cleaner/', views.cleaner_registration, name='cleaner_registration'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/customer/', views.customer_dashboard, name='customer_dashboard'),
    path('dashboard/company/', views.company_dashboard, name='company_dashboard'),
    path('dashboard/cleaner/', views.cleaner_dashboard, name='cleaner_dashboard'),
    
    # Jobs
    path('jobs/', views.JobListView.as_view(), name='job_list'),
    path('jobs/create/', views.create_job, name='job_create'),
    path('jobs/<uuid:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('jobs/<uuid:job_id>/apply/', views.apply_to_job, name='job_apply'),
    path('jobs/<uuid:job_id>/start/', views.start_job, name='job_start'),
    path('jobs/<uuid:job_id>/complete/', views.complete_job, name='job_complete'),
    path('jobs/<uuid:job_id>/rate/', views.rate_job, name='job_rate'),
    
    # Job Applications
    path('application/<int:application_id>/accept/', views.accept_application, name='accept_application'),
    path('application/<int:application_id>/reject/', views.reject_application, name='reject_application'),
    
    # Timesheets
    path('timesheets/', views.timesheet_list, name='timesheet_list'),
    path('timesheets/create/', views.create_timesheet, name='timesheet_create'),
    path('timesheets/create/<uuid:job_id>/', views.create_timesheet, name='timesheet_create_for_job'),
    path('timesheets/<int:timesheet_id>/approve/', views.approve_timesheet, name='approve_timesheet'),
    
    # Documents
    path('documents/', views.document_list, name='document_list'),
    path('documents/upload/', views.document_upload, name='document_upload'),
    path('documents/<int:document_id>/', views.document_detail, name='document_detail'),
    
    # Payroll
    path('payroll/', views.payroll_list, name='payroll_list'),
    path('payroll/create/', views.create_payroll, name='payroll_create'),
    path('payroll/<int:payroll_id>/', views.payroll_detail, name='payroll_detail'),
    
    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
]
