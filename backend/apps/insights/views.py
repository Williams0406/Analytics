import json

from django.http import StreamingHttpResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.analytics.models import MetricSnapshot, RevenueTimeSeries
from apps.datasets.analysis_summary import get_dataset_analysis_summary, get_latest_ready_dataset_import

from .ai_service import get_ai_provider_and_model, get_ai_response, get_ai_stream
from .models import AIInsight
from .serializers import AIInsightSerializer


def build_metrics_context(user):
    from datetime import date

    today = date.today()
    snapshots = MetricSnapshot.objects.filter(user=user, date=today)
    series = RevenueTimeSeries.objects.filter(user=user).order_by('-month')[:3]

    metrics = {}
    for snap in snapshots:
        metrics[snap.metric_type] = {
            'value': float(snap.value),
            'previous': float(snap.previous_value) if snap.previous_value else None,
            'change_percent': snap.change_percent,
            'unit': snap.unit,
        }

    recent_revenue = [
        {
            'month': item.month_label,
            'revenue': float(item.revenue),
            'profit': float(item.profit),
        }
        for item in series
    ]

    return {
        'mode': 'metrics',
        'company': user.company or 'tu empresa',
        'metrics': metrics,
        'recent_revenue': recent_revenue,
    }


def select_relevant_dataset_tables(dataset_import, summary, question=None):
    summary_tables = {table['name']: table for table in summary.get('tables', [])}
    question_lower = (question or '').lower()

    scored = []
    for table in dataset_import.tables.all():
        score = 0
        if table.name.lower() in question_lower:
            score += 4
        for column in table.columns.all():
            if column.name.lower() in question_lower:
                score += 2
        score += min(table.row_count / 1000, 3)
        scored.append((score, table.name, table, summary_tables.get(table.name, {})))

    scored.sort(key=lambda item: (item[0], item[2].row_count), reverse=True)
    selected = [item for item in scored if item[0] > 0][:4]
    if not selected:
        selected = scored[:4]
    return selected


