from django.urls import path
from . import views

urlpatterns = [
    path('insights/', views.InsightListView.as_view(), name='insight_list'),
    path('insights/generate/', views.generate_insight, name='generate_insight'),
    path('insights/stream/', views.stream_insight, name='stream_insight'),
    path('insights/<int:pk>/read/', views.mark_insight_read, name='insight_read'),
]