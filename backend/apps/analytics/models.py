from django.db import models
from django.conf import settings


class MetricSnapshot(models.Model):
    """
    Snapshot diario de métricas clave del negocio.
    Cada usuario/empresa tiene sus propias métricas.
    Preparado para multi-tenancy por usuario.
    """
    METRIC_TYPES = [
        ('revenue', 'Revenue'),
        ('users', 'Usuarios Activos'),
        ('conversion', 'Tasa de Conversión'),
        ('churn', 'Churn Rate'),
        ('mrr', 'MRR'),
        ('arr', 'ARR'),
        ('cac', 'CAC'),
        ('ltv', 'LTV'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='metric_snapshots',
    )
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    value = models.DecimalField(max_digits=15, decimal_places=2)
    previous_value = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True
    )
    date = models.DateField()
    label = models.CharField(max_length=100, blank=True)
    unit = models.CharField(
        max_length=10,
        choices=[('$', 'Dólares'), ('%', 'Porcentaje'), ('#', 'Número')],
        default='$'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Métrica'
        verbose_name_plural = 'Métricas'
        ordering = ['-date']
        unique_together = ['user', 'metric_type', 'date']

    def __str__(self):
        return f'{self.user.email} | {self.metric_type} | {self.date}'

    @property
    def change_percent(self):
        """Calcula el % de cambio respecto al valor anterior."""
        if self.previous_value and self.previous_value != 0:
            change = ((self.value - self.previous_value) / self.previous_value) * 100
            return round(float(change), 2)
        return 0.0


class RevenueTimeSeries(models.Model):
    """
    Serie temporal de revenue mensual para gráficos.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='revenue_series',
    )
    month = models.CharField(max_length=7)   # formato: "2024-01"
    month_label = models.CharField(max_length=10)  # formato: "Ene", "Feb"
    revenue = models.DecimalField(max_digits=15, decimal_places=2)
    expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Revenue Mensual'
        verbose_name_plural = 'Revenue Mensual'
        ordering = ['month']
        unique_together = ['user', 'month']

    def __str__(self):
        return f'{self.user.email} | {self.month}'