from datetime import datetime, timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DataConnector, SyncLog
from .serializers import DataConnectorSerializer, ConnectorCreateSerializer

# Catálogo de conectores disponibles en la plataforma
CONNECTOR_CATALOG = [
    {
        'type': 'stripe',
        'name': 'Stripe',
        'description': 'Revenue, MRR, ARR, churn y pagos',
        'category': 'Finanzas',
        'icon': '💳',
        'available': True,
    },
    {
        'type': 'google_analytics',
        'name': 'Google Analytics 4',
        'description': 'Tráfico, conversiones y comportamiento',
        'category': 'Marketing',
        'icon': '📊',
        'available': True,
    },
    {
        'type': 'meta_ads',
        'name': 'Meta Ads',
        'description': 'ROAS, CPM, alcance y campañas',
        'category': 'Marketing',
        'icon': '📱',
        'available': True,
    },
    {
        'type': 'shopify',
        'name': 'Shopify',
        'description': 'Ventas, productos y clientes',
        'category': 'eCommerce',
        'icon': '🛒',
        'available': True,
    },
    {
        'type': 'hubspot',
        'name': 'HubSpot',
        'description': 'Pipeline, deals y CRM',
        'category': 'Ventas',
        'icon': '🤝',
        'available': False,
    },
    {
        'type': 'postgresql',
        'name': 'PostgreSQL',
        'description': 'Conecta tu propia base de datos',
        'category': 'Base de Datos',
        'icon': '🗄️',
        'available': False,
    },
    {
        'type': 'csv_upload',
        'name': 'CSV Upload',
        'description': 'Sube archivos CSV manualmente',
        'category': 'Manual',
        'icon': '📄',
        'available': True,
    },
    {
        'type': 'google_sheets',
        'name': 'Google Sheets',
        'description': 'Sincroniza hojas de cálculo',
        'category': 'Productividad',
        'icon': '📋',
        'available': False,
    },
]


class ConnectorListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ConnectorCreateSerializer
        return DataConnectorSerializer

    def get_queryset(self):
        return DataConnector.objects.filter(
            user=self.request.user,
            is_active=True,
        ).prefetch_related('sync_logs')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='connected')


class ConnectorDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DataConnectorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DataConnector.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.status = 'disconnected'
        instance.save()
        return Response({'message': f'Conector {instance.name} desconectado.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def connector_catalog(request):
    """Lista todos los conectores disponibles con su estado para el usuario."""
    user_connectors = DataConnector.objects.filter(
        user=request.user,
        is_active=True,
    ).values_list('connector_type', flat=True)

    catalog = []
    for connector in CONNECTOR_CATALOG:
        catalog.append({
            **connector,
            'connected': connector['type'] in user_connectors,
        })

    return Response({'catalog': catalog})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_connector(request, pk):
    """Simula una sincronización del conector (demo)."""
    try:
        connector = DataConnector.objects.get(pk=pk, user=request.user)
    except DataConnector.DoesNotExist:
        return Response({'error': 'Conector no encontrado.'}, status=404)

    # Simular sync exitoso
    connector.last_sync = datetime.now(timezone.utc)
    connector.records_synced += 150
    connector.status = 'connected'
    connector.save()

    SyncLog.objects.create(
        connector=connector,
        records_processed=150,
        status='success',
        finished_at=datetime.now(timezone.utc),
    )

    return Response({
        'message': f'{connector.name} sincronizado correctamente.',
        'records_synced': connector.records_synced,
        'last_sync': connector.last_sync,
    })