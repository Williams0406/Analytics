import json
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal

from django.http import StreamingHttpResponse
from django.db import models as django_models
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.analytics.models import MetricSnapshot, RevenueTimeSeries
from apps.datasets.analysis_summary import (
    build_combo_story_chart,
    build_relationship_sankey_chart,
    build_story_payload as build_dataset_story_payload,
    build_structure_chart,
    get_dataset_analysis_summary,
    get_latest_ready_dataset_import,
    make_chart_slide,
)
from apps.datasets.story_engine import (
    build_benchmark_story_slide,
    build_change_contribution_story_slide,
    build_dimension_story_slide,
    build_discovery_story_slide,
    build_quality_story_slide,
    build_relationship_story_slide,
    build_time_story_slide,
)

from .ai_service import get_ai_provider_and_model, get_ai_response
from .models import AIInsight
from .serializers import AIInsightSerializer


TIME_QUESTION_HINTS = {
    'tiempo', 'temporal', 'tendencia', 'trend', 'fecha', 'serie', 'series',
    'mes', 'meses', 'month', 'periodo', 'periodos', 'forecast', 'proyeccion',
    'proyecciones', 'evoluciona', 'evolucion',
}
QUALITY_QUESTION_HINTS = {
    'calidad', 'quality', 'nulo', 'nulos', 'faltante', 'faltantes', 'missing',
    'completitud', 'completo', 'incompleto', 'riesgo', 'riesgos', 'outlier',
    'outliers', 'anomalia', 'anomalias', 'alerta', 'alertas',
}
RELATIONSHIP_QUESTION_HINTS = {
    'relacion', 'relaciones', 'correlacion', 'correlaciones', 'driver',
    'drivers', 'causa', 'causas', 'causalidad', 'explica', 'explican',
    'impacta', 'impactan',
}
SEGMENT_QUESTION_HINTS = {
    'segmento', 'segmentos', 'categoria', 'categorias', 'region', 'regiones',
    'mix', 'distribucion', 'benchmark', 'benchmarks', 'dimension',
    'dimensiones', 'canal', 'canales', 'pais', 'paises',
}
STRUCTURE_QUESTION_HINTS = {
    'tabla', 'tablas', 'schema', 'esquema', 'estructura', 'estructural',
    'columna', 'columnas', 'campo', 'campos', 'nucleo', 'operativo',
    'modelo', 'modelado',
}


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
    summary_tables = {table['name']: table for table in summary.get('tables', [])}
    selected_tables = select_relevant_dataset_tables(dataset_import, summary, question)
    single_table_mode = len(summary.get('tables', [])) == 1
    if single_table_mode:
        selected_tables = selected_tables[:1]
    selected_table_names = [table.name for _, _, table, _ in selected_tables]
    selected_table_summaries = [
        summary_tables[name]
        for name in selected_table_names
        if name in summary_tables
    ]

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
        'selected_table_names': selected_table_names,
        'selected_table_summaries': selected_table_summaries,
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


def extract_json_payload(raw_text):
    if not raw_text:
        return None

    cleaned = raw_text.strip()
    fenced_match = re.search(r'```(?:json)?\s*(\{[\s\S]*\})\s*```', cleaned)
    if fenced_match:
        cleaned = fenced_match.group(1)

    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        return json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError:
        return None


def strip_markdown(text):
    if not text:
        return ''

    plain = str(text)
    plain = re.sub(r'```[\s\S]*?```', ' ', plain)
    plain = re.sub(r'`([^`]+)`', r'\1', plain)
    plain = re.sub(r'!\[[^\]]*\]\([^)]+\)', ' ', plain)
    plain = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', plain)
    plain = re.sub(r'(\*\*|__)(.*?)\1', r'\2', plain)
    plain = re.sub(r'(\*|_)(.*?)\1', r'\2', plain)
    plain = re.sub(r'^#{1,6}\s*', '', plain, flags=re.MULTILINE)
    plain = re.sub(r'^\s*[-*+]\s+', '', plain, flags=re.MULTILINE)
    plain = re.sub(r'^\s*\d+\.\s+', '', plain, flags=re.MULTILINE)
    plain = plain.replace('\\(', '').replace('\\)', '')
    plain = plain.replace('\\[', '').replace('\\]', '')
    plain = plain.replace('$$', '')
    plain = re.sub(r'\s+', ' ', plain)
    return plain.strip()


