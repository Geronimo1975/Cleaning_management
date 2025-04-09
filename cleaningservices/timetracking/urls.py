from django.urls import path
from . import views

app_name = 'timetracking'

urlpatterns = [
    # Time entry management
    path('', views.time_entry_list_view, name='list'),
    path('entries/', views.time_entry_list_view, name='entry_list'),
    path('entries/create/', views.create_time_entry_view, name='create_entry'),
    path('entries/select-cleaner/', views.select_cleaner_view, name='select_cleaner'),
    path('entries/<int:entry_id>/', views.time_entry_detail_view, name='entry_detail'),
    path('entries/<int:entry_id>/edit/', views.edit_time_entry_view, name='edit_entry'),
    path('entries/<int:entry_id>/delete/', views.delete_time_entry_view, name='delete_entry'),
    path('entries/<int:entry_id>/verify/', views.verify_time_entry_view, name='verify_entry'),
    
    # Time clock operations
    path('clock-in/', views.clock_in_view, name='clock_in'),
    path('clock-out/', views.clock_out_view, name='clock_out'),
    path('break-start/', views.break_start_view, name='break_start'),
    path('break-end/', views.break_end_view, name='break_end'),
    
    # Timesheet management
    path('timesheets/', views.timesheet_list_view, name='timesheet_list'),
    path('timesheets/create/', views.create_timesheet_view, name='create_timesheet'),
    path('timesheets/select-cleaner/', views.select_cleaner_timesheet_view, name='select_cleaner_timesheet'),
    path('timesheets/<int:timesheet_id>/', views.timesheet_detail_view, name='timesheet_detail'),
    path('timesheets/<int:timesheet_id>/edit/', views.edit_timesheet_view, name='edit_timesheet'),
    path('timesheets/<int:timesheet_id>/delete/', views.delete_timesheet_view, name='delete_timesheet'),
    path('timesheets/<int:timesheet_id>/submit/', views.submit_timesheet_view, name='submit_timesheet'),
    path('timesheets/<int:timesheet_id>/approve/', views.approve_timesheet_view, name='approve_timesheet'),
    path('timesheets/<int:timesheet_id>/reject/', views.reject_timesheet_view, name='reject_timesheet'),
    path('timesheets/<int:timesheet_id>/export/', views.export_timesheet_view, name='export_timesheet'),
    
    # Work schedule management
    path('schedules/', views.work_schedule_list_view, name='schedule_list'),
    path('schedules/create/', views.create_work_schedule_view, name='create_schedule'),
    path('schedules/select-cleaner/', views.select_cleaner_schedule_view, name='select_cleaner_schedule'),
    path('schedules/<int:schedule_id>/', views.work_schedule_detail_view, name='schedule_detail'),
    path('schedules/<int:schedule_id>/edit/', views.edit_work_schedule_view, name='edit_schedule'),
    path('schedules/<int:schedule_id>/delete/', views.delete_work_schedule_view, name='delete_schedule'),
    path('schedules/<int:schedule_id>/approve/', views.approve_work_schedule_view, name='approve_schedule'),
    path('schedules/<int:schedule_id>/workdays/add/', views.add_workday_view, name='add_workday'),
    path('schedules/<int:schedule_id>/workdays/<int:workday_id>/edit/', views.edit_workday_view, name='edit_workday'),
    path('schedules/<int:schedule_id>/workdays/<int:workday_id>/delete/', views.delete_workday_view, name='delete_workday'),
    
    # API endpoints
    path('api/current-status/', views.get_current_status_view, name='get_current_status'),
    path('api/active-entries/', views.get_active_entries_view, name='get_active_entries'),
    path('api/location/', views.get_location_view, name='get_location'),
]