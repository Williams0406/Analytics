from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.core.urls')),
    path('api/', include('apps.users.urls')),
    path('api/', include('apps.analytics.urls')),
    path('api/', include('apps.connectors.urls')),
    path('api/', include('apps.insights.urls')),
    path('api/', include('apps.datasets.urls')),
]