def make_json_safe(value):
    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(item) for item in value]
    if isinstance(value, django_models.Model):
        return {
            'id': value.pk,
            'model': value.__class__.__name__,
            'label': str(value),
        }
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def extract_table_name(table_line):
    if not table_line:
        return 'tabla'
    line = str(table_line).strip()
    if line.startswith('- '):
        line = line[2:]
    return line.split(':', 1)[0].strip() or 'tabla'


def normalize_question_text(value):
    normalized = unicodedata.normalize('NFKD', str(value or ''))
    ascii_only = normalized.encode('ascii', 'ignore').decode('ascii')
    return ascii_only.lower()


def question_matches(question, hints):
    question_text = normalize_question_text(question)
    return any(hint in question_text for hint in hints)


def _make_signature_fragment(value):
    if isinstance(value, dict):
        cleaned = {}
        for key in sorted(value.keys()):
            normalized = _make_signature_fragment(value[key])
            if normalized in (None, '', [], {}):
                continue
            cleaned[str(key)] = normalized
        return cleaned
    if isinstance(value, (list, tuple, set)):
        return [_make_signature_fragment(item) for item in value]
    if isinstance(value, Decimal):
        return round(float(value), 4)
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    return normalize_question_text(value)


def _pick_chart_point_signature(item):
    if not isinstance(item, dict):
        return _make_signature_fragment(item)

    keys = (
        'label', 'name', 'metric', 'x', 'y', 'value',
        'secondary_value', 'reference_value', 'source', 'target',
    )
    return {
        key: _make_signature_fragment(item[key])
        for key in keys
        if key in item and item[key] not in (None, '')
    }


def build_chart_signature(chart):
    if not isinstance(chart, dict):
        return None

    data = chart.get('data')
    if isinstance(data, list):
        normalized_data = [_pick_chart_point_signature(item) for item in data]
    elif isinstance(data, dict):
        normalized_data = {
            'nodes': [_pick_chart_point_signature(item) for item in data.get('nodes', [])],
            'links': [_pick_chart_point_signature(item) for item in data.get('links', [])],
        }
    else:
        normalized_data = _make_signature_fragment(data)

    payload = {
        'chart_type': normalize_question_text(chart.get('chart_type')),
        'orientation': normalize_question_text(chart.get('orientation')),
        'value_label': normalize_question_text(chart.get('value_label')),
        'secondary_label': normalize_question_text(chart.get('secondary_label')),
        'x_label': normalize_question_text(chart.get('x_label')),
        'y_label': normalize_question_text(chart.get('y_label')),
        'x_labels': [normalize_question_text(item) for item in (chart.get('x_labels') or [])],
        'y_labels': [normalize_question_text(item) for item in (chart.get('y_labels') or [])],
        'series': [normalize_question_text(item) for item in (chart.get('series') or [])],
        'data': normalized_data,
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=True)


def _collect_slide_charts(slide):
    charts = slide.get('charts')
    if isinstance(charts, list) and charts:
        return [chart for chart in charts if isinstance(chart, dict)]
    if slide.get('type') == 'chart' or slide.get('chart_type'):
        return [slide]
    return []


def dedupe_slides(slides):
    unique = []
    seen = set()
    seen_chart_keys = set()

    for slide in slides:
        if not isinstance(slide, dict):
            continue

        slide_charts = _collect_slide_charts(slide)
        if slide_charts:
            unique_charts = []
            for chart in slide_charts:
                signature = build_chart_signature(chart)
                if not signature or signature in seen_chart_keys:
                    continue
                seen_chart_keys.add(signature)
                unique_charts.append(chart)

            if not unique_charts:
                continue

            normalized_slide = dict(slide)
            normalized_slide['charts'] = unique_charts
            unique.append(normalized_slide)
            continue

        identity = (
            normalize_question_text(slide.get('type')),
            normalize_question_text(slide.get('title')),
            normalize_question_text(slide.get('question')),
            normalize_question_text(slide.get('stage')),
        )
        if identity in seen:
            continue
        seen.add(identity)
        unique.append(slide)

    return unique


