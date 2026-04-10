from django.contrib import admin
from .models import DataConnector, SyncLog


@admin.register(DataConnector)
class DataConnectorAdmin(admin.ModelAdmin):
    list_display = ['user', 'connector_type', 'name', 'status', 'records_synced', 'last_sync']
    list_filter = ['connector_type', 'status']
    search_fields = ['user__email', 'name']


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ['connector', 'status', 'records_processed', 'started_at']
    list_filter = ['status']