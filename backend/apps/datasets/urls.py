from django.urls import path

from . import views

urlpatterns = [
    path('datasets/imports/', views.DatasetImportListCreateView.as_view(), name='dataset_imports'),
    path('datasets/imports/latest/', views.latest_dataset_import, name='dataset_import_latest'),
    path('datasets/imports/<int:pk>/', views.DatasetImportDetailView.as_view(), name='dataset_import_detail'),
]
