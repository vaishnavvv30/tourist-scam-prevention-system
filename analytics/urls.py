from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_overview, name='overview'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('api/charts/', views.analytics_api, name='charts_api'),
]
