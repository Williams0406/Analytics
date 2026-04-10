from django.urls import path
from . import views

urlpatterns = [
    path('analytics/dashboard/', views.dashboard_payload, name='analytics_dashboard'),
    path('analytics/presentation/', views.presentation_payload, name='analytics_presentation'),
    path('analytics/kpis/', views.kpi_summary, name='kpi_summary'),
    path('analytics/revenue/', views.revenue_chart, name='revenue_chart'),
    path('analytics/overview/', views.analytics_overview, name='analytics_overview'),
]
