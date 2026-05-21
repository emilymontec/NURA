from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_endpoint, name='test'),
    path('analyze/', views.analyze_endpoint, name='analyze'),
    path('chat/', views.chat_endpoint, name='chat'),
    path('sessions/', views.list_sessions, name='list_sessions'),
    path('sessions/<str:session_id>/', views.get_session_history, name='get_session_history'),
    path('sessions/<str:session_id>/rename/', views.rename_session, name='rename_session'),
    path('sessions/<str:session_id>/delete/', views.delete_session, name='delete_session'),
]
