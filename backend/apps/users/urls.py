from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from . import views

urlpatterns = [
    # ─── Auth ──────────────────────────────────────────────────────
    path('auth/login/', views.LumiqTokenObtainPairView.as_view(), name='login'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # ─── Perfil ────────────────────────────────────────────────────
    path('auth/profile/', views.ProfileView.as_view(), name='profile'),
    path('auth/change-password/', views.change_password, name='change_password'),
]