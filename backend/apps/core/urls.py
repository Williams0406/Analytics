from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('ping/', views.protected_ping, name='protected_ping'),
]