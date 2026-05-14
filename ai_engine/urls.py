# pyrefly: ignore [missing-import]
from django.urls import path
# pyrefly: ignore [missing-import]
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('assistant/', views.ai_assistant, name='assistant'),
    path('api/chat/', views.ai_chat_api, name='chat_api'),
    path('api/verify-price/', views.ai_price_verify_api, name='verify_price_api'),
    path('api/similar-reports/', views.ai_similar_reports, name='similar_reports'),
]
