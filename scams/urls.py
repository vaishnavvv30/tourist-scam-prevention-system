from django.urls import path
from . import views

app_name = 'scams'

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('report/new/', views.report_create, name='report_create'),
    path('report/<int:pk>/', views.report_detail, name='report_detail'),
    path('report/<int:pk>/vote/', views.vote_report, name='vote_report'),
    path('bill/upload/', views.bill_upload, name='bill_upload'),
    path('bill/<int:pk>/', views.bill_detail, name='bill_detail'),
    path('price-check/', views.price_check, name='price_check'),
    path('heatmap/', views.scam_heatmap, name='heatmap'),
    path('api/map-data/', views.scam_map_data, name='map_data'),
]
