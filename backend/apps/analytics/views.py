from datetime import date
from decimal import Decimal

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.datasets.analysis_summary import get_dataset_analysis_summary, get_latest_ready_dataset_import

from .models import MetricSnapshot, RevenueTimeSeries
from .serializers import MetricSnapshotSerializer, RevenueTimeSeriesSerializer


def build_field_role_lookup(table_summary):
    role_lookup = {}

    def push_role(column_name, role):
        if not column_name:
            return
        role_lookup.setdefault(column_name, [])
        if role not in role_lookup[column_name]:
            role_lookup[column_name].append(role)

    push_role(table_summary.get('primary_key_name'), 'primary_key')
    push_role(table_summary.get('focus_measure_column'), 'measure')
    push_role(table_summary.get('focus_date_column'), 'date')

    for dimension in table_summary.get('top_dimensions', [])[:2]:
        push_role(dimension.get('column'), 'dimension')

    for issue in table_summary.get('quality_watchlist', [])[:3]:
        push_role(issue.get('column'), 'quality')

    return role_lookup


def build_dataset_context_payload(dataset_import, summary):
    table_summaries = {
        table_summary['name']: table_summary
        for table_summary in summary.get('tables', [])
    }

    tables = []
    for table in sorted(dataset_import.tables.all(), key=lambda item: item.row_count, reverse=True):
        table_summary = table_summaries.get(table.name, {})
        role_lookup = build_field_role_lookup(table_summary)
        fields = [
            {
                'name': column.name,
                'inferred_type': column.inferred_type,
                'is_nullable': column.is_nullable,
                'is_primary_key': column.is_primary_key,
                'uniqueness_ratio': round(float(column.uniqueness_ratio), 4),
                'null_count': column.null_count,
                'sample_values': column.sample_values[:2],
                'roles': role_lookup.get(column.name, []),
            }
            for column in table.columns.all()
        ]

        tables.append({
            'name': table.name,
            'source_file': table.source_file,
            'row_count': table.row_count,
            'column_count': table.column_count,
            'primary_key_name': table.primary_key_name,
            'business_context': table_summary.get('business_context', ''),
            'focus_measure_column': table_summary.get('focus_measure_column', ''),
            'focus_date_column': table_summary.get('focus_date_column', ''),
            'analysis_modes': table_summary.get('analysis_modes', []),
            'recommended_analyses': table_summary.get('recommended_analyses', [])[:3],
            'field_highlights': table_summary.get('field_highlights', [])[:4],
            'null_impact': table_summary.get('null_impact', [])[:3],
            'null_patterns': table_summary.get('null_patterns', [])[:3],
            'change_contribution': table_summary.get('change_contribution', [])[:3],
            'hero_kpi': table_summary.get('hero_kpi'),
            'insight_confidence': table_summary.get('insight_confidence', {}),
            'fields': fields,
        })

    return {
        'dataset_name': dataset_import.name,
        'summary': summary.get('overview', {}),
        'tables': tables,
        'relationships': summary.get('relationships', []),
    }


def seed_demo_data(user):
    today = date.today()

    kpis = [
        {'metric_type': 'mrr', 'value': 12450, 'previous_value': 10800, 'label': 'MRR', 'unit': '$'},
        {'metric_type': 'users', 'value': 1284, 'previous_value': 1150, 'label': 'Usuarios Activos', 'unit': '#'},
        {'metric_type': 'conversion', 'value': 3.8, 'previous_value': 3.2, 'label': 'Conversion', 'unit': '%'},
        {'metric_type': 'churn', 'value': 2.1, 'previous_value': 2.8, 'label': 'Churn Rate', 'unit': '%'},
    ]

    for kpi in kpis:
        MetricSnapshot.objects.get_or_create(
            user=user,
            metric_type=kpi['metric_type'],
            date=today,
            defaults={
                'value': Decimal(str(kpi['value'])),
                'previous_value': Decimal(str(kpi['previous_value'])),
                'label': kpi['label'],
                'unit': kpi['unit'],
            },
        )

    months = [
        ('2024-08', 'Ago', 7200, 4100),
        ('2024-09', 'Sep', 8100, 4300),
        ('2024-10', 'Oct', 8900, 4600),
        ('2024-11', 'Nov', 9800, 5000),
        ('2024-12', 'Dic', 11200, 5400),
        ('2025-01', 'Ene', 10100, 5100),
        ('2025-02', 'Feb', 11500, 5500),
        ('2025-03', 'Mar', 12450, 5800),
    ]

    for month, label, revenue, expenses in months:
        RevenueTimeSeries.objects.get_or_create(
            user=user,
            month=month,
            defaults={
                'month_label': label,
                'revenue': Decimal(str(revenue)),
                'expenses': Decimal(str(expenses)),
                'profit': Decimal(str(revenue - expenses)),
            },
        )