def build_dataset_overview_chart_slide(context, question=None):
    summary = context.get('summary') or {}
    overview = summary.get('overview') or {}
    tables = context.get('selected_table_summaries') or summary.get('tables', [])
    if not tables:
        return None

    focus_tables = tables[:4]
    largest_table = max(focus_tables, key=lambda item: item.get('row_count', 0))
    weakest_quality = min(
        focus_tables,
        key=lambda item: float(item.get('completeness_ratio', 1) or 1),
    )

    if len(focus_tables) == 1:
        focus_table = focus_tables[0]
        return make_chart_slide(
            build_structure_chart(focus_table),
            build_dataset_story_payload(
                stage='Contexto',
                question=question or 'Que tan robusta es la tabla que sostiene esta respuesta?',
                finding=(
                    f'{focus_table["name"]} aporta {focus_table["row_count"]:,} filas '
                    f'y {focus_table["column_count"]} columnas al analisis.'
                ),
                complication=(
                    f'Su completitud estimada es de '
                    f'{round(float(focus_table.get("completeness_ratio", 0) or 0) * 100, 1)}%, '
                    'asi que conviene contrastar volumen con calidad.'
                ),
                conclusion='La huella estructural muestra si la respuesta se apoya en una base amplia y usable.',
                recommendation='Usa esta tabla como fuente principal y luego profundiza en sus dimensiones o riesgos mas visibles.',
                signal_value=focus_table['row_count'],
                signal_label='filas analizadas',
                evidence=[
                    f'Columnas: {focus_table["column_count"]}',
                    f'Completitud: {round(float(focus_table.get("completeness_ratio", 0) or 0) * 100, 1)}%',
                ],
                business_context=overview.get('business_context', ''),
                insight_type='segment',
                table=focus_table,
            ),
            table=focus_table,
        )

    chart = build_combo_story_chart(
        title='Fuentes que sostienen esta respuesta',
        subtitle='Volumen y completitud de las tablas priorizadas para la pregunta',
        data=[
            {
                'label': table['name'],
                'value': table['row_count'],
                'secondary_value': round(float(table.get('completeness_ratio', 0) or 0) * 100, 1),
            }
            for table in focus_tables
        ],
        value_label='filas',
        secondary_label='% completitud',
        secondary_domain=[0, 100],
    )

    return make_chart_slide(
        chart,
        build_dataset_story_payload(
            stage='Contexto',
            question=question or 'Que tablas sostienen esta lectura?',
            finding=(
                f'{largest_table["name"]} concentra el mayor volumen con '
                f'{largest_table["row_count"]:,} filas dentro del set citado.'
            ),
            complication=(
                f'La calidad mas baja aparece en {weakest_quality["name"]} con '
                f'{round(float(weakest_quality.get("completeness_ratio", 0) or 0) * 100, 1)}% de completitud.'
            ),
            conclusion='La respuesta es mas solida cuando el peso de cada tabla se lee junto con su calidad.',
            recommendation='Prioriza primero las tablas con alto volumen y buena completitud antes de profundizar en detalles mas finos.',
            signal_value=largest_table['row_count'],
            signal_label=f'filas en {largest_table["name"]}',
            evidence=[
                f'Tablas citadas: {len(focus_tables)}',
                f'Completitud global: {round(float(overview.get("completeness_ratio", 0) or 0) * 100, 1)}%',
            ],
            business_context=overview.get('business_context', ''),
            insight_type='segment',
            table=largest_table,
        ),
        table=largest_table,
    )


