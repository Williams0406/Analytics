from rest_framework import serializers
from .models import MetricSnapshot, RevenueTimeSeries


class MetricSnapshotSerializer(serializers.ModelSerializer):
    change_percent = serializers.ReadOnlyField()

    class Meta:
        model = MetricSnapshot
        fields = [
            'id', 'metric_type', 'value', 'previous_value',
            'change_percent', 'date', 'label', 'unit',
        ]


class RevenueTimeSeriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = RevenueTimeSeries
        fields = ['month', 'month_label', 'revenue', 'expenses', 'profit']


class KpiSummarySerializer(serializers.Serializer):
    """
    Serializer para el resumen de KPIs del dashboard principal.
    Agrupa las métricas más importantes en un solo endpoint.
    """
    metric_type = serializers.CharField()
    label = serializers.CharField()
    value = serializers.DecimalField(max_digits=15, decimal_places=2)
    change_percent = serializers.FloatField()
    unit = serializers.CharField()
    trend = serializers.CharField()  # 'up' | 'down' | 'neutral'