def build_demo_dashboard_payload(user):
    today = date.today()

    if not MetricSnapshot.objects.filter(user=user).exists():
        seed_demo_data(user)

    snapshots = MetricSnapshot.objects.filter(user=user, date=today)
    kpis = []
    for snap in snapshots:
        trend = 'neutral'
        if snap.change_percent > 0:
            trend = 'up'
        elif snap.change_percent < 0:
            trend = 'down'

        if snap.metric_type == 'churn':
            trend = 'down' if snap.change_percent > 0 else 'up'

        kpis.append({
            'metric_type': snap.metric_type,
            'label': snap.label,
            'value': float(snap.value),
            'change_percent': snap.change_percent,
            'unit': snap.unit,
            'trend': trend,
            'caption': 'vs. mes anterior',
        })

    if not RevenueTimeSeries.objects.filter(user=user).exists():
        seed_demo_data(user)

    series = RevenueTimeSeries.objects.filter(user=user).order_by('month')

    return {
        'source': 'demo',
        'headline': 'Lumiq esta mostrando datos demo',
        'subheadline': 'Sube un dataset en Conectores para activar un dashboard basado en tu base real.',
        'dataset_import': None,
        'kpis': kpis,
        'primary_chart': {
            'title': 'Revenue vs Gastos',
            'subtitle': 'Serie demo de 8 meses',
            'data': [
                {'label': item.month_label, 'value': float(item.revenue), 'secondary_value': float(item.profit)}
                for item in series
            ],
            'value_label': 'Revenue',
            'secondary_label': 'Profit',
        },
        'secondary_chart': None,
        'type_distribution': None,
        'insights': [
            'Aun no hay un dataset analizado; esta vista sigue usando metricas de demostracion.',
            'Carga uno o varios CSV o Excel en Conectores para construir un dashboard con tus tablas reales.',
        ],
        'table_spotlights': [],
    }


def build_dataset_dashboard_payload(user):
    dataset_import = get_latest_ready_dataset_import(user)
    if not dataset_import:
        return None

    summary = get_dataset_analysis_summary(dataset_import)
    dashboard = summary.get('dashboard', {})
    return {
        'source': 'dataset',
        'headline': dashboard.get('headline'),
        'subheadline': dashboard.get('subheadline'),
        'dataset_import': {
            'id': dataset_import.id,
            'name': dataset_import.name,
            'created_at': dataset_import.created_at.isoformat(),
            'tables_count': dataset_import.tables_count,
            'relationships_count': dataset_import.relationships_count,
        },
        'kpis': dashboard.get('kpis', []),
        'primary_chart': dashboard.get('primary_chart'),
        'secondary_chart': dashboard.get('secondary_chart'),
        'type_distribution': dashboard.get('type_distribution'),
        'insights': dashboard.get('insights', []),
        'table_spotlights': dashboard.get('table_spotlights', []),
        'overview': summary.get('overview', {}),
        'dataset_context': build_dataset_context_payload(dataset_import, summary),
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_payload(request):
    payload = build_dataset_dashboard_payload(request.user)
    if payload:
        return Response(payload)
    return Response(build_demo_dashboard_payload(request.user))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def presentation_payload(request):
    dataset_import = get_latest_ready_dataset_import(request.user)
    if dataset_import:
        summary = get_dataset_analysis_summary(dataset_import)
        return Response({
            'source': 'dataset',
            'dataset_import': {
                'id': dataset_import.id,
                'name': dataset_import.name,
                'created_at': dataset_import.created_at.isoformat(),
            },
            'title': summary.get('presentation', {}).get('title'),
            'slides': summary.get('presentation', {}).get('slides', []),
            'dataset_context': build_dataset_context_payload(dataset_import, summary),
        })

    demo_dashboard = build_demo_dashboard_payload(request.user)
    return Response({
        'source': 'demo',
        'dataset_import': None,
        'title': 'Lectura ejecutiva demo',
        'slides': [
            {
                'type': 'hero',
                'eyebrow': 'Demo Mode',
                'title': 'Sube un dataset para activar Analytics',
                'subtitle': 'Lumiq puede convertir tu bundle de archivos en una narrativa visual tipo presentacion.',
                'accent_value': 0,
                'accent_label': 'datasets listos',
                'bullets': demo_dashboard['insights'],
            }
        ],
        'dataset_context': None,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def kpi_summary(request):
    payload = build_dataset_dashboard_payload(request.user)
    if payload:
        return Response({
            'source': 'dataset',
            'kpis': payload['kpis'],
            'as_of': payload['dataset_import']['created_at'],
        })

    demo = build_demo_dashboard_payload(request.user)
    return Response({
        'source': 'demo',
        'kpis': demo['kpis'],
        'as_of': date.today().isoformat(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def revenue_chart(request):
    payload = build_dataset_dashboard_payload(request.user)
    if payload and payload.get('primary_chart'):
        primary_chart = payload['primary_chart']
        return Response({
            'source': 'dataset',
            'series': [
                {
                    'month_label': point['label'],
                    'revenue': point['value'],
                    'profit': point.get('secondary_value'),
                }
                for point in primary_chart.get('data', [])
            ],
            'chart': primary_chart,
        })

    if not RevenueTimeSeries.objects.filter(user=request.user).exists():
        seed_demo_data(request.user)

    series = RevenueTimeSeries.objects.filter(user=request.user).order_by('month')
    serializer = RevenueTimeSeriesSerializer(series, many=True)
    return Response({
        'source': 'demo',
        'series': serializer.data,
        'total_revenue': sum(float(item.revenue) for item in series),
        'total_profit': sum(float(item.profit) for item in series),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_overview(request):
    payload = build_dataset_dashboard_payload(request.user)
    if payload:
        return Response({
            'source': 'dataset',
            'overview': payload['overview'],
            'dataset_import': payload['dataset_import'],
            'insights': payload['insights'],
            'table_spotlights': payload['table_spotlights'],
            'dataset_context': payload['dataset_context'],
            'charts': {
                'primary': payload['primary_chart'],
                'secondary': payload['secondary_chart'],
                'type_distribution': payload['type_distribution'],
            },
        })

    if not MetricSnapshot.objects.filter(user=request.user).exists():
        seed_demo_data(request.user)

    today = date.today()
    metrics = MetricSnapshot.objects.filter(user=request.user, date=today)
    serializer = MetricSnapshotSerializer(metrics, many=True)
    return Response({
        'source': 'demo',
        'metrics': serializer.data,
        'generated_at': today.isoformat(),
        'user': request.user.email,
    })