def build_metrics_supporting_chart_slides(context, question=None, max_slides=2):
    revenue = list(reversed(context.get('recent_revenue') or []))
    metrics = context.get('metrics') or {}
    slides = []

    if len(revenue) >= 2:
        peak_month = max(revenue, key=lambda item: float(item.get('revenue') or 0))
        slides.append(make_chart_slide(
            build_combo_story_chart(
                title='Revenue y profit recientes',
                subtitle='Contexto temporal disponible para responder la pregunta',
                data=[
                    {
                        'label': item['month'],
                        'value': item['revenue'],
                        'secondary_value': item['profit'],
                    }
                    for item in revenue
                ],
                value_label='Revenue',
                secondary_label='Profit',
            ),
            build_dataset_story_payload(
                stage='Contexto',
                question=question or 'Como viene el negocio en los ultimos periodos?',
                finding=(
                    f'El mayor revenue reciente aparece en {peak_month["month"]} '
                    f'con {peak_month["revenue"]:,.0f}.'
                ),
                complication='La lectura ejecutiva necesita separar crecimiento de revenue y conversion en profit.',
                conclusion='La serie reciente permite sostener la respuesta con una referencia temporal concreta.',
                recommendation='Usa esta tendencia como base y luego valida que KPI explica mejor el cambio observado.',
                signal_value=f'{peak_month["revenue"]:,.0f}',
                signal_label='revenue pico',
                evidence=[f'Periodos visibles: {len(revenue)}'],
                business_context=context.get('company', ''),
                insight_type='trend',
            ),
        ))

    if metrics:
        metrics_items = list(metrics.items())[:5]
        lead_metric_key, lead_metric = max(
            metrics_items,
            key=lambda item: abs(float(item[1].get('change_percent') or 0)),
        )
        slides.append(make_chart_slide(
            {
                'chart_type': 'bar',
                'title': 'Cambio reciente por KPI',
                'subtitle': 'Comparativo de variacion porcentual entre metricas actuales',
                'data': [
                    {
                        'label': metric_data.get('unit') == '#'
                            and metric_key.upper()
                            or metric_key.upper(),
                        'value': round(float(metric_data.get('change_percent') or 0), 2),
                    }
                    for metric_key, metric_data in metrics_items
                ],
                'value_label': '% cambio',
                'orientation': 'horizontal',
            },
            build_dataset_story_payload(
                stage='Drivers',
                question=question or 'Que KPI se esta moviendo con mas fuerza?',
                finding=(
                    f'{lead_metric_key.upper()} registra un cambio de '
                    f'{float(lead_metric.get("change_percent") or 0):+.1f}%.'
                ),
                complication='No todos los KPI se mueven en la misma direccion, asi que una sola lectura agregada puede ocultar tensiones.',
                conclusion='Comparar los cambios por KPI ayuda a sostener la respuesta con evidencia cuantitativa inmediata.',
                recommendation='Profundiza primero en el KPI con mayor cambio absoluto y contrasta su variacion con la serie de revenue.',
                signal_value=f'{float(lead_metric.get("change_percent") or 0):+.1f}%',
                signal_label=f'cambio en {lead_metric_key.upper()}',
                evidence=[f'KPI visibles: {len(metrics_items)}'],
                business_context=context.get('company', ''),
                insight_type='segment',
            ),
        ))

    return dedupe_slides(slides)[:max_slides]


def resolve_dataset_chart_builders(question=None):
    builders = []

    if question_matches(question, TIME_QUESTION_HINTS):
        builders.extend([build_time_story_slide, build_change_contribution_story_slide])
    if question_matches(question, SEGMENT_QUESTION_HINTS):
        builders.extend([build_dimension_story_slide, build_benchmark_story_slide])
    if question_matches(question, RELATIONSHIP_QUESTION_HINTS):
        builders.extend([build_relationship_story_slide, build_discovery_story_slide])
    if question_matches(question, QUALITY_QUESTION_HINTS):
        builders.extend([build_quality_story_slide])

    builders.extend([
        build_time_story_slide,
        build_dimension_story_slide,
        build_benchmark_story_slide,
        build_change_contribution_story_slide,
        build_relationship_story_slide,
        build_quality_story_slide,
        build_discovery_story_slide,
    ])

    unique = []
    seen = set()
    for builder in builders:
        if builder.__name__ in seen:
            continue
        seen.add(builder.__name__)
        unique.append(builder)
    return unique


