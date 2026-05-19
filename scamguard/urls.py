"""
URL configuration for ScamGuard AI project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='landing.html'), name='landing'),
    path('accounts/', include('accounts.urls')),
    path('scams/', include('scams.urls')),
    path('vendors/', include('vendors.urls')),
    path('ai/', include('ai_engine.urls')),
    path('analytics/', include('analytics.urls')),
    path('alerts/', include('alerts.urls')),
    path('planner/', include('trip_planner.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Admin site customization
admin.site.site_header = 'ScamGuard AI Administration'
admin.site.site_title = 'ScamGuard AI Admin'
admin.site.index_title = 'Tourism Safety Management'
