from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    path('', views.vendor_list, name='vendor_list'),
    path('<int:pk>/', views.vendor_detail, name='vendor_detail'),
    path('add/', views.vendor_create, name='vendor_create'),
    path('<int:pk>/review/', views.add_review, name='add_review'),
]