def build_dataset_supporting_chart_slides(context, question=None, max_slides=2):
    summary = context.get('summary') or {}
    table_lookup = {
        table.get('name'): table
        for table in summary.get('tables', [])
        if isinstance(table, dict)
    }
    selected_tables = [
        table_lookup[name]
        for name in context.get('selected_table_names', [])
        if name in table_lookup
    ] or context.get('selected_table_summaries') or summary.get('tables', [])

    slides = []
    relationships = summary.get('relationships', [])
    should_add_overview = (
        len(selected_tables) > 1
        or question_matches(question, STRUCTURE_QUESTION_HINTS)
        or not question
    )

    if should_add_overview:
        overview_slide = build_dataset_overview_chart_slide(context, question)
        if overview_slide:
            slides.append(overview_slide)

    if question_matches(question, STRUCTURE_QUESTION_HINTS) and len(selected_tables) > 1 and relationships:
        selected_names = {table.get('name') for table in selected_tables}
        selected_relationships = [
            relationship
            for relationship in relationships
            if relationship.get('source_table_name') in selected_names
            and relationship.get('target_table_name') in selected_names
        ]
        relationship_chart = build_relationship_sankey_chart(selected_tables, selected_relationships)
        if relationship_chart:
            slides.append(make_chart_slide(
                relationship_chart,
                build_dataset_story_payload(
                    stage='Contexto',
                    question=question or 'Como se conectan las tablas priorizadas?',
                    finding=(
                        f'Se detectan {len(selected_relationships)} relaciones entre las tablas priorizadas '
                        'que ayudan a sostener la lectura entre tablas.'
                    ),
                    complication='La respuesta depende no solo de cada tabla, sino de como viaja la informacion entre ellas.',
                    conclusion='El mapa de relaciones permite validar que la evidencia citada tiene una ruta de conexion clara.',
                    recommendation='Usa esta red para profundizar en llaves, uniones y tablas foco antes de automatizar reportes.',
                    signal_value=len(selected_relationships),
                    signal_label='relaciones detectadas',
                    evidence=[f'Tablas citadas: {len(selected_tables)}'],
                    business_context=(summary.get('overview') or {}).get('business_context', ''),
                    insight_type='segment',
                    table=selected_tables[0],
                ),
                table=selected_tables[0],
            ))

    builders = resolve_dataset_chart_builders(question)
    for table in selected_tables:
        for builder in builders:
            slide = builder(table)
            if slide:
                slides.append(slide)
            if len(dedupe_slides(slides)) >= max_slides:
                return dedupe_slides(slides)[:max_slides]

    if not slides:
        fallback_slide = build_dataset_overview_chart_slide(context, question)
        if fallback_slide:
            slides.append(fallback_slide)

    return dedupe_slides(slides)[:max_slides]


def build_supporting_chart_slides(context, question=None, max_slides=2):
    if context.get('mode') == 'dataset':
        return build_dataset_supporting_chart_slides(context, question, max_slides=max_slides)
    return build_metrics_supporting_chart_slides(context, question, max_slides=max_slides)


def merge_supporting_chart_slides(presentation, chart_slides):
    if not chart_slides:
        return presentation

    slides = list((presentation or {}).get('slides') or [])
    merged = dedupe_slides(slides + [])

    insert_at = 1 if merged and merged[0].get('type') == 'hero' else 0
    merged_slides = dedupe_slides(merged[:insert_at] + list(chart_slides) + merged[insert_at:])
    return {
        **(presentation or {}),
        'slides': merged_slides[:6],
    }


def build_table_focus_payload(context):
    tables = []
    for table_line in (context.get('table_lines') or [])[:2]:
        tables.append({
            'name': extract_table_name(table_line),
            'detail': table_line.lstrip('- ').strip(),
            'highlight': extract_table_name(table_line),
        })
    return tables


