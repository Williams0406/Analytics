from django.contrib import admin
from .models import MetricSnapshot, RevenueTimeSeries


@admin.register(MetricSnapshot)
class MetricSnapshotAdmin(admin.ModelAdmin):
    list_display = ['user', 'metric_type', 'value', 'change_percent', 'date']
    list_filter = ['metric_type', 'date']
    search_fields = ['user__email']


@admin.register(RevenueTimeSeries)
class RevenueTimeSeriesAdmin(admin.ModelAdmin):
    list_display = ['user', 'month', 'revenue', 'expenses', 'profit']
    search_fields = ['user__email']