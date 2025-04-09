"""
URL configuration for cleaningservices project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('accounts/', include('accounts.urls')),
    path('jobs/', include('jobs.urls')),
    path('documents/', include('documents.urls', namespace='documents')),
    path('payroll/', include('payroll.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('shop/', include('shop.urls')),
    path('notifications/', include('notifications.urls')),
    path('contracts/', include('contracts.urls')),
    path('timetracking/', include('timetracking.urls')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