def build_default_ai_presentation(context, question=None, raw_response=''):
    dataset_name = (
        context.get('summary', {}).get('overview', {}).get('dataset_name')
        if context.get('mode') == 'dataset'
        else None
    )
    title = question or f'Respuesta sobre {dataset_name or context.get("company", "tu negocio")}'
    summary_markdown = raw_response.strip() if raw_response else 'No pude estructurar la respuesta, pero aqui esta la mejor lectura disponible.'

    hero_bullets = []
    if context.get('mode') == 'dataset':
        hero_bullets.extend((context.get('summary', {}).get('dashboard', {}).get('insights') or [])[:3])
        if not hero_bullets:
            hero_bullets.extend((context.get('table_lines') or [])[:2])
    else:
        hero_bullets.extend([
            f"{key.upper()}: {value['value']} {value['unit']} ({value['change_percent']:+.1f}%)"
            for key, value in list((context.get('metrics') or {}).items())[:3]
        ])

    if not hero_bullets:
        hero_bullets.append('No encontre suficiente contexto estructurado para responder con mas precision.')

    slides = [
        {
            'type': 'hero',
            'eyebrow': 'AI Insight',
            'stage': 'Respuesta',
            'title': title,
            'subtitle': (
                f"Lectura basada en {dataset_name}."
                if dataset_name
                else f"Lectura ejecutiva para {context.get('company', 'tu negocio')}."
            ),
            'question': question or 'Resumen ejecutivo',
            'bullets': hero_bullets[:4],
            'accent_value': str(len(hero_bullets[:4])),
            'accent_label': 'hallazgos clave',
            'finding': hero_bullets[0],
            'conclusion': hero_bullets[1] if len(hero_bullets) > 1 else hero_bullets[0],
            'recommendation': hero_bullets[2] if len(hero_bullets) > 2 else 'Haz una siguiente pregunta mas especifica para profundizar.',
        }
    ]

    if context.get('mode') == 'dataset':
        slides.append({
            'type': 'table_focus',
            'stage': 'Contexto',
            'title': 'Tablas y campos mas relevantes',
            'subtitle': 'La respuesta se apoya en las tablas priorizadas por la pregunta y el resumen del dataset.',
            'question': question or 'Que debo revisar primero?',
            'tables': build_table_focus_payload(context),
            'finding': (context.get('relationship_lines') or ['No se detectaron relaciones relevantes.'])[0],
            'conclusion': 'Conviene validar primero las tablas citadas antes de llevar esta lectura a decisiones operativas.',
            'recommendation': 'Si quieres, puedo desglosar esta respuesta por tabla, columna o segmento.',
        })

    slides.append({
        'type': 'rich_text',
        'stage': 'Desarrollo',
        'title': 'Respuesta desarrollada',
        'subtitle': 'Puedes usar Markdown y LaTeX en esta lectura.',
        'body': summary_markdown,
        'callouts': [
            {'label': 'Modo', 'value': 'dataset' if context.get('mode') == 'dataset' else 'metricas'},
            {'label': 'Soporte visual', 'value': 'Narrativa y evidencia grafica'},
        ],
    })

    return {
        'title': title,
        'summary_markdown': summary_markdown,
        'slides': slides[:3],
    }


