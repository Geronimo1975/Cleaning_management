from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Dashboard views
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/customize/', views.customize_dashboard_view, name='customize_dashboard'),
    path('dashboard/save-view/', views.save_dashboard_view, name='save_dashboard_view'),
    path('dashboard/load-view/<int:view_id>/', views.load_dashboard_view, name='load_dashboard_view'),
    path('dashboard/delete-view/<int:view_id>/', views.delete_dashboard_view, name='delete_dashboard_view'),
    
    # Charts and data API
    path('api/chart-data/<str:chart_type>/', views.chart_data_view, name='chart_data'),
    path('api/summary-data/', views.summary_data_view, name='summary_data'),
    
    # Reports
    path('reports/', views.reports_list_view, name='reports_list'),
    path('reports/create/', views.create_report_view, name='create_report'),
    path('reports/<int:report_id>/', views.report_detail_view, name='report_detail'),
    path('reports/<int:report_id>/edit/', views.edit_report_view, name='edit_report'),
    path('reports/<int:report_id>/delete/', views.delete_report_view, name='delete_report'),
    path('reports/<int:report_id>/generate-pdf/', views.generate_report_pdf_view, name='generate_report_pdf'),
    path('reports/<int:report_id>/schedule/', views.schedule_report_view, name='schedule_report'),
    
    # Widgets
    path('widgets/cleaner-performance/', views.cleaner_performance_widget_view, name='cleaner_performance_widget'),
    path('widgets/company-revenue/', views.company_revenue_widget_view, name='company_revenue_widget'),
    path('widgets/job-statistics/', views.job_statistics_widget_view, name='job_statistics_widget'),
    path('widgets/contract-status/', views.contract_status_widget_view, name='contract_status_widget'),
    path('widgets/customer-satisfaction/', views.customer_satisfaction_widget_view, name='customer_satisfaction_widget'),
    path('widgets/time-tracking/', views.time_tracking_widget_view, name='time_tracking_widget'),
]