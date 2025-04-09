from django.urls import path
from . import views

urlpatterns = [
    # Job listing and details
    path('', views.job_list_view, name='job_list'),
    path('new/', views.create_job_request_view, name='create_job'),
    path('<int:job_id>/', views.job_detail_view, name='job_detail'),
    
    # Bid management
    path('<int:job_id>/bids/', views.manage_bids_view, name='manage_bids'),
    
    # Assignment
    path('<int:job_id>/bid/<int:bid_id>/assign/', views.assign_cleaner_view, name='assign_cleaner'),
    
    # Time tracking
    path('time-tracking/history/', views.time_tracking_history_view, name='time_tracking_history'),
]
