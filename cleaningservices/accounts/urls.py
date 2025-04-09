from django.urls import path
from .views import (
    CustomLoginView, UserRegistrationView, complete_profile_view, 
    profile_view, logout_view
)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('complete-profile/', complete_profile_view, name='complete_profile'),
]
