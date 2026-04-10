from django.db import models
from django.conf import settings


class AIInsight(models.Model):
    """
    Insight generado por IA para un usuario.
    Cada insight analiza las métricas y genera una narrativa
    ejecutiva con recomendaciones accionables.
    """
    INSIGHT_TYPES = [
        ('summary', 'Resumen Ejecutivo'),
        ('anomaly', 'Anomalía Detectada'),
        ('trend', 'Tendencia'),
        ('recommendation', 'Recomendación'),
        ('forecast', 'Proyección'),
    ]

    PRIORITY_LEVELS = [
        ('high', 'Alta'),
        ('medium', 'Media'),
        ('low', 'Baja'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='insights',
    )
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES, default='summary')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    title = models.CharField(max_length=200)
    content = models.TextField()
    metrics_context = models.JSONField(default=dict)
    is_read = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'AI Insight'
        verbose_name_plural = 'AI Insights'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} | {self.insight_type} | {self.title[:50]}'