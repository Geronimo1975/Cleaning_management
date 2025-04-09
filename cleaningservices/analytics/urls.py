from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Dashboard views
    path('', views.dashboard_view, name='dashboard'),
    path('customize/', views.customize_dashboard_view, name='customize_dashboard'),
    path('save-view/', views.save_dashboard_view, name='save_dashboard_view'),
    path('load-view/<int:view_id>/', views.load_dashboard_view, name='load_dashboard_view'),
    path('delete-view/<int:view_id>/', views.delete_dashboard_view, name='delete_dashboard_view'),
    
    # Data endpoints
    path('api/chart/<str:chart_type>/', views.chart_data_view, name='chart_data'),
    path('api/summary/', views.summary_data_view, name='summary_data'),
    
    # Widgets endpoints
    path('widgets/time_tracking/', views.time_tracking_widget_view, name='time_tracking_widget'),
    path('widgets/contract_status/', views.contract_status_widget_view, name='contract_status_widget'),
    path('widgets/cleaner_performance/', views.cleaner_performance_widget_view, name='cleaner_performance_widget'),
    path('widgets/company_revenue/', views.company_revenue_widget_view, name='company_revenue_widget'),
    path('widgets/customer_satisfaction/', views.customer_satisfaction_widget_view, name='customer_satisfaction_widget'),
    path('widgets/job_statistics/', views.job_statistics_widget_view, name='job_statistics_widget'),
    
    # Reports
    path('reports/', views.reports_list_view, name='reports_list'),
    path('reports/create/', views.create_report_view, name='create_report'),
    path('reports/<int:report_id>/', views.report_detail_view, name='report_detail'),
    path('reports/<int:report_id>/edit/', views.edit_report_view, name='edit_report'),
    path('reports/<int:report_id>/delete/', views.delete_report_view, name='delete_report'),
    path('reports/<int:report_id>/pdf/', views.generate_report_pdf_view, name='generate_report_pdf'),
    path('reports/<int:report_id>/schedule/', views.schedule_report_view, name='schedule_report'),
]