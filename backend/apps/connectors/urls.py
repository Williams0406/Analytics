from django.urls import path
from . import views

urlpatterns = [
    path('connectors/', views.ConnectorListCreateView.as_view(), name='connector_list'),
    path('connectors/catalog/', views.connector_catalog, name='connector_catalog'),
    path('connectors/<int:pk>/', views.ConnectorDetailView.as_view(), name='connector_detail'),
    path('connectors/<int:pk>/sync/', views.sync_connector, name='connector_sync'),
]