def build_dataset_context(user, question=None):
    dataset_import = get_latest_ready_dataset_import(user)
    if not dataset_import:
        return None

    summary = get_dataset_analysis_summary(dataset_import)
    selected_tables = select_relevant_dataset_tables(dataset_import, summary, question)
    single_table_mode = len(summary.get('tables', [])) == 1
    if single_table_mode:
        selected_tables = selected_tables[:1]

    table_lines = []
    for _, _, table, table_summary in selected_tables:
        columns = []
        for column in table.columns.all()[:12]:
            suffix = ' PK' if column.is_primary_key else ''
            columns.append(f'{column.name} ({column.inferred_type}{suffix})')

        table_line = (
            f'- {table.name}: {table.row_count} filas, {table.column_count} columnas. '
            f'PK: {table.primary_key_name or "no detectada"}. '
            f'Columnas clave: {", ".join(columns)}.'
        )

        top_metric = (table_summary.get('top_numeric_metrics') or [])
        if top_metric:
            metric = top_metric[0]
            table_line += (
                f' Medida destacada: {metric["column"]} '
                f'(sum={metric["sum"]}, mean={metric["mean"]}, max={metric["max"]}).'
            )
            if single_table_mode and len(top_metric) > 1:
                extra_metrics = ', '.join(
                    f'{item["column"]} sum={item["sum"]}'
                    for item in top_metric[1:3]
                )
                table_line += f' Otras medidas: {extra_metrics}.'

        top_dimension = (table_summary.get('top_dimensions') or [])
        if top_dimension:
            dimension = top_dimension[0]
            if dimension.get('top_values'):
                top_value = dimension['top_values'][0]
                table_line += (
                    f' Dimension dominante: {dimension["column"]}={top_value["label"]} '
                    f'({round(top_value["share"] * 100, 1)}%).'
                )
                if single_table_mode and len(dimension['top_values']) > 1:
                    next_values = ', '.join(
                        f'{item["label"]} ({round(item["share"] * 100, 1)}%)'
                        for item in dimension['top_values'][1:4]
                    )
                    table_line += f' Luego siguen: {next_values}.'

        if table_summary.get('time_series'):
            series = table_summary['time_series']
            table_line += (
                f' Serie temporal disponible en {series["date_column"]} '
                f'para seguir {series["value_label"]}.'
            )
            if single_table_mode and table_summary.get('trend_summary'):
                trend = table_summary['trend_summary']
                if trend['change_percent'] is not None:
                    table_line += (
                        f' Cambio observado: {trend["change_percent"]:+.1f}% '
                        f'entre {trend["start_label"]} y {trend["end_label"]}.'
                    )

        quality_watchlist = table_summary.get('quality_watchlist') or []
        if single_table_mode and quality_watchlist:
            quality_bits = ', '.join(
                f'{item["column"]} ({item["completeness_percent"]}% completo)'
                for item in quality_watchlist[:3]
            )
            table_line += f' Riesgos de calidad: {quality_bits}.'

        correlation_pairs = table_summary.get('correlation_pairs') or []
        if single_table_mode and correlation_pairs:
            strongest = correlation_pairs[0]
            table_line += (
                f' Correlacion mas fuerte: {strongest["left_column"]} x {strongest["right_column"]} '
                f'({round(strongest["absolute_correlation"] * 100, 1)}%, {strongest["direction"]}).'
            )

        outlier_watchlist = table_summary.get('outlier_watchlist') or []
        if single_table_mode and outlier_watchlist:
            outlier_bits = ', '.join(
                f'{item["column"]} ({item["outlier_percent"]}% atipico)'
                for item in outlier_watchlist[:2]
            )
            table_line += f' Outliers destacados: {outlier_bits}.'

        text_watchlist = table_summary.get('text_watchlist') or []
        if single_table_mode and text_watchlist:
            text_bits = ', '.join(
                f'{item["column"]} (promedio {item["avg_length"]} chars)'
                for item in text_watchlist[:2]
            )
            table_line += f' Texto util para analisis: {text_bits}.'

        field_highlights = table_summary.get('field_highlights') or []
        if single_table_mode and field_highlights:
            highlight_bits = ', '.join(
                f'{item["column"]} como {item["role"].lower()}'
                for item in field_highlights[:4]
            )
            table_line += f' Campos a priorizar: {highlight_bits}.'

        recommended_analyses = table_summary.get('recommended_analyses') or []
        if single_table_mode and recommended_analyses:
            recommendation_bits = ' '.join(
                f'- {item}'
                for item in recommended_analyses[:3]
            )
            table_line += f' Siguientes analisis sugeridos: {recommendation_bits}'

        sample_rows = table_summary.get('sample_rows') or []
        if single_table_mode and sample_rows:
            table_line += f' Ejemplo de fila: {json.dumps(sample_rows[0], ensure_ascii=False)}.'

        table_lines.append(table_line)

    relationship_lines = [
        (
            f'- {item["source_table_name"]}.{item["source_column_name"]} -> '
            f'{item["target_table_name"]}.{item["target_column_name"]} '
            f'(confianza {round(item["confidence"] * 100)}%).'
        )
        for item in summary.get('relationships', [])[:8]
    ]

    return {
        'mode': 'dataset',
        'company': user.company or 'tu empresa',
        'dataset_import': dataset_import,
        'summary': summary,
        'table_lines': table_lines,
        'relationship_lines': relationship_lines,
        'single_table_mode': single_table_mode,
    }


def build_analysis_context(user, question=None):
    dataset_context = build_dataset_context(user, question)
    if dataset_context:
        return dataset_context
    return build_metrics_context(user)


