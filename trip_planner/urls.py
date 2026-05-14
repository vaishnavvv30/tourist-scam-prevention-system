from django.urls import path
from . import views

app_name = 'trip_planner'

urlpatterns = [
    path('', views.planner_dashboard, name='dashboard'),
    path('create/', views.create_trip, name='create_trip'),
    path('trip/<int:trip_id>/', views.trip_detail, name='trip_detail'),
    path('trip/<int:trip_id>/itinerary/', views.trip_itinerary, name='trip_itinerary'),
    path('trip/<int:trip_id>/budget/', views.trip_budget, name='trip_budget'),
    path('trip/<int:trip_id>/pdf/', views.download_trip_pdf, name='download_trip_pdf'),
]
