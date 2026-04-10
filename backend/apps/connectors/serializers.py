from rest_framework import serializers
from .models import DataConnector, SyncLog


class SyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncLog
        fields = ['id', 'started_at', 'finished_at', 'records_processed', 'status', 'error_message']


class DataConnectorSerializer(serializers.ModelSerializer):
    sync_logs = SyncLogSerializer(many=True, read_only=True)
    connector_type_display = serializers.CharField(
        source='get_connector_type_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = DataConnector
        fields = [
            'id', 'connector_type', 'connector_type_display',
            'name', 'status', 'status_display', 'last_sync',
            'records_synced', 'is_active', 'created_at', 'sync_logs',
        ]
        read_only_fields = ['id', 'created_at', 'last_sync', 'records_synced']


class ConnectorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataConnector
        fields = ['connector_type', 'name', 'config']

    def validate_connector_type(self, value):
        user = self.context['request'].user
        if DataConnector.objects.filter(user=user, connector_type=value).exists():
            raise serializers.ValidationError(
                f'Ya tienes un conector de tipo {value} configurado.'
            )
        return value