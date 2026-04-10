from django.db import models
from django.conf import settings


class DataConnector(models.Model):
    """
    Representa una fuente de datos conectada por el usuario.
    En producción cada tipo tendría su propio OAuth flow.
    """
    CONNECTOR_TYPES = [
        ('stripe', 'Stripe'),
        ('google_analytics', 'Google Analytics 4'),
        ('meta_ads', 'Meta Ads'),
        ('shopify', 'Shopify'),
        ('hubspot', 'HubSpot'),
        ('postgresql', 'PostgreSQL'),
        ('csv_upload', 'CSV Upload'),
        ('google_sheets', 'Google Sheets'),
    ]

    STATUS_CHOICES = [
        ('connected', 'Conectado'),
        ('disconnected', 'Desconectado'),
        ('error', 'Error'),
        ('pending', 'Pendiente'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='connectors',
    )
    connector_type = models.CharField(max_length=30, choices=CONNECTOR_TYPES)
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    config = models.JSONField(default=dict, blank=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    records_synced = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conector'
        verbose_name_plural = 'Conectores'
        ordering = ['-created_at']
        unique_together = ['user', 'connector_type']

    def __str__(self):
        return f'{self.user.email} | {self.connector_type} | {self.status}'


class SyncLog(models.Model):
    """Historial de sincronizaciones de cada conector."""
    connector = models.ForeignKey(
        DataConnector,
        on_delete=models.CASCADE,
        related_name='sync_logs',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    records_processed = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[('success', 'Éxito'), ('failed', 'Fallido'), ('running', 'En progreso')],
        default='running',
    )
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.connector} | {self.status} | {self.started_at}'