def build_ai_prompt(context, question=None):
    if context.get('mode') == 'dataset':
        summary = context['summary']
        overview = summary.get('overview', {})
        dashboard = summary.get('dashboard', {})
        table_lines = '\n'.join(context.get('table_lines', []))
        relationship_lines = '\n'.join(context.get('relationship_lines', [])) or '- No se detectaron relaciones.'
        insights_text = '\n'.join(f'- {item}' for item in dashboard.get('insights', []))

        base_prompt = f"""Eres el AI Analytics Engine de Lumiq, especializado en explorar datasets empresariales para equipos de negocio en LATAM.
Responde usando solo el contexto del dataset cargado. Si una respuesta no puede inferirse del resumen disponible, dilo de forma explicita y sugiere el siguiente analisis.

CONTEXTO GENERAL:
- Empresa: {context['company']}
- Dataset: {overview.get('dataset_name', 'dataset importado')}
- Tablas: {overview.get('tables_count', 0)}
- Filas totales: {overview.get('total_rows', 0)}
- Columnas totales: {overview.get('total_columns', 0)}
- Relaciones inferidas: {overview.get('relationships_count', 0)}
- Completitud estimada: {round(overview.get('completeness_ratio', 0) * 100, 1)}%
- Lentes analiticos disponibles: {", ".join(overview.get('available_lenses', [])) or "quality"}

HALLAZGOS PRINCIPALES:
{insights_text or '- No hay hallazgos sintetizados todavia.'}

TABLAS Y CAMPOS RELEVANTES:
{table_lines or '- No hay tablas relevantes seleccionadas.'}

RELACIONES:
{relationship_lines}

INSTRUCCIONES:
- Responde en espanol.
- Prioriza claridad ejecutiva y utilidad practica.
- Cuando mencionas una tabla o columna, usa su nombre exacto.
- Puedes responder dudas sobre schema, relaciones, calidad de datos, volumen, medidas detectadas, categorias, series temporales, correlaciones, outliers y texto.
- Si solo hay una tabla, enfocate en ese dataset y evita responder con generalidades de arquitectura.
- Si solo hay una tabla o un solo archivo, abre la respuesta con 2 o 3 hallazgos concretos del dataset, citando columnas, porcentajes, categorias o cambios temporales cuando existan.
- No des recomendaciones genericas sobre arquitectura, gobierno o integracion salvo que el usuario lo pida.
- Si el usuario pide algo granular que no se conserva en el resumen, dilo sin inventar.
- Maximo 280 palabras.
"""

        if question:
            return base_prompt + f'\nPREGUNTA DEL USUARIO:\n{question}'

        return base_prompt + '\nGenera un resumen ejecutivo del dataset cargado y como empezar a explorarlo.'

    metrics = context.get('metrics', {})
    revenue = context.get('recent_revenue', [])
    company = context.get('company', 'la empresa')

    metrics_text = '\n'.join([
        f"- {key.upper()}: {value['value']} {value['unit']} (cambio: {value['change_percent']:+.1f}%)"
        for key, value in metrics.items()
    ])

    revenue_text = '\n'.join([
        f"- {item['month']}: Revenue ${item['revenue']:,.0f} | Profit ${item['profit']:,.0f}"
        for item in revenue
    ])

    base_prompt = f"""Eres el AI Analytics Engine de Lumiq, especializado en Business Intelligence para empresas LATAM.
Analiza las siguientes metricas reales de {company} y genera insights ejecutivos accionables.

METRICAS ACTUALES:
{metrics_text}

REVENUE RECIENTE:
{revenue_text}

INSTRUCCIONES:
- Se directo y ejecutivo.
- Identifica el insight mas importante primero.
- Da 2 o 3 recomendaciones concretas.
- Usa numeros especificos del contexto.
- Responde en espanol.
- Maximo 250 palabras.
"""

    if question:
        return base_prompt + f'\nPREGUNTA DEL USUARIO:\n{question}'

    return base_prompt + '\nGenera el resumen ejecutivo del estado actual del negocio.'


class InsightListView(generics.ListAPIView):
    serializer_class = AIInsightSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AIInsight.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_insight_read(request, pk):
    try:
        insight = AIInsight.objects.get(pk=pk, user=request.user)
        insight.is_read = True
        insight.save()
        return Response({'message': 'Marcado como leido.'})
    except AIInsight.DoesNotExist:
        return Response({'error': 'No encontrado.'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_insight(request):
    try:
        question = request.data.get('question', None)
        context = build_analysis_context(request.user, question)
        prompt = build_ai_prompt(context, question)
        content = get_ai_response(prompt)

        insight = AIInsight.objects.create(
            user=request.user,
            insight_type='summary' if not question else 'recommendation',
            priority='high',
            title=question or 'Resumen Ejecutivo IA',
            content=content,
            metrics_context=context,
        )

        return Response({'insight': AIInsightSerializer(insight).data})
    except Exception as exc:
        return Response(
            {'error': f'Error al generar insight: {str(exc)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stream_insight(request):
    question = request.data.get('question', None)
    context = build_analysis_context(request.user, question)
    prompt = build_ai_prompt(context, question)

    provider, model = get_ai_provider_and_model()

    def event_stream():
        full_content = ''
        try:
            for token in get_ai_stream(prompt):
                full_content += token
                yield f'data: {json.dumps({"token": token})}\n\n'
        except Exception as exc:
            yield f'data: {json.dumps({"error": str(exc)})}\n\n'
            return

        AIInsight.objects.create(
            user=request.user,
            insight_type='summary' if not question else 'recommendation',
            priority='high',
            title=question or 'Resumen Ejecutivo IA',
            content=full_content,
            metrics_context=context,
        )
        yield f'data: {json.dumps({"done": True, "provider": provider, "model": model})}\n\n'

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