def normalize_ai_slide(slide, index, context, question=None):
    slide_type = str((slide or {}).get('type') or 'rich_text').strip().lower()
    if slide_type not in {'hero', 'rich_text', 'table_focus'}:
        slide_type = 'rich_text'

    if slide_type == 'hero':
        bullets = [
            str(item).strip()
            for item in ((slide or {}).get('bullets') or [])
            if str(item).strip()
        ][:4]
        if not bullets:
            bullets = [item for item in (context.get('summary', {}).get('dashboard', {}).get('insights') or [])[:3] if item]
        if not bullets:
            bullets = ['No hubo suficientes datos para construir bullets adicionales.']

        return {
            'type': 'hero',
            'eyebrow': (slide or {}).get('eyebrow') or 'AI Insight',
            'stage': (slide or {}).get('stage') or 'Respuesta',
            'title': (slide or {}).get('title') or question or 'Respuesta ejecutiva',
            'subtitle': (slide or {}).get('subtitle') or 'Lectura sintetizada a partir del contexto disponible.',
            'question': (slide or {}).get('question') or question or 'Pregunta sin titulo',
            'bullets': bullets,
            'accent_value': str((slide or {}).get('accent_value') or len(bullets)),
            'accent_label': (slide or {}).get('accent_label') or 'puntos clave',
            'finding': (slide or {}).get('finding') or bullets[0],
            'conclusion': (slide or {}).get('conclusion') or bullets[min(1, len(bullets) - 1)],
            'recommendation': (slide or {}).get('recommendation') or 'Haz una siguiente pregunta para profundizar.',
        }

    if slide_type == 'table_focus':
        tables = []
        for table in ((slide or {}).get('tables') or [])[:2]:
            name = str((table or {}).get('name') or '').strip()
            detail = str((table or {}).get('detail') or '').strip()
            highlight = str((table or {}).get('highlight') or name or '').strip()
            if not name:
                continue
            tables.append({
                'name': name,
                'detail': detail or f'{name} fue seleccionada por su relevancia para esta respuesta.',
                'highlight': highlight or name,
            })
        if not tables:
            tables = build_table_focus_payload(context)

        return {
            'type': 'table_focus',
            'stage': (slide or {}).get('stage') or 'Contexto',
            'title': (slide or {}).get('title') or 'Tablas relevantes para la respuesta',
            'subtitle': (slide or {}).get('subtitle') or 'Estas son las fuentes mas importantes citadas para responder.',
            'question': (slide or {}).get('question') or question or 'Que tablas importan aqui?',
            'tables': tables[:2],
            'finding': (slide or {}).get('finding') or 'Estas tablas concentran la evidencia principal.',
            'conclusion': (slide or {}).get('conclusion') or 'Conviene contrastar la respuesta con estas fuentes antes de automatizar decisiones.',
            'recommendation': (slide or {}).get('recommendation') or 'Pide un zoom por tabla o columna para profundizar.',
        }

    callouts = []
    for callout in ((slide or {}).get('callouts') or [])[:4]:
        label = str((callout or {}).get('label') or '').strip()
        value = str((callout or {}).get('value') or '').strip()
        if not label and not value:
            continue
        callouts.append({
            'label': label or 'Dato',
            'value': value or 'Sin detalle',
        })

    body = str((slide or {}).get('body') or '').strip()
    if not body:
        body = 'No hubo suficiente detalle estructurado para este slide.'

    return {
        'type': 'rich_text',
        'stage': (slide or {}).get('stage') or f'Detalle {index + 1}',
        'title': (slide or {}).get('title') or 'Desarrollo',
        'subtitle': (slide or {}).get('subtitle') or 'Lectura desarrollada en formato enriquecido.',
        'body': body,
        'callouts': callouts,
    }


def normalize_ai_presentation(payload, context, question=None, raw_response=''):
    if not isinstance(payload, dict):
        return build_default_ai_presentation(context, question, raw_response)

    slides = payload.get('slides')
    if not isinstance(slides, list) or not slides:
        return build_default_ai_presentation(context, question, raw_response)

    normalized_slides = [
        normalize_ai_slide(slide, index, context, question)
        for index, slide in enumerate(slides[:4])
    ]
    summary_markdown = str(payload.get('summary_markdown') or '').strip()
    if not summary_markdown:
        summary_markdown = '\n\n'.join(
            slide.get('body') or slide.get('finding') or slide.get('subtitle') or ''
            for slide in normalized_slides
        ).strip()
    if not summary_markdown:
        summary_markdown = raw_response.strip() or 'Respuesta sin resumen adicional.'

    return {
        'title': str(payload.get('title') or question or 'AI Insight').strip(),
        'summary_markdown': summary_markdown,
        'slides': normalized_slides,
    }


