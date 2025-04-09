from django.urls import path
from . import views

urlpatterns = [
    # Company payroll management
    path('', views.payroll_overview, name='payroll_overview'),
    path('period/create/', views.create_pay_period, name='create_pay_period'),
    path('period/<int:period_id>/', views.pay_period_detail, name='pay_period_detail'),
    path('payslip/<int:payslip_id>/', views.payslip_detail, name='payslip_detail'),
    
    # Contract management
    path('contracts/', views.manage_contracts, name='manage_contracts'),
    path('contracts/create/', views.create_contract, name='create_contract'),
    path('contracts/<int:contract_id>/edit/', views.edit_contract, name='edit_contract'),
    
    # Cleaner payslip views
    path('my-payslips/', views.cleaner_payslips, name='cleaner_payslips'),
    path('my-payslips/<int:payslip_id>/', views.cleaner_payslip_detail, name='cleaner_payslip_detail'),
    
    # Settings
    path('settings/', views.payroll_settings, name='payroll_settings'),
]