def build_ai_presentation_prompt(context, question=None):
    analysis_prompt = build_ai_prompt(context, question)
    return f"""Actua como el motor de presentaciones de Lumiq.
Devuelve solo JSON valido, sin texto adicional, siguiendo exactamente este esquema:
{{
  "title": "titulo breve",
  "summary_markdown": "resumen breve en markdown",
  "slides": [
    {{
      "type": "hero|rich_text|table_focus",
      "stage": "etapa corta",
      "title": "titulo en markdown",
      "subtitle": "subtitulo en markdown"
    }}
  ]
}}

Reglas de composicion:
- Responde solo con las diapositivas necesarias para contestar la pregunta.
- Usa 1 slide si la pregunta es directa y puntual.
- Usa 2 slides si necesitas respuesta + evidencia.
- Usa 3 slides si necesitas respuesta + evidencia + accion.
- Usa 4 slides solo si la pregunta es comparativa o claramente multietapa.
- Nunca generes index o workflow salvo que el usuario pida proceso o roadmap.
- Usa solo los tipos permitidos: hero, rich_text y table_focus.
- Si usas hero, incluye: question, bullets, accent_value, accent_label, finding, conclusion, recommendation.
- Si usas rich_text, incluye: body y opcionalmente callouts = [{{"label":"...", "value":"..."}}].
- Si usas table_focus, incluye tables con maximo 2 elementos: [{{"name":"...", "detail":"...", "highlight":"..."}}].
- En todos los textos puedes usar Markdown.
- Si necesitas notacion matematica, prefiere LaTeX con \\( ... \\) o \\[ ... \\].
- Cita nombres exactos de tablas y columnas cuando existan.
- No inventes datos faltantes; si algo no se puede inferir, dilo con claridad.
- Mantente ejecutivo, concreto y visual.
- Redacta pensando que la presentacion tambien mostrara graficos de soporte: deja aire visual y evita bloques largos.
- Si usas rich_text, el body debe caber como lectura breve junto a evidencia visual: 1 idea por parrafo y maximo 90 palabras.
- Si usas callouts, cada value debe ser breve, accionable y de una sola idea; evita repetir literalmente lo que ya se veria en un grafico.
- Prioriza explicar que debe mirarse, por que importa y que decision sugiere, en vez de volver a enumerar todos los datos.

CONTEXTO ANALITICO:
{analysis_prompt}
"""


def build_stored_metrics_context(context, presentation):
    return {
        'analysis_context': make_json_safe(context),
        'presentation': make_json_safe(presentation),
    }


def generate_ai_presentation(context, question=None):
    prompt = build_ai_presentation_prompt(context, question)
    raw_response = get_ai_response(prompt, max_tokens=1400)
    parsed = extract_json_payload(raw_response)
    presentation = normalize_ai_presentation(parsed, context, question, raw_response)
    presentation = merge_supporting_chart_slides(
        presentation,
        build_supporting_chart_slides(context, question, max_slides=2),
    )
    preview = strip_markdown(presentation.get('summary_markdown') or raw_response)
    if not preview:
        preview = strip_markdown(question or presentation.get('title') or 'AI Insight')
    return presentation, preview[:600]


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


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_insight(request, pk):
    try:
        insight = AIInsight.objects.get(pk=pk, user=request.user)
        insight.delete()
        return Response({'message': 'Insight eliminado correctamente.'})
    except AIInsight.DoesNotExist:
        return Response({'error': 'No encontrado.'}, status=404)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_insights(request):
    deleted_count, _ = AIInsight.objects.filter(user=request.user).delete()
    return Response({
        'message': 'Historial eliminado correctamente.',
        'deleted': deleted_count,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_insight(request):
    try:
        question = request.data.get('question', None)
        context = build_analysis_context(request.user, question)
        presentation, content = generate_ai_presentation(context, question)
        title = presentation.get('title') or question or 'Resumen Ejecutivo IA'

        insight = AIInsight.objects.create(
            user=request.user,
            insight_type='summary' if not question else 'recommendation',
            priority='high',
            title=title,
            content=content,
            metrics_context=build_stored_metrics_context(context, presentation),
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
    provider, model = get_ai_provider_and_model()

    def event_stream():
        try:
            yield f'data: {json.dumps({"status": "Interpretando tu pregunta..."})}\n\n'
            yield f'data: {json.dumps({"status": "Construyendo la presentacion..."})}\n\n'
            presentation, content = generate_ai_presentation(context, question)
        except Exception as exc:
            yield f'data: {json.dumps({"error": str(exc)})}\n\n'
            return

        insight = AIInsight.objects.create(
            user=request.user,
            insight_type='summary' if not question else 'recommendation',
            priority='high',
            title=presentation.get('title') or question or 'Resumen Ejecutivo IA',
            content=content,
            metrics_context=build_stored_metrics_context(context, presentation),
        )
        serialized = AIInsightSerializer(insight).data
        yield f'data: {json.dumps({"status": "Presentacion lista."})}\n\n'
        yield f'data: {json.dumps({"done": True, "provider": provider, "model": model, "insight": serialized})}\n\n'

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
