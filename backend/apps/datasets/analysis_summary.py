from datetime import datetime

import pandas as pd

from . import insight_engine, story_engine, visual_engine
from .analysis_enrichment import (
    MAX_NULL_PATTERN_ITEMS,
    build_business_impact,
    build_business_context,
    build_change_contribution,
    build_chart_annotations,
    build_diagnostic_chain,
    build_hero_kpi,
    build_insight_confidence,
    build_narrative_arc,
    build_null_impact,
    build_null_patterns,
    build_reference_lines,
    build_seasonality_analysis,
    build_segment_benchmarks,
    build_segment_clusters,
    build_semantic_colors,
    build_slide_layout,
    build_trend_forecast,
    choose_best_chart,
    infer_higher_is_better,
    rank_table_insights,
)
from .datetime_utils import parse_datetime_series
from .models import DatasetImport
from .services import extract_schema_profile
from .utils import (
    format_compact_number,
    format_percent,
    is_identifier_like,
    json_value,
    normalize_lookup_label,
    safe_ratio,
    score_column_name,
)

MEASURE_KEYWORDS = [
    'amount',
    'total',
    'revenue',
    'sales',
    'sale',
    'price',
    'profit',
    'cost',
    'monto',
    'importe',
    'ingreso',
    'venta',
    'valor',
    'quantity',
    'qty',
]

DATE_KEYWORDS = ['date', 'created', 'updated', 'time', 'timestamp', 'fecha', 'period', 'month']
GEO_KEYWORDS = ['country', 'pais', 'state', 'estado', 'region', 'provincia', 'province', 'city', 'ciudad']
GEO_POINT_LOOKUP = {
    'argentina': {'x': 30, 'y': 43},
    'australia': {'x': 84, 'y': 42},
    'brazil': {'x': 34, 'y': 32},
    'brasil': {'x': 34, 'y': 32},
    'canada': {'x': 20, 'y': 12},
    'chile': {'x': 28, 'y': 44},
    'china': {'x': 75, 'y': 20},
    'colombia': {'x': 28, 'y': 26},
    'france': {'x': 49, 'y': 18},
    'germany': {'x': 52, 'y': 16},
    'india': {'x': 69, 'y': 25},
    'italy': {'x': 54, 'y': 20},
    'japan': {'x': 86, 'y': 21},
    'mexico': {'x': 16, 'y': 23},
    'peru': {'x': 29, 'y': 33},
    'spain': {'x': 46, 'y': 20},
    'united kingdom': {'x': 47, 'y': 14},
    'uk': {'x': 47, 'y': 14},
    'united states': {'x': 17, 'y': 20},
    'usa': {'x': 17, 'y': 20},
    'us': {'x': 17, 'y': 20},
    'uruguay': {'x': 33, 'y': 45},
    'venezuela': {'x': 31, 'y': 24},
    'lima': {'x': 29, 'y': 32},
    'bogota': {'x': 28, 'y': 25},
    'santiago': {'x': 28, 'y': 44},
    'mexico city': {'x': 17, 'y': 22},
    'new york': {'x': 20, 'y': 18},
    'california': {'x': 13, 'y': 23},
    'texas': {'x': 16, 'y': 24},
    'florida': {'x': 22, 'y': 25},
    'madrid': {'x': 46, 'y': 20},
    'paris': {'x': 49, 'y': 18},
    'berlin': {'x': 52, 'y': 16},
}
def compact_table_record(table):
    return {
        'name': table['name'],
        'row_count': table['row_count'],
        'column_count': table['column_count'],
        'primary_key_name': table.get('primary_key_name', ''),
        'completeness_ratio': table.get('completeness_ratio', 0),
        'numeric_columns_count': table.get('numeric_columns_count', 0),
        'categorical_columns_count': table.get('categorical_columns_count', 0),
        'datetime_columns_count': table.get('datetime_columns_count', 0),
        'focus_measure_column': table.get('focus_measure_column', ''),
        'focus_date_column': table.get('focus_date_column', ''),
        'business_context': table.get('business_context', ''),
        'top_numeric_metrics': table.get('top_numeric_metrics', [])[:3],
        'top_dimensions': table.get('top_dimensions', [])[:2],
        'time_series': table.get('time_series'),
        'seasonality_analysis': table.get('seasonality_analysis'),
        'trend_summary': table.get('trend_summary'),
        'quality_watchlist': table.get('quality_watchlist', [])[:4],
        'null_impact': table.get('null_impact', [])[:4],
        'null_patterns': table.get('null_patterns', [])[:MAX_NULL_PATTERN_ITEMS],
        'correlation_pairs': table.get('correlation_pairs', [])[:4],
        'outlier_watchlist': table.get('outlier_watchlist', [])[:4],
        'text_watchlist': table.get('text_watchlist', [])[:3],
        'segment_clusters': table.get('segment_clusters'),
        'segment_benchmarks': table.get('segment_benchmarks', [])[:5],
        'change_contribution': table.get('change_contribution', [])[:5],
        'diagnostic_chain': table.get('diagnostic_chain'),
        'business_impact': table.get('business_impact'),
        'ranked_insights': table.get('ranked_insights', [])[:3],
        'insight_bundle': table.get('insight_bundle'),
        'hero_kpi': table.get('hero_kpi'),
        'insight_confidence': table.get('insight_confidence', {}),
        'analysis_modes': table.get('analysis_modes', []),
        'recommended_analyses': table.get('recommended_analyses', [])[:4],
        'field_highlights': table.get('field_highlights', [])[:4],
        'sample_rows': table.get('sample_rows', [])[:2],
        'scatter_chart': table.get('scatter_chart'),
        'heatmap_chart': table.get('heatmap_chart'),
        'geo_map_chart': table.get('geo_map_chart'),
        'sankey_chart': table.get('sankey_chart'),
        'radar_chart': table.get('radar_chart'),
        'treemap_chart': table.get('treemap_chart'),
    }
def choose_measure_column(dataframe: pd.DataFrame, numeric_columns: list[str]) -> str:
    candidates = []
    for column_name in numeric_columns:
        lowered = column_name.lower()
        if lowered == 'id' or lowered.endswith('_id'):
            continue
        series = pd.to_numeric(dataframe[column_name], errors='coerce').dropna()
        if series.empty:
            continue
        score = score_column_name(column_name, MEASURE_KEYWORDS)
        score += int(series.abs().sum() > 0)
        score += int(series.nunique() > 1)
        candidates.append((score, series.abs().mean(), column_name))

    if not candidates:
        return ''

    candidates.sort(reverse=True)
    return candidates[0][2]


def choose_date_column(dataframe: pd.DataFrame, datetime_columns: list[str]) -> str:
    scored = []
    for column_name in datetime_columns:
        parsed = parse_datetime_series(dataframe[column_name]).dropna()
        if parsed.empty:
            continue
        score = score_column_name(column_name, DATE_KEYWORDS)
        score += int(parsed.nunique() > 1)
        scored.append((score, parsed.nunique(), column_name))

    if not scored:
        return ''

    scored.sort(reverse=True)
    return scored[0][2]


def build_sample_rows(dataframe: pd.DataFrame, max_rows: int = 3) -> list[dict]:
    sample = []
    for _, row in dataframe.head(max_rows).iterrows():
        sample.append({
            str(column): json_value(value)
            for column, value in row.items()
        })
    return sample


def build_numeric_summaries(dataframe: pd.DataFrame, numeric_columns: list[str]) -> list[dict]:
    summaries = []
    for column_name in numeric_columns:
        if is_identifier_like(column_name):
            continue
        series = pd.to_numeric(dataframe[column_name], errors='coerce').dropna()
        if series.empty:
            continue
        summaries.append({
            'column': column_name,
            'count': int(series.shape[0]),
            'sum': round(float(series.sum()), 4),
            'mean': round(float(series.mean()), 4),
            'std': round(float(series.std(ddof=1)), 4),
            'p25': round(float(series.quantile(0.25)), 4),
            'median': round(float(series.median()), 4),
            'p75': round(float(series.quantile(0.75)), 4),
            'min': round(float(series.min()), 4),
            'max': round(float(series.max()), 4),
            'score': score_column_name(column_name, MEASURE_KEYWORDS),
        })

    summaries.sort(key=lambda item: (item['score'], item['count'], abs(item['sum'])), reverse=True)
    for item in summaries:
        item.pop('score', None)
    return summaries[:5]


def build_category_summaries(dataframe: pd.DataFrame, categorical_columns: list[str]) -> list[dict]:
    summaries = []
    for column_name in categorical_columns:
        if is_identifier_like(column_name):
            continue
        series = dataframe[column_name].dropna().astype(str).str.strip()
        if series.empty:
            continue
        unique_count = int(series.nunique())
        if unique_count <= 1:
            continue
        is_high_cardinality = unique_count > 25
        if unique_count > 100:
            continue

        top_values = series.value_counts().head(5)
        total = int(series.shape[0])
        summaries.append({
            'column': column_name,
            'cardinality': unique_count,
            'is_high_cardinality': is_high_cardinality,
            'top_values': [
                {
                    'label': index,
                    'count': int(value),
                    'share': round(float(value / total), 4),
                }
                for index, value in top_values.items()
            ],
        })

    summaries.sort(
        key=lambda item: (
            item['top_values'][0]['share'] if item['top_values'] else 0,
            -item['cardinality'],
        ),
        reverse=True,
    )
    return summaries[:4]


def build_dimension_story_chart(table: dict) -> dict | None:
    top_dimension = (table.get('top_dimensions') or [None])[0]
    if not top_dimension or not top_dimension.get('top_values'):
        return None

    values = top_dimension['top_values']
    max_label_length = max(len(str(item['label'])) for item in values)
    chart_choice = choose_best_chart('distribution', {
        'n_categories': len(values),
        'n_points': len(values),
        'has_negatives': False,
        'is_temporal': False,
        'n_series': 1,
    })
    chart_type = 'bar' if chart_choice == 'bar_horizontal' else chart_choice

    chart = {
        'chart_type': chart_type,
        'title': f'Distribucion de {top_dimension["column"]}',
        'subtitle': f'Categorias dominantes en {table["name"]}',
        'data': [
            {'label': item['label'], 'value': item['count']}
            for item in values
        ],
        'value_label': 'registros',
    }

    if chart_choice == 'bar_horizontal' or chart_type == 'bar':
        chart['orientation'] = 'horizontal' if len(values) > 4 or max_label_length > 12 else 'vertical'

    return chart


def build_treemap_chart(dataframe: pd.DataFrame, dimension_column: str, measure_column: str, table_name: str) -> dict | None:
    if not dimension_column or not measure_column:
        return None

    categories = dataframe[dimension_column].dropna().astype(str).str.strip()
    if categories.empty:
        return None

    unique_count = int(categories.nunique())
    if unique_count < 4 or unique_count > 12:
        return None

    numeric_values = pd.to_numeric(dataframe[measure_column], errors='coerce')
    chart_frame = pd.DataFrame({'dimension': categories, 'value': numeric_values}).dropna()
    if chart_frame.empty:
        return None

    aggregated = chart_frame.groupby('dimension')['value'].sum().sort_values(ascending=False).head(8)
    if aggregated.shape[0] < 4:
        return None

    return {
        'chart_type': 'treemap',
        'title': f'{measure_column} por {dimension_column}',
        'subtitle': f'Peso relativo por categoria dentro de {table_name}',
        'data': [
            {'name': index, 'value': round(float(value), 4)}
            for index, value in aggregated.items()
        ],
        'value_label': measure_column,
    }


def build_scatter_chart(dataframe: pd.DataFrame, correlation_pairs: list[dict], table_name: str) -> dict | None:
    pair = next(
        (
            item
            for item in (correlation_pairs or [])
            if item.get('absolute_correlation', 0) >= 0.6
        ),
        None,
    )
    if not pair:
        return None

    x_column = pair['left_column']
    y_column = pair['right_column']
    scatter_frame = dataframe[[x_column, y_column]].apply(pd.to_numeric, errors='coerce').dropna()
    if scatter_frame.shape[0] < 6:
        return None

    if scatter_frame.shape[0] > 80:
        scatter_frame = scatter_frame.sample(80, random_state=7)

    return {
        'chart_type': 'scatter',
        'title': f'Relacion entre {x_column} y {y_column}',
        'subtitle': f'Senal {pair["direction"]} detectada en {table_name}',
        'data': [
            {'x': round(float(row[x_column]), 4), 'y': round(float(row[y_column]), 4)}
            for _, row in scatter_frame.iterrows()
        ],
        'x_label': x_column,
        'y_label': y_column,
        'value_label': 'puntos',
    }


def build_heatmap_chart(dataframe: pd.DataFrame, numeric_columns: list[str], table_name: str) -> dict | None:
    candidate_columns = [column_name for column_name in numeric_columns if not is_identifier_like(column_name)]
    if len(candidate_columns) < 3:
        return None

    numeric_frame = dataframe[candidate_columns].apply(pd.to_numeric, errors='coerce')
    usable_columns = [
        column_name
        for column_name in candidate_columns
        if numeric_frame[column_name].notna().sum() >= 4 and numeric_frame[column_name].nunique(dropna=True) > 1
    ][:5]
    if len(usable_columns) < 3:
        return None

    correlation_matrix = numeric_frame[usable_columns].corr()
    cells = []
    for row_label in usable_columns:
        for column_label in usable_columns:
            value = correlation_matrix.at[row_label, column_label]
            if pd.isna(value):
                continue
            cells.append({
                'x': column_label,
                'y': row_label,
                'value': round(float(value), 4),
            })

    return {
        'chart_type': 'heatmap',
        'title': 'Mapa de calor de correlaciones',
        'subtitle': f'Cruce numerico principal en {table_name}',
        'data': cells,
        'x_labels': usable_columns,
        'y_labels': usable_columns,
        'value_label': 'correlacion',
    }


def build_sankey_chart(
    dataframe: pd.DataFrame,
    categorical_columns: list[str],
    measure_column: str,
    table_name: str,
) -> dict | None:
    candidate_dimensions = []
    for column_name in categorical_columns:
        if is_identifier_like(column_name):
            continue
        series = dataframe[column_name].dropna().astype(str).str.strip()
        unique_count = int(series.nunique())
        if 2 <= unique_count <= 8:
            score = score_column_name(column_name, ['stage', 'step', 'status', 'segment', 'channel', 'category', 'region'])
            candidate_dimensions.append((score, -unique_count, column_name))

    if len(candidate_dimensions) < 2:
        return None

    candidate_dimensions.sort(reverse=True)
    left_column = candidate_dimensions[0][2]
    right_column = next(
        (
            column_name
            for _, _, column_name in candidate_dimensions[1:]
            if column_name != left_column
        ),
        '',
    )
    if not right_column:
        return None

    flow_frame = dataframe[[left_column, right_column]].copy()
    flow_frame[left_column] = flow_frame[left_column].astype('string').str.strip()
    flow_frame[right_column] = flow_frame[right_column].astype('string').str.strip()
    flow_frame = flow_frame.dropna()
    if flow_frame.empty:
        return None

    if measure_column:
        numeric_values = pd.to_numeric(dataframe.loc[flow_frame.index, measure_column], errors='coerce')
        flow_frame['value'] = numeric_values.fillna(0)
        aggregated = flow_frame.groupby([left_column, right_column])['value'].sum()
    else:
        aggregated = flow_frame.groupby([left_column, right_column]).size()

    aggregated = aggregated.sort_values(ascending=False).head(12)
    if aggregated.shape[0] < 3:
        return None

    nodes = []
    node_index = {}

    def ensure_node(column_name: str, label: str) -> int:
        key = f'{column_name}::{label}'
        if key not in node_index:
            node_index[key] = len(nodes)
            nodes.append({
                'name': label,
                'group': column_name,
            })
        return node_index[key]

    links = []
    for (left_value, right_value), value in aggregated.items():
        source_index = ensure_node(left_column, str(left_value))
        target_index = ensure_node(right_column, str(right_value))
        links.append({
            'source': source_index,
            'target': target_index,
            'value': round(float(value), 4),
        })

    return {
        'chart_type': 'sankey',
        'title': f'Flujo entre {left_column} y {right_column}',
        'subtitle': f'Transiciones visibles dentro de {table_name}',
        'data': {
            'nodes': nodes,
            'links': links,
        },
        'value_label': measure_column or 'registros',
    }


def build_geo_map_chart(
    dataframe: pd.DataFrame,
    categorical_columns: list[str],
    measure_column: str,
    table_name: str,
) -> dict | None:
    for column_name in categorical_columns:
        series = dataframe[column_name].dropna().astype(str).str.strip()
        if series.empty:
            continue

        value_counts = series.value_counts().head(12)
        mapped_points = []
        for label, count in value_counts.items():
            normalized = normalize_lookup_label(label)
            lookup = GEO_POINT_LOOKUP.get(normalized)
            if not lookup:
                continue

            if measure_column:
                value_series = pd.to_numeric(
                    dataframe.loc[series[series == label].index, measure_column],
                    errors='coerce',
                ).dropna()
                value = round(float(value_series.sum()), 4) if not value_series.empty else float(count)
            else:
                value = float(count)

            mapped_points.append({
                'label': label,
                'value': value,
                'x': lookup['x'],
                'y': lookup['y'],
            })

        keyword_match = score_column_name(column_name, GEO_KEYWORDS) > 0
        if len(mapped_points) >= 3 and (keyword_match or len(mapped_points) >= 4):
            return {
                'chart_type': 'map',
                'title': f'Mapa geografico de {column_name}',
                'subtitle': f'Distribucion espacial detectada en {table_name}',
                'data': mapped_points,
                'value_label': measure_column or 'registros',
            }

    return None


def build_radar_chart(
    dataframe: pd.DataFrame,
    top_dimensions: list[dict],
    top_numeric_metrics: list[dict],
    table_name: str,
) -> dict | None:
    if not top_dimensions or not top_numeric_metrics:
        return None

    dimension = top_dimensions[0]
    categories = [item['label'] for item in dimension.get('top_values', [])[:4]]
    metrics = [item['column'] for item in top_numeric_metrics[:3]]
    if len(categories) < 3 or len(metrics) < 2:
        return None

    radar_frame = dataframe[[dimension['column'], *metrics]].copy()
    radar_frame = radar_frame[radar_frame[dimension['column']].isin(categories)]
    if radar_frame.empty:
        return None

    radar_frame[dimension['column']] = radar_frame[dimension['column']].astype(str)
    for metric in metrics:
        radar_frame[metric] = pd.to_numeric(radar_frame[metric], errors='coerce')

    aggregated = radar_frame.groupby(dimension['column'])[metrics].mean().dropna(how='all')
    if aggregated.shape[0] < 3:
        return None

    data = []
    for metric in metrics:
        metric_row = {'metric': metric}
        max_value = float(aggregated[metric].max()) if aggregated[metric].notna().any() else 0
        divisor = max_value or 1
        for category in categories:
            raw_value = float(aggregated.at[category, metric]) if category in aggregated.index and pd.notna(aggregated.at[category, metric]) else 0
            metric_row[category] = round((raw_value / divisor) * 100, 1)
        data.append(metric_row)

    return {
        'chart_type': 'radar',
        'title': f'Perfil comparado por {dimension["column"]}',
        'subtitle': f'Comparacion normalizada de metricas en {table_name}',
        'data': data,
        'series': categories,
        'value_label': 'indice normalizado',
    }


def build_time_series(dataframe: pd.DataFrame, date_column: str, measure_column: str) -> dict | None:
    if not date_column:
        return None

    parsed_dates = parse_datetime_series(dataframe[date_column])
    valid_mask = parsed_dates.notna()
    if valid_mask.sum() < 2:
        return None

    series_frame = pd.DataFrame({'date': parsed_dates[valid_mask]})
    value_label = 'Registros'

    if measure_column:
        numeric_series = pd.to_numeric(dataframe.loc[valid_mask, measure_column], errors='coerce').fillna(0)
        series_frame['value'] = numeric_series
        value_label = measure_column
        aggregated = series_frame.groupby(series_frame['date'].dt.to_period('M'))['value'].sum()
    else:
        aggregated = series_frame.groupby(series_frame['date'].dt.to_period('M')).size()

    if aggregated.empty:
        return None

    points = [
        {
            'label': str(period),
            'value': round(float(value), 4),
        }
        for period, value in aggregated.tail(12).items()
    ]

    if len(points) < 2:
        return None

    return {
        'date_column': date_column,
        'measure_column': measure_column,
        'value_label': value_label,
        'start': json_value(parsed_dates[valid_mask].min()),
        'end': json_value(parsed_dates[valid_mask].max()),
        'points': points,
    }


def build_trend_summary(time_series: dict | None) -> dict | None:
    if not time_series or len(time_series.get('points', [])) < 2:
        return None

    points = time_series['points']
    start_value = float(points[0]['value'])
    end_value = float(points[-1]['value'])
    change_value = round(end_value - start_value, 4)
    change_percent = None
    if start_value:
        change_percent = round((change_value / start_value) * 100, 2)

    return {
        'start_label': points[0]['label'],
        'end_label': points[-1]['label'],
        'start_value': start_value,
        'end_value': end_value,
        'change_value': change_value,
        'change_percent': change_percent,
    }


def build_correlation_pairs(dataframe: pd.DataFrame, numeric_columns: list[str]) -> list[dict]:
    candidate_columns = [
        column_name
        for column_name in numeric_columns
        if not is_identifier_like(column_name)
    ]
    if len(candidate_columns) < 2:
        return []

    numeric_frame = dataframe[candidate_columns].apply(pd.to_numeric, errors='coerce')
    usable_columns = [
        column_name
        for column_name in candidate_columns
        if numeric_frame[column_name].notna().sum() >= 4 and numeric_frame[column_name].nunique(dropna=True) > 1
    ]
    if len(usable_columns) < 2:
        return []

    correlations = numeric_frame[usable_columns].corr()
    pairs = []
    for index, left_column in enumerate(usable_columns):
        for right_column in usable_columns[index + 1:]:
            correlation_value = correlations.at[left_column, right_column]
            if pd.isna(correlation_value):
                continue

            absolute_value = abs(float(correlation_value))
            if absolute_value < 0.35:
                continue

            pairs.append({
                'left_column': left_column,
                'right_column': right_column,
                'correlation': round(float(correlation_value), 4),
                'absolute_correlation': round(absolute_value, 4),
                'direction': 'positiva' if correlation_value >= 0 else 'negativa',
            })

    pairs.sort(key=lambda item: item['absolute_correlation'], reverse=True)
    return pairs[:5]


def build_outlier_watchlist(
    dataframe: pd.DataFrame,
    numeric_columns: list[str],
    segment_column: str = '',
) -> list[dict]:
    watchlist = []
    for column_name in numeric_columns:
        if is_identifier_like(column_name):
            continue

        series = pd.to_numeric(dataframe[column_name], errors='coerce').dropna()
        if series.shape[0] < 4 or series.nunique() < 4:
            continue

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        if iqr <= 0:
            continue

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        outlier_mask = (series < lower_bound) | (series > upper_bound)
        outlier_count = int(outlier_mask.sum())
        if outlier_count == 0:
            continue

        outlier_share = safe_ratio(outlier_count, int(series.shape[0]))
        most_affected_segment = ''
        if segment_column and segment_column in dataframe.columns:
            segment_series = dataframe.loc[series.index[outlier_mask], segment_column].dropna().astype(str).str.strip()
            if not segment_series.empty:
                most_affected_segment = str(segment_series.mode().iloc[0])
        watchlist.append({
            'column': column_name,
            'outlier_count': outlier_count,
            'outlier_share': outlier_share,
            'outlier_percent': round(outlier_share * 100, 1),
            'lower_bound': round(lower_bound, 4),
            'upper_bound': round(upper_bound, 4),
            'most_affected_segment': most_affected_segment,
        })

    watchlist.sort(key=lambda item: (item['outlier_share'], item['outlier_count']), reverse=True)
    return watchlist[:5]


def build_text_watchlist(dataframe: pd.DataFrame, categorical_columns: list[str]) -> list[dict]:
    watchlist = []
    for column_name in categorical_columns:
        if is_identifier_like(column_name):
            continue

        series = dataframe[column_name].dropna().astype(str).str.strip()
        if series.empty:
            continue

        lengths = series.str.len()
        average_length = float(lengths.mean())
        max_length = int(lengths.max())
        if average_length < 12 and max_length < 30:
            continue

        watchlist.append({
            'column': column_name,
            'avg_length': round(average_length, 1),
            'max_length': max_length,
            'unique_count': int(series.nunique()),
            'sample': str(series.iloc[0])[:120],
        })

    watchlist.sort(
        key=lambda item: (item['avg_length'], item['max_length'], item['unique_count']),
        reverse=True,
    )
    return watchlist[:3]


def build_quality_watchlist(profile: dict, row_count: int) -> list[dict]:
    if row_count <= 0:
        return []

    watchlist = []
    for column in profile['columns']:
        non_null_count = column.get('non_null_count')
        null_count = column.get('null_count')
        if non_null_count is None:
            non_null_count = max(0, row_count - int(null_count or 0))
        if null_count is None:
            null_count = max(0, row_count - int(non_null_count))
        completeness_ratio = safe_ratio(non_null_count, row_count)
        if completeness_ratio >= 0.999:
            continue

        watchlist.append({
            'column': column['name'],
            'inferred_type': column['inferred_type'],
            'null_count': int(null_count),
            'completeness_ratio': completeness_ratio,
            'completeness_percent': round(completeness_ratio * 100, 1),
        })

    watchlist.sort(key=lambda item: (item['completeness_ratio'], -item['null_count']))
    return watchlist[:5]


def build_field_highlights(table: dict) -> list[dict]:
    highlights = []

    if table.get('primary_key_name'):
        highlights.append({
            'column': table['primary_key_name'],
            'role': 'Llave primaria',
            'detail': 'Identifica cada registro dentro del dataset.',
        })

    focus_metric = next(
        (
            metric
            for metric in table.get('top_numeric_metrics', [])
            if metric['column'] == table.get('focus_measure_column')
        ),
        None,
    )
    if focus_metric:
        highlights.append({
            'column': focus_metric['column'],
            'role': 'Medida central',
            'detail': (
                f'Suma {focus_metric["sum"]:,.2f}, promedio {focus_metric["mean"]:,.2f} '
                f'y maximo {focus_metric["max"]:,.2f}.'
            ),
        })

    top_dimension = (table.get('top_dimensions') or [None])[0]
    if top_dimension and top_dimension.get('top_values'):
        dominant = top_dimension['top_values'][0]
        highlights.append({
            'column': top_dimension['column'],
            'role': 'Dimension dominante',
            'detail': (
                f'{dominant["label"]} concentra '
                f'{round(dominant["share"] * 100, 1)}% de los registros visibles.'
            ),
        })

    time_series = table.get('time_series')
    if time_series:
        highlights.append({
            'column': time_series['date_column'],
            'role': 'Serie temporal',
            'detail': (
                f'Permite seguir {time_series["value_label"]} desde '
                f'{time_series["start"]} hasta {time_series["end"]}.'
            ),
        })

    seasonality_analysis = table.get('seasonality_analysis')
    if seasonality_analysis and seasonality_analysis.get('detected'):
        highlights.append({
            'column': seasonality_analysis['strongest_periodicity'],
            'role': 'Estacionalidad',
            'detail': (
                f'Pico en {seasonality_analysis["peak_period"]} y valle en {seasonality_analysis["trough_period"]}, '
                f'con variacion CV {seasonality_analysis["analyses"][0]["cv"]}.'
            ),
        })

    strongest_correlation = (table.get('correlation_pairs') or [None])[0]
    if strongest_correlation:
        highlights.append({
            'column': f'{strongest_correlation["left_column"]} x {strongest_correlation["right_column"]}',
            'role': 'Relacion numerica',
            'detail': (
                f'Correlacion {strongest_correlation["direction"]} de '
                f'{round(strongest_correlation["absolute_correlation"] * 100, 1)}%.'
            ),
        })

    return highlights[:4]


def build_analysis_modes(table: dict) -> list[str]:
    modes = ['quality']
    if table.get('top_numeric_metrics'):
        modes.append('numeric')
    if table.get('top_dimensions'):
        modes.append('categorical')
    if table.get('time_series'):
        modes.append('time_series')
    if table.get('seasonality_analysis'):
        modes.append('seasonality')
    if table.get('correlation_pairs'):
        modes.append('correlation')
    if table.get('outlier_watchlist'):
        modes.append('outliers')
    if table.get('text_watchlist'):
        modes.append('text')
    if table.get('segment_clusters'):
        modes.append('clusters')
    if table.get('change_contribution'):
        modes.append('contribution')
    if table.get('diagnostic_chain'):
        modes.append('diagnostic')
    if table.get('scatter_chart'):
        modes.append('scatter')
    if table.get('heatmap_chart'):
        modes.append('heatmap')
    if table.get('sankey_chart'):
        modes.append('flow')
    if table.get('geo_map_chart'):
        modes.append('geo')
    if table.get('treemap_chart'):
        modes.append('treemap')
    if table.get('radar_chart'):
        modes.append('radar')
    return modes


def build_recommended_analyses(table: dict) -> list[str]:
    suggestions = []

    if table.get('time_series'):
        suggestions.append(
            f'Explorar la tendencia mensual de {table["time_series"]["value_label"]} usando {table["time_series"]["date_column"]}.'
        )

    top_dimension = (table.get('top_dimensions') or [None])[0]
    if top_dimension:
        measure_label = table.get('focus_measure_column') or 'registros'
        suggestions.append(
            f'Segmentar {measure_label} por {top_dimension["column"]} para detectar concentracion o mix de categorias.'
        )

    if table.get('segment_benchmarks'):
        benchmark = table['segment_benchmarks'][0]
        suggestions.append(
            f'Comparar {benchmark["label"]} contra el baseline interno: esta {benchmark["delta_pct"]}% frente al promedio.'
        )

    strongest_correlation = (table.get('correlation_pairs') or [None])[0]
    if strongest_correlation:
        suggestions.append(
            f'Revisar la relacion entre {strongest_correlation["left_column"]} y {strongest_correlation["right_column"]}.'
        )

    if table.get('change_contribution'):
        contribution = table['change_contribution'][0]
        suggestions.append(
            f'Validar por que {contribution["label"]} aporta {contribution["contribution_pct"]}% del cambio observado.'
        )

    outlier_risk = (table.get('outlier_watchlist') or [None])[0]
    if outlier_risk:
        suggestions.append(
            f'Validar outliers en {outlier_risk["column"]}, donde {outlier_risk["outlier_percent"]}% de los valores sale del rango esperado.'
        )

    text_column = (table.get('text_watchlist') or [None])[0]
    if text_column:
        suggestions.append(
            f'Explorar patrones textuales en {text_column["column"]}, con longitud media de {text_column["avg_length"]} caracteres.'
        )

    if table.get('geo_map_chart'):
        suggestions.append(
            f'Revisar la dispersion geografica detectada en {table["geo_map_chart"]["title"].replace("Mapa geografico de ", "")}.'
        )

    if table.get('sankey_chart'):
        suggestions.append(
            f'Analizar el flujo principal descrito entre categorias usando {table["sankey_chart"]["title"].replace("Flujo entre ", "")}.'
        )

    return suggestions[:4]


def _resolve_business_impact_inputs(table: dict) -> tuple[float | None, float | None]:
    trend_summary = table.get('trend_summary') or {}
    delta_pct = trend_summary.get('change_percent')
    if delta_pct is None:
        diagnostic_chain = table.get('diagnostic_chain') or {}
        primary_driver = diagnostic_chain.get('primary_driver') or {}
        delta_pct = primary_driver.get('contribution_pct')
    if delta_pct is None:
        top_benchmark = ((table.get('segment_benchmarks') or [None])[0] or {})
        delta_pct = top_benchmark.get('delta_pct')

    metric_column = table.get('focus_measure_column')
    metric_summary = next(
        (
            item
            for item in (table.get('top_numeric_metrics') or [])
            if item.get('column') == metric_column
        ),
        None,
    ) or ((table.get('top_numeric_metrics') or [None])[0] or {})

    reference_value = metric_summary.get('sum')
    if reference_value in (None, 0):
        reference_value = metric_summary.get('mean')

    return delta_pct, reference_value


def apply_insight_engine_layers(table_analysis: dict) -> dict:
    table_analysis['diagnostic_chain'] = insight_engine.build_diagnostic_chain(table_analysis)
    impact_delta_pct, impact_reference_value = _resolve_business_impact_inputs(table_analysis)
    table_analysis['business_impact'] = insight_engine.build_business_impact(
        impact_delta_pct,
        table_analysis.get('focus_measure_column') or '',
        table_analysis.get('business_context', ''),
        impact_reference_value,
    )
    table_analysis['insight_confidence'] = {
        'trend': insight_engine.build_insight_confidence(table_analysis, 'trend'),
        'correlation': insight_engine.build_insight_confidence(table_analysis, 'correlation'),
        'segment': insight_engine.build_insight_confidence(table_analysis, 'segment'),
        'diagnostic': insight_engine.build_insight_confidence(table_analysis, 'diagnostic'),
        'outlier': insight_engine.build_insight_confidence(table_analysis, 'outlier'),
    }
    table_analysis['ranked_insights'] = insight_engine.rank_table_insights(table_analysis)
    table_analysis['insight_bundle'] = insight_engine.build_insight_bundle(table_analysis)
    return table_analysis


def build_table_analysis(
    profile: dict,
    business_context: str = '',
    progress_guard=None,
) -> dict:
    dataframe = profile['dataframe']
    row_count = int(len(dataframe.index))
    column_count = int(len(dataframe.columns))
    total_cells = row_count * column_count
    non_null_cells = int(dataframe.notna().sum().sum()) if total_cells else 0

    numeric_columns = [
        column['name']
        for column in profile['columns']
        if column['inferred_type'] in {'integer', 'decimal'}
    ]
    datetime_columns = [
        column['name']
        for column in profile['columns']
        if column['inferred_type'] == 'datetime'
    ]
    categorical_columns = [
        column['name']
        for column in profile['columns']
        if column['inferred_type'] in {'string', 'text', 'boolean'}
    ]
    if not business_context:
        business_context = insight_engine.build_business_context(
            dataframe,
            [column['name'] for column in profile.get('columns', [])],
        )
    if progress_guard:
        progress_guard()

    measure_column = choose_measure_column(dataframe, numeric_columns)
    date_column = choose_date_column(dataframe, datetime_columns)
    top_numeric_metrics = build_numeric_summaries(dataframe, numeric_columns)
    top_dimensions = build_category_summaries(dataframe, categorical_columns)
    if progress_guard:
        progress_guard()
    lead_dimension_column = top_dimensions[0]['column'] if top_dimensions else ''
    time_series = insight_engine.build_time_series(dataframe, date_column, measure_column)
    seasonality_analysis = insight_engine.build_seasonality_analysis(dataframe, date_column, measure_column)
    forecast = insight_engine.build_trend_forecast(time_series['points']) if time_series else {'forecast_points': []}
    if time_series:
        time_series['forecast'] = forecast
        time_series['forecast_points'] = forecast.get('forecast_points', [])
    correlation_pairs = insight_engine.build_correlation_pairs(dataframe, numeric_columns)
    outlier_watchlist = insight_engine.build_outlier_watchlist(dataframe, numeric_columns, lead_dimension_column)
    text_watchlist = build_text_watchlist(dataframe, categorical_columns)
    segment_clusters = insight_engine.build_segment_clusters(dataframe, numeric_columns, categorical_columns)
    if progress_guard:
        progress_guard()
    segment_benchmarks = insight_engine.build_segment_benchmarks(dataframe, lead_dimension_column, measure_column)
    change_contribution = insight_engine.build_change_contribution(dataframe, date_column, lead_dimension_column, measure_column)
    quality_watchlist = build_quality_watchlist(profile, row_count)
    null_impact = build_null_impact(dataframe, quality_watchlist, measure_column, lead_dimension_column)
    null_patterns = build_null_patterns(dataframe, date_column, quality_watchlist)
    if progress_guard:
        progress_guard()

    if top_dimensions and segment_benchmarks:
        benchmark_lookup = {item['label']: item for item in segment_benchmarks}
        enriched_values = []
        for item in top_dimensions[0]['top_values']:
            benchmark = benchmark_lookup.get(str(item['label']))
            enriched_values.append({
                **item,
                'benchmark_delta_pct': benchmark.get('delta_pct') if benchmark else 0,
                'benchmark_status': benchmark.get('status') if benchmark else 'on_par',
            })
        top_dimensions[0]['top_values'] = enriched_values
        top_dimensions[0]['benchmarks'] = segment_benchmarks

    provisional_table = {
        'name': profile['name'],
        'top_dimensions': top_dimensions,
        'top_numeric_metrics': top_numeric_metrics,
        'time_series': time_series,
        'correlation_pairs': correlation_pairs,
        'outlier_watchlist': outlier_watchlist,
    }
    dimension_story_chart = visual_engine.build_dimension_story_chart(provisional_table)
    treemap_chart = visual_engine.build_treemap_chart(
        dataframe,
        (top_dimensions[0]['column'] if top_dimensions else ''),
        measure_column,
        profile['name'],
    )
    scatter_chart = visual_engine.build_scatter_chart(dataframe, correlation_pairs, profile['name'])
    heatmap_chart = visual_engine.build_heatmap_chart(dataframe, numeric_columns, profile['name'])
    sankey_chart = visual_engine.build_sankey_chart(dataframe, categorical_columns, measure_column, profile['name'])
    geo_map_chart = visual_engine.build_geo_map_chart(dataframe, categorical_columns, measure_column, profile['name'])
    radar_chart = visual_engine.build_radar_chart(dataframe, top_dimensions, top_numeric_metrics, profile['name'])
    if progress_guard:
        progress_guard()
    table_analysis = {
        'name': profile['name'],
        'row_count': row_count,
        'column_count': column_count,
        'primary_key_name': profile.get('primary_key_name', ''),
        'completeness_ratio': safe_ratio(non_null_cells, total_cells),
        'business_context': business_context,
        'numeric_columns_count': len(numeric_columns),
        'categorical_columns_count': len(categorical_columns),
        'datetime_columns_count': len(datetime_columns),
        'focus_measure_column': measure_column,
        'focus_date_column': date_column,
        'top_numeric_metrics': top_numeric_metrics,
        'top_dimensions': top_dimensions,
        'time_series': time_series,
        'seasonality_analysis': seasonality_analysis,
        'trend_summary': insight_engine.build_trend_summary(time_series),
        'quality_watchlist': quality_watchlist,
        'null_impact': null_impact,
        'null_patterns': null_patterns,
        'correlation_pairs': correlation_pairs,
        'outlier_watchlist': outlier_watchlist,
        'text_watchlist': text_watchlist,
        'segment_clusters': segment_clusters,
        'segment_benchmarks': segment_benchmarks,
        'change_contribution': change_contribution,
        'dimension_story_chart': dimension_story_chart,
        'treemap_chart': treemap_chart,
        'scatter_chart': scatter_chart,
        'heatmap_chart': heatmap_chart,
        'sankey_chart': sankey_chart,
        'geo_map_chart': geo_map_chart,
        'radar_chart': radar_chart,
        'sample_rows': build_sample_rows(dataframe),
    }

    table_analysis = apply_insight_engine_layers(table_analysis)
    table_analysis['analysis_modes'] = build_analysis_modes(table_analysis)
    table_analysis['recommended_analyses'] = build_recommended_analyses(table_analysis)
    table_analysis['field_highlights'] = build_field_highlights(table_analysis)
    table_analysis['hero_kpi'] = visual_engine.build_hero_kpi(table_analysis, business_context or 'dataset de negocio')
    return table_analysis


def build_single_table_insights(table: dict, relationships: list[dict]) -> list[str]:
    top_dimension = (table.get('top_dimensions') or [None])[0] or {}
    dominant = (top_dimension.get('top_values') or [None])[0] or {}
    hero_kpi = table.get('hero_kpi') or build_hero_kpi(table, table.get('business_context', 'dataset de negocio'))
    quality_impact = (table.get('null_impact') or [None])[0] or {}
    quality_issue = (table.get('quality_watchlist') or [None])[0] or {}
    trend = table.get('trend_summary') or {}
    seasonality = table.get('seasonality_analysis') or {}
    contributions = table.get('change_contribution') or []
    lead_contribution = contributions[0] if contributions else None
    benchmarks = table.get('segment_benchmarks') or []
    lead_benchmark = benchmarks[0] if benchmarks else None
    ranked_insights = table.get('ranked_insights') or []
    lead_ranked = (ranked_insights[0] if ranked_insights else {}) or {}
    diagnostic_chain = table.get('diagnostic_chain') or {}
    business_impact = table.get('business_impact') or {}
    business_context = table.get('business_context', 'dataset de negocio')

    situation = (
        f'{table["name"]} es un {business_context} con {table["row_count"]:,} filas '
        f'donde el indicador clave es {hero_kpi["value"]} en {hero_kpi["label"]}.'
    )
    situation = lead_ranked.get('title') or situation
    if trend.get('change_percent') is not None:
        direction = 'creciendo' if float(trend.get('change_value', 0) or 0) >= 0 else 'cayendo'
        complication = (
            f'La metrica principal lleva {direction} {abs(float(trend["change_percent"])):.1f}% '
            f'desde {trend["start_label"]}'
        )
        if lead_contribution:
            complication += f', impulsada principalmente por {lead_contribution["label"]}.'
        elif seasonality.get('detected'):
            complication += f', con patron estacional en {seasonality["strongest_periodicity"]}.'
        else:
            complication += '.'
    elif dominant:
        complication = (
            f'{dominant.get("label", "un segmento")} concentra '
            f'{round(float(dominant.get("share", 0) or 0) * 100, 1)}% de los registros'
        )
        benchmark_delta = float(dominant.get('benchmark_delta_pct', 0) or 0)
        complication += f' y rinde {benchmark_delta:+.1f}% vs el promedio interno.' if benchmark_delta else '.'
    else:
        quality_column = quality_issue.get('column') or quality_impact.get('column')
        if quality_column:
            complication = (
                f'{quality_column} tiene solo {quality_issue.get("completeness_percent", "?")}% de completitud '
                f'e impacta {quality_impact.get("measure_impact_pct", "?")}% de la medida central.'
            )
        else:
            complication = 'La estructura disponible permite una lectura ejecutiva inicial.'
    if diagnostic_chain.get('root_cause_hypothesis'):
        complication = diagnostic_chain['root_cause_hypothesis']

    implication = (
        f'El KPI dominante hoy es {hero_kpi["value"]} en {hero_kpi["label"]}; '
        'si no se explica bien su driver, se bloquean decisiones de priorizacion y seguimiento.'
    )
    if business_impact:
        implication += (
            f' El impacto estimado ya equivale a {format_compact_number(business_impact["impact_value"])} '
            f'{business_impact["impact_unit"]} en {business_impact["impact_label"]}.'
        )
    if lead_contribution and abs(float(lead_contribution.get('contribution_pct', 0) or 0)) >= 40:
        implication += f' {lead_contribution["label"]} ya concentra el mayor impacto sobre el cambio observado.'
    elif lead_benchmark and abs(float(lead_benchmark.get('delta_pct', 0) or 0)) >= 10:
        implication += (
            f' {lead_benchmark["label"]} ya se desvía {lead_benchmark["delta_pct"]:+.1f}% '
            'del baseline interno.'
        )
    elif quality_impact:
        implication += (
            f' Los vacios en {quality_impact["column"]} ya tocan '
            f'{quality_impact["measure_impact_pct"]}% de la metrica central.'
        )

    if trend.get('change_percent') is not None:
        action = 'Profundiza primero en tendencia, benchmark de segmentos y contribucion al cambio para separar crecimiento real de ruido operativo.'
    elif dominant:
        action = f'Separa a {dominant.get("label", "el segmento lider")} del resto y compara volumen, benchmark y calidad antes de definir prioridades.'
    else:
        action = 'Corrige primero los vacios de calidad con mayor impacto antes de automatizar conclusiones o forecasts.'
    action = lead_ranked.get('action_hint') or action

    arc = build_narrative_arc(
        business_context=business_context,
        question=f'Que cambia de forma mas importante en {table["name"]}?',
        situation=situation,
        complication=complication,
        implication=implication,
        action=action,
        ranked_insights=ranked_insights,
        diagnostic_chain=diagnostic_chain,
        stats={
            'hero_kpi': hero_kpi,
            'trend': trend,
            'dominant_segment': dominant,
            'seasonality': seasonality,
            'top_contribution': lead_contribution,
            'top_benchmark': lead_benchmark,
            'quality_issue': quality_issue,
            'null_impact': quality_impact,
            'business_impact': business_impact,
            'ranked_insights': ranked_insights,
            'diagnostic_chain': diagnostic_chain,
            'confidence': table.get('insight_confidence', {}),
        },
    )

    insights = [arc['situation'], arc['complication'], arc['implication'], arc['action']]
    if relationships and len(insights) < 4:
        relation = relationships[0]
        insights.append(
            f'Existe una relacion detectada entre {relation["source_table_name"]}.{relation["source_column_name"]} y {relation["target_table_name"]}.{relation["target_column_name"]}.'
        )
    return insights[:4]


def build_headline_insights(overview: dict, tables: list[dict], relationships: list[dict], business_context: str = '') -> list[str]:
    effective_context = business_context or overview.get('business_context', 'dataset de negocio')
    if len(tables) == 1:
        return build_single_table_insights(tables[0], relationships)

    largest = max(tables, key=lambda item: item['row_count']) if tables else None
    weakest_quality = min(tables, key=lambda item: item['completeness_ratio']) if tables else None
    strongest = max(relationships, key=lambda item: item['confidence']) if relationships else None
    best_trend = overview.get('best_trend') or {}
    top_ranked_insights = [
        {**insight, 'table_name': table['name']}
        for table in tables[:3]
        for insight in (table.get('ranked_insights') or [])[:1]
    ]
    lead_ranked = (top_ranked_insights[0] if top_ranked_insights else {}) or {}

    arc = build_narrative_arc(
        business_context=effective_context,
        question='Que historia estructural domina el dataset?',
        situation=lead_ranked.get('title') or (
            f'El dataset integra {overview.get("tables_count", len(tables))} tablas y {overview.get("total_rows", 0):,} filas '
            f'dentro de un {effective_context}.'
        ),
        complication=(
            f'La mayor tension esta entre volumen y confiabilidad: {largest["name"] if largest else "la tabla principal"} concentra masa critica, '
            f'pero {weakest_quality["name"] if weakest_quality else "otra tabla"} reduce calidad util.'
        ),
        implication=(
            f'Si no se prioriza bien la topologia, se frena la lectura de {best_trend.get("value_label", "la metrica clave")} '
            'y se sobrecarga el analisis con tablas menos accionables.'
        ),
        action=lead_ranked.get('action_hint') or (
            'Empieza por la tabla lider, valida la relacion estructural principal y usa la mejor serie temporal como columna vertebral del deck.'
        ),
        ranked_insights=top_ranked_insights,
        diagnostic_chain=(largest or {}).get('diagnostic_chain'),
        stats={
            'largest_table': largest,
            'weakest_quality': weakest_quality,
            'strongest_relationship': strongest,
            'best_trend': best_trend,
            'top_ranked_insights': top_ranked_insights,
        },
    )
    insights = [arc['situation'], arc['complication'], arc['implication'], arc['action']]
    return insights[:4]


def build_quality_chart(table: dict) -> dict | None:
    quality_watchlist = table.get('quality_watchlist') or []
    if not quality_watchlist:
        return None

    return {
        'chart_type': 'bar',
        'title': 'Campos con menor completitud',
        'subtitle': f'Columnas con mas vacios en {table["name"]}',
        'data': [
            {'label': item['column'], 'value': item['completeness_percent']}
            for item in quality_watchlist
        ],
        'value_label': '% completitud',
        'orientation': 'horizontal',
    }


def build_correlation_chart(table: dict) -> dict | None:
    correlation_pairs = table.get('correlation_pairs') or []
    if not correlation_pairs:
        return None

    return {
        'chart_type': 'bar',
        'title': 'Correlaciones mas fuertes',
        'subtitle': f'Variables que se mueven juntas en {table["name"]}',
        'data': [
            {
                'label': f'{item["left_column"]} x {item["right_column"]}',
                'value': round(item['absolute_correlation'] * 100, 1),
            }
            for item in correlation_pairs
        ],
        'value_label': '% correlacion',
        'orientation': 'horizontal',
    }


def build_outlier_chart(table: dict) -> dict | None:
    outlier_watchlist = table.get('outlier_watchlist') or []
    if not outlier_watchlist:
        return None

    return {
        'chart_type': 'bar',
        'title': 'Columnas con mas outliers',
        'subtitle': f'Variables con mayor dispersion atipica en {table["name"]}',
        'data': [
            {
                'label': item['column'],
                'value': item['outlier_percent'],
            }
            for item in outlier_watchlist
        ],
        'value_label': '% outliers',
        'orientation': 'horizontal',
    }


def build_column_mix_chart(table: dict) -> dict:
    return {
        'chart_type': 'bar',
        'title': f'Mix de columnas en {table["name"]}',
        'subtitle': 'Como se reparte la estructura del dataset',
        'data': [
            {'label': 'Numericas', 'value': table['numeric_columns_count']},
            {'label': 'Categoricas', 'value': table['categorical_columns_count']},
            {'label': 'Fecha', 'value': table['datetime_columns_count']},
        ],
        'value_label': 'columnas',
        'orientation': 'vertical',
    }


def build_structure_chart(table: dict) -> dict:
    return {
        'chart_type': 'bar',
        'title': f'Huella estructural de {table["name"]}',
        'subtitle': 'Volumen y complejidad del dataset cargado',
        'data': [
            {'label': 'Filas', 'value': table['row_count']},
            {'label': 'Columnas', 'value': table['column_count']},
            {'label': 'Numericas', 'value': table['numeric_columns_count']},
            {'label': 'Categoricas', 'value': table['categorical_columns_count']},
        ],
        'value_label': 'conteo',
        'orientation': 'vertical',
    }


def build_benchmark_chart(table: dict) -> dict | None:
    benchmarks = table.get('segment_benchmarks') or []
    if not benchmarks:
        return None

    chart_type = choose_best_chart('deviation', {
        'n_categories': len(benchmarks),
        'n_points': len(benchmarks),
        'has_negatives': any(item.get('delta_pct', 0) < 0 for item in benchmarks),
        'is_temporal': False,
        'n_series': 1,
    })
    return {
        'chart_type': chart_type,
        'title': 'Benchmark interno por segmento',
        'subtitle': 'Desvio de cada categoria frente al promedio global',
        'data': [
            {
                'label': item['label'],
                'value': item['average'],
                'secondary_value': item['baseline'],
                'delta_pct': item['delta_pct'],
                'status': item['status'],
            }
            for item in benchmarks[:6]
        ],
        'value_label': table.get('focus_measure_column') or 'valor promedio',
        'secondary_label': 'baseline',
        'orientation': 'horizontal',
    }


def build_change_contribution_chart(table: dict) -> dict | None:
    contributions = table.get('change_contribution') or []
    if not contributions:
        return None

    chart_type = choose_best_chart('composition', {
        'n_categories': len(contributions),
        'n_points': len(contributions),
        'has_negatives': any(item.get('delta', 0) < 0 for item in contributions),
        'is_temporal': False,
        'n_series': 1,
    })
    base_chart_type = 'bar' if chart_type == 'bar_horizontal' else chart_type
    return {
        'chart_type': base_chart_type,
        'title': 'Quien explica el cambio observado',
        'subtitle': 'Contribucion por categoria entre la primera y la segunda mitad del periodo',
        'data': [
            {
                'label': item['label'],
                'value': item['delta'],
                'contribution_pct': item['contribution_pct'],
            }
            for item in contributions[:6]
        ],
        'value_label': 'delta',
        'secondary_label': '% contribucion',
        'orientation': 'horizontal',
    }


def build_relationship_sankey_chart(tables: list[dict], relationships: list[dict]) -> dict | None:
    if not relationships:
        return None

    table_rows = {table['name']: table['row_count'] for table in tables}
    node_index = {}
    nodes = []

    def ensure_node(label: str) -> int:
        if label not in node_index:
            node_index[label] = len(nodes)
            nodes.append({'name': label, 'group': 'tabla'})
        return node_index[label]

    links = []
    for relationship in relationships:
        source_name = relationship['source_table_name']
        target_name = relationship['target_table_name']
        source_index = ensure_node(source_name)
        target_index = ensure_node(target_name)
        value = max(table_rows.get(source_name, 0), table_rows.get(target_name, 0)) or 1
        links.append({
            'source': source_index,
            'target': target_index,
            'value': round(float(value), 4),
        })

    return {
        'chart_type': 'sankey',
        'title': 'Flujo estructural entre tablas',
        'subtitle': 'Relaciones inferidas dentro del bundle cargado',
        'data': {
            'nodes': nodes,
            'links': links,
        },
        'value_label': 'filas relacionadas',
    }




def build_story_payload(
    *,
    stage: str,
    question: str,
    finding: str,
    conclusion: str,
    recommendation: str,
    complication: str = '',
    signal_value: str | float | int | None = None,
    signal_label: str = '',
    evidence: list[str] | None = None,
    stats: dict | None = None,
    business_context: str = '',
    insight_type: str = 'trend',
    table: dict | None = None,
) -> dict:
    confidence = (
        (table.get('insight_confidence') or {}).get(insight_type)
        if table
        else None
    ) or (build_insight_confidence(table or {}, insight_type) if table else None)
    hero_kpi = (table.get('hero_kpi') if table else None) or (
        build_hero_kpi(table, business_context) if table else None
    )
    enriched_stats = {
        **(stats or {}),
        'hero_kpi': hero_kpi,
        'seasonality': (table or {}).get('seasonality_analysis'),
        'top_benchmark': ((table or {}).get('segment_benchmarks') or [None])[0],
        'top_contribution': ((table or {}).get('change_contribution') or [None])[0],
        'diagnostic_chain': (table or {}).get('diagnostic_chain'),
        'business_impact': (table or {}).get('business_impact'),
        'ranked_insights': (table or {}).get('ranked_insights', []),
        'business_context': business_context or (table or {}).get('business_context', 'dataset de negocio'),
        'insight_confidence': ((table or {}).get('insight_confidence') or {}).get(insight_type, confidence or {}),
    }
    arc = build_narrative_arc(
        business_context=business_context or (table or {}).get('business_context', 'dataset de negocio'),
        question=question,
        situation=finding,
        complication=complication or (evidence[0] if evidence else finding),
        implication=conclusion,
        action=recommendation,
        ranked_insights=(table or {}).get('ranked_insights', []),
        diagnostic_chain=(table or {}).get('diagnostic_chain'),
        stats=enriched_stats | {
            'finding': finding,
            'conclusion': conclusion,
            'recommendation': recommendation,
            'signal_value': signal_value,
            'evidence': evidence or [],
            'confidence': confidence or {},
        },
    )
    payload = {
        'stage': stage,
        'question': arc['question'],
        'situation': arc['situation'],
        'complication': arc['complication'],
        'severity': arc['severity'],
        'implication': arc['implication'],
        'action': arc['action'],
        'finding': arc['situation'],
        'conclusion': arc['implication'],
        'recommendation': arc['action'],
    }

    if signal_value not in (None, ''):
        payload['signal_value'] = signal_value
    if signal_label:
        payload['signal_label'] = signal_label
    if evidence:
        payload['evidence'] = evidence[:4]
    if confidence:
        payload['confidence'] = confidence
    if hero_kpi:
        payload['hero_kpi'] = hero_kpi
    payload['insight_type'] = insight_type
    payload['signal_type'] = insight_type

    return payload


LAYOUT_RULES = {
    (1, 'default'): 'chart_dominant',
    (2, 'Exploracion Temporal'): 'dual_chart',
    (2, 'Segmentacion'): 'split_horizontal',
    (2, 'Benchmarking'): 'dual_chart',
    (2, 'Causalidad'): 'split_horizontal',
    (2, 'Drivers'): 'split_horizontal',
    (2, 'Riesgo'): 'dual_chart',
}


def _resolve_signal_color(signal_value, stage: str, metric_context: str = '') -> str:
    try:
        numeric = float(str(signal_value).replace('%', '').replace('+', '').strip())
        if stage == 'Riesgo':
            return 'negative' if numeric < 85 else 'warning'
        higher_is_better = infer_higher_is_better(metric_context or stage)
        if numeric == 0:
            return 'neutral'
        if higher_is_better:
            return 'positive' if numeric > 0 else 'negative'
        return 'positive' if numeric < 0 else 'negative'
    except (TypeError, ValueError):
        return 'neutral'


def _severity_color(text: str) -> str:
    critical_keywords = {
        'invalida', 'bloquea', 'riesgo alto', 'estructural', 'deterioro',
        'sesgo', 'distorsion', 'dependencia critica',
    }
    warning_keywords = {
        'brecha', 'divergen', 'oculta', 'modera', 'conviene revisar',
    }
    text_lower = text.lower()
    if any(keyword in text_lower for keyword in critical_keywords):
        return 'negative'
    if any(keyword in text_lower for keyword in warning_keywords):
        return 'warning'
    return 'neutral'


def _decorate_supporting_chart(
    chart: dict,
    role: str = 'supporting',
    size_hint: str = 'small',
    metric_context: str = '',
    business_context: str = '',
) -> dict:
    decorated = {
        **chart,
        'role': chart.get('role', role),
        'size_hint': chart.get('size_hint', size_hint),
    }
    chart_type = decorated.get('chart_type')
    chart_data = decorated.get('data') or []
    annotation_chart_types = {'bar', 'bar_horizontal', 'line', 'combo', 'bullet', 'waterfall'}
    reference_chart_types = {'bar', 'bar_horizontal', 'line', 'combo'}

    if chart_data and chart_type in annotation_chart_types and not decorated.get('annotations'):
        decorated['annotations'] = build_chart_annotations(chart_data, chart_type)
    if chart_data and chart_type in reference_chart_types and not decorated.get('reference_lines'):
        decorated['reference_lines'] = build_reference_lines(
            chart_data,
            metric_context,
            business_context,
        )

    return decorated


def _build_quality_impact_chart(table: dict) -> dict | None:
    null_impact = table.get('null_impact') or []
    data = [
        {
            'label': item['column'],
            'value': item['measure_impact_pct'],
        }
        for item in null_impact[:5]
        if item.get('measure_impact_pct', 0) > 0
    ]
    if not data:
        return None
    chart = {
        'chart_type': 'bar',
        'title': 'Impacto sobre la metrica central',
        'subtitle': '% de la medida principal afectado por cada campo vacio',
        'data': data,
        'value_label': '% impacto',
        'orientation': 'horizontal',
    }
    chart['data'] = build_semantic_colors(chart['data'], table.get('focus_measure_column') or '')
    chart['annotations'] = build_chart_annotations(chart['data'], chart['chart_type'])
    chart['reference_lines'] = build_reference_lines(
        chart['data'],
        table.get('focus_measure_column'),
        table.get('business_context', ''),
    )
    return chart


def _build_time_context_chart(table: dict) -> dict | None:
    time_series = table.get('time_series') or {}
    points = time_series.get('points') or []
    if len(points) < 4:
        return None
    recent_points = list(points[-8:])
    chart = {
        'chart_type': 'line',
        'title': f'Tendencia de {time_series.get("value_label", "la metrica central")}',
        'subtitle': 'Contexto temporal del cambio analizado',
        'data': recent_points,
        'value_label': time_series.get('value_label', 'valor'),
    }
    chart['data'] = build_semantic_colors(chart['data'], table.get('focus_measure_column') or '')
    chart['annotations'] = build_chart_annotations(chart['data'], chart['chart_type'])
    chart['reference_lines'] = build_reference_lines(
        chart['data'],
        table.get('focus_measure_column'),
        table.get('business_context', ''),
    )
    return chart


def _select_supporting_charts(
    table: dict,
    primary_chart: dict,
    narrative: dict,
    max_secondary: int = 2,
) -> list[dict]:
    supporting = []
    primary_type = primary_chart.get('chart_type', '')
    stage = narrative.get('stage', '')
    metric_context = (
        table.get('focus_measure_column')
        or primary_chart.get('value_label')
        or narrative.get('signal_label', '')
    )
    business_context = table.get('business_context', '')

    if primary_type in {'combo', 'line', 'trend'}:
        contributions = table.get('change_contribution') or []
        if contributions:
            lead = contributions[0]
            pct = abs(float(lead.get('contribution_pct', 0) or 0))
            if pct >= 25:
                contribution_chart = build_change_contribution_chart(table)
                if contribution_chart:
                    supporting.append({
                        **contribution_chart,
                        'narrative_link': (
                            f'Explica el driver de la complicacion: '
                            f'{lead["label"]} aporta {lead["contribution_pct"]}%'
                        ),
                    })

    if primary_type in {'bar', 'donut', 'combo'} and stage == 'Segmentacion':
        benchmark_chart = build_benchmark_chart(table)
        benchmarks = table.get('segment_benchmarks') or []
        if benchmark_chart and benchmarks:
            best = max(benchmarks, key=lambda item: item['delta_pct'])
            worst = min(benchmarks, key=lambda item: item['delta_pct'])
            gap = abs(float(best['delta_pct']) - float(worst['delta_pct']))
            if gap >= 15:
                supporting.append({
                    **benchmark_chart,
                    'narrative_link': (
                        f'Demuestra la complicacion: brecha de {gap:.1f}% '
                        f'entre {best["label"]} y {worst["label"]}'
                    ),
                })

    if stage == 'Benchmarking':
        strongest = (table.get('correlation_pairs') or [None])[0]
        scatter_chart = table.get('scatter_chart')
        if scatter_chart and strongest and float(strongest.get('absolute_correlation', 0) or 0) >= 0.55:
            supporting.append({
                **scatter_chart,
                'size_hint': 'medium',
                'narrative_link': (
                    'Valida si el segmento lider tambien se sostiene frente a '
                    'las variables que mejor se correlacionan.'
                ),
            })

    if stage == 'Drivers':
        if primary_type == 'bar':
            if table.get('heatmap_chart'):
                supporting.append({
                    **table['heatmap_chart'],
                    'narrative_link': 'Contexto: panorama completo de correlaciones para validar que el par lider no es aislado.',
                })
            elif table.get('scatter_chart'):
                supporting.append({
                    **table['scatter_chart'],
                    'size_hint': 'medium',
                    'narrative_link': 'Detalle visual del par con mayor relacion identificado en el ranking.',
                })
        elif primary_type == 'scatter' and table.get('heatmap_chart'):
            supporting.append({
                **table['heatmap_chart'],
                'narrative_link': 'Contexto: panorama completo de correlaciones para validar que el par lider no es aislado.',
            })
        elif primary_type == 'heatmap' and table.get('scatter_chart'):
            supporting.append({
                **table['scatter_chart'],
                'size_hint': 'medium',
                'narrative_link': 'Detalle del par mas fuerte identificado en el heatmap.',
            })

    if primary_type == 'scatter':
        heatmap_chart = table.get('heatmap_chart')
        if heatmap_chart:
            supporting.append({
                **heatmap_chart,
                'narrative_link': 'Contexto: esta es la correlacion mas fuerte del dataset?',
            })
    elif primary_type == 'heatmap':
        scatter_chart = table.get('scatter_chart')
        if scatter_chart:
            supporting.append({
                **scatter_chart,
                'size_hint': 'medium',
                'narrative_link': 'Detalle del par mas fuerte identificado en el heatmap.',
            })

    if stage == 'Riesgo':
        impact_chart = _build_quality_impact_chart(table)
        if impact_chart:
            supporting.append({
                **impact_chart,
                'narrative_link': 'Cuantifica la complicacion: porcentaje real de la medida en riesgo.',
            })

    if stage == 'Causalidad':
        time_context_chart = _build_time_context_chart(table)
        if time_context_chart:
            supporting.append({
                **time_context_chart,
                'narrative_link': 'Contexto: el cambio es reciente o viene de antes?',
            })

    deduped = []
    seen = set()
    for chart in supporting:
        identity = (
            chart.get('chart_type'),
            chart.get('title'),
            chart.get('narrative_link'),
        )
        if identity in seen:
            continue
        deduped.append(_decorate_supporting_chart(
            chart,
            size_hint=chart.get('size_hint', 'small'),
            metric_context=metric_context,
            business_context=business_context,
        ))
        seen.add(identity)

    return deduped[:max_secondary]


def build_text_blocks_for_slide(
    narrative: dict,
    table: dict,
    primary_chart: dict,
    supporting_charts: list[dict],
) -> list[dict]:
    del primary_chart
    blocks = []
    stage = narrative.get('stage', '')
    hero_kpi = table.get('hero_kpi') or {}
    signal_value = narrative.get('signal_value')
    signal_label = narrative.get('signal_label', '')
    complication = narrative.get('complication', '')
    conclusion = narrative.get('conclusion', '')
    metric_context = signal_label or table.get('focus_measure_column') or hero_kpi.get('label', '')

    if signal_value not in (None, ''):
        blocks.append({
            'role': 'kpi_badge',
            'position': 'top-right',
            'value': str(signal_value),
            'label': signal_label,
            'content': '',
            'color_signal': _resolve_signal_color(signal_value, stage, metric_context),
            'size': 'large',
        })
    elif hero_kpi.get('value'):
        blocks.append({
            'role': 'kpi_badge',
            'position': 'top-right',
            'value': hero_kpi['value'],
            'label': hero_kpi.get('label', ''),
            'content': '',
            'color_signal': hero_kpi.get('color_signal', 'neutral'),
            'size': 'large',
        })

    finding = narrative.get('finding', '')
    if finding:
        blocks.append({
            'role': 'finding',
            'position': 'bottom-left',
            'content': finding,
            'color_signal': 'neutral',
            'size': 'normal',
        })

    if supporting_charts:
        if complication:
            blocks.append({
                'role': 'complication',
                'position': 'bottom-right',
                'content': complication,
                'color_signal': _severity_color(complication),
                'size': 'normal',
            })
    elif conclusion:
        blocks.append({
            'role': 'conclusion',
            'position': 'bottom-right',
            'content': conclusion,
            'color_signal': 'neutral',
            'size': 'normal',
        })

    evidence = narrative.get('evidence') or []
    if stage in {'Riesgo', 'Causalidad'} and evidence:
        for item in evidence[:3]:
            blocks.append({
                'role': 'evidence',
                'position': 'sidebar-right',
                'content': item,
                'color_signal': 'neutral',
                'size': 'small',
            })

    action = narrative.get('action', '')
    if action and not supporting_charts and not any(
        block.get('role') == 'action' and block.get('position') == 'bottom-right'
        for block in blocks
    ):
        blocks.append({
            'role': 'action',
            'position': 'bottom-right',
            'content': action,
            'color_signal': 'neutral',
            'size': 'normal',
        })

    return blocks


def make_chart_slide(
    primary_chart: dict,
    narrative: dict | None = None,
    table: dict | None = None,
    *,
    supporting_charts: list[dict] | None = None,
    text_blocks: list[dict] | None = None,
) -> dict:
    return visual_engine.render_slide(
        {
            'slide_type': 'chart',
            'primary_chart': primary_chart,
            'narrative': narrative or {},
            'supporting_charts': list(supporting_charts or []),
            'text_blocks': text_blocks,
        },
        table=table,
        story_objective=(narrative or {}).get('story_objective'),
    )


def build_combo_story_chart(
    *,
    title: str,
    subtitle: str,
    data: list[dict],
    value_label: str,
    secondary_label: str,
    secondary_domain: list[int] | None = None,
) -> dict:
    chart = {
        'chart_type': 'combo',
        'title': title,
        'subtitle': subtitle,
        'data': data,
        'value_label': value_label,
        'secondary_label': secondary_label,
    }
    if secondary_domain:
        chart['secondary_domain'] = secondary_domain
    return chart


def build_time_story_slide(table: dict) -> dict | None:
    time_series = table.get('time_series')
    trend_summary = table.get('trend_summary')
    if not time_series or len(time_series.get('points', [])) < 2:
        return None

    raw_points = list(time_series['points'])
    forecast_points = time_series.get('forecast_points') or []
    combo_points = []
    for index, point in enumerate(raw_points):
        window = raw_points[max(0, index - 2):index + 1]
        rolling_average = sum(float(item['value']) for item in window) / len(window)
        combo_points.append({
            'label': point['label'],
            'value': point['value'],
            'secondary_value': round(rolling_average, 4),
        })
    combo_points = build_semantic_colors(combo_points, table.get('focus_measure_column') or table.get('business_context', ''))
    for point in forecast_points:
        combo_points.append({
            'label': point['label'],
            'value': point['value'],
            'secondary_value': point.get('lower', point['value']),
            'forecast_upper': point.get('upper'),
            'is_forecast': True,
            'color_signal': 'neutral',
        })
    annotations = build_chart_annotations(combo_points[:len(raw_points)], 'combo')
    reference_lines = build_reference_lines(combo_points[:len(raw_points)], table.get('focus_measure_column'), table.get('business_context', ''))

    peak_point = max(raw_points, key=lambda item: item['value'])
    low_point = min(raw_points, key=lambda item: item['value'])
    seasonality = table.get('seasonality_analysis') or {}
    contributions = table.get('change_contribution') or []
    lead_contribution = contributions[0] if contributions else None

    if trend_summary and trend_summary.get('change_percent') is not None:
        change_percent = float(trend_summary['change_percent'])
        if abs(change_percent) >= 30:
            severity = 'un cambio estructural que requiere atencion inmediata'
        elif abs(change_percent) >= 10:
            severity = 'una tendencia material que conviene monitorear'
        else:
            severity = 'una variacion moderada dentro del rango operativo'

        conclusion = (
            f'La serie muestra {severity} entre {trend_summary["start_label"]} y {trend_summary["end_label"]}.'
        )
        if seasonality.get('detected'):
            conclusion += f' El patron {seasonality["strongest_periodicity"]} explica parte del movimiento.'
        if lead_contribution and abs(float(lead_contribution.get('contribution_pct', 0) or 0)) >= 40:
            conclusion += f' {lead_contribution["label"]} es el principal responsable del cambio.'

        if lead_contribution and abs(float(lead_contribution.get('contribution_pct', 0) or 0)) >= 40:
            recommendation = (
                f'Empieza por {lead_contribution["label"]}, que hoy explica '
                f'{format_percent(lead_contribution["contribution_pct"], signed=True)} del cambio, '
                'antes de ajustar el forecast global.'
            )
        elif seasonality.get('detected'):
            recommendation = (
                f'Ajusta capacidad, presupuesto o cobertura al patron {seasonality["strongest_periodicity"]}: '
                f'protege {seasonality["peak_period"]} y refuerza el plan para {seasonality["trough_period"]}.'
            )
        elif abs(change_percent) >= 30:
            recommendation = 'Convierte esta serie en un KPI ejecutivo con alertas tempranas y revisa causas raiz antes de escalar decisiones.'
        elif abs(change_percent) >= 10:
            recommendation = 'Monitorea la tendencia en cada cierre y valida si el movimiento reciente se sostiene frente a la referencia movil.'
        else:
            recommendation = 'Manten seguimiento ligero sobre esta serie para separar ruido operativo de una futura inflexion.'
        signal_value = format_percent(change_percent, signed=True)
        signal_label = f'variacion vs {trend_summary["start_label"]}'
    else:
        conclusion = (
            f'La serie cubre {len(raw_points)} periodos y permite leer ritmo, estacionalidad y cambios de nivel.'
        )
        recommendation = 'Manten esta serie como tablero base para detectar inflexiones antes de que lleguen al resultado.'
        signal_value = len(raw_points)
        signal_label = 'periodos observados'

    chart = build_combo_story_chart(
        title=f'{time_series["value_label"]} a lo largo del tiempo',
        subtitle=f'Tendencia mensual de {table["name"]} con forecast y referencia lineal',
        data=combo_points,
        value_label=time_series['value_label'],
        secondary_label='Referencia',
    )
    chart['annotations'] = annotations
    chart['reference_lines'] = reference_lines

    return make_chart_slide(
        chart,
        build_story_payload(
            stage='Exploracion Temporal',
            question=f'Como evoluciona {time_series["value_label"]} a lo largo del tiempo?',
            finding=(
                f'El pico ocurre en {peak_point["label"]} ({format_compact_number(peak_point["value"])})'
                + (
                    f', con patron estacional en {seasonality["strongest_periodicity"]}: '
                    f'{seasonality["peak_period"]} es consistentemente el periodo mas alto '
                    f'y {seasonality["trough_period"]} el mas bajo.'
                    if seasonality.get('detected')
                    else f', con un valle en {low_point["label"]} ({format_compact_number(low_point["value"])}).'
                )
            ),
            complication=(
                f'{lead_contribution["label"]} explica {format_percent(lead_contribution["contribution_pct"], signed=True)} '
                f'del cambio entre la primera y segunda mitad del periodo, pasando de '
                f'{format_compact_number(lead_contribution["before"])} a {format_compact_number(lead_contribution["after"])}.'
                if lead_contribution
                else f'La serie proyecta {len(forecast_points)} periodos adicionales.'
            ),
            conclusion=conclusion,
            recommendation=recommendation,
            signal_value=signal_value,
            signal_label=signal_label,
            evidence=[
                f'Ventana: {raw_points[0]["label"]} a {raw_points[-1]["label"]}',
                f'Pico: {peak_point["label"]} | {format_compact_number(peak_point["value"])}',
                f'Valle: {low_point["label"]} | {format_compact_number(low_point["value"])}',
            ],
            business_context=table.get('business_context', ''),
            insight_type='trend',
            table=table,
        ),
        table=table,
    )


def build_dimension_story_slide(table: dict) -> dict | None:
    top_dimension = (table.get('top_dimensions') or [None])[0]
    if not top_dimension or not top_dimension.get('top_values'):
        return None

    values = top_dimension['top_values'][:6]
    dominant = values[0]
    runner_up = values[1] if len(values) > 1 else None
    chart_choice = choose_best_chart('distribution', {
        'n_categories': len(values),
        'n_points': len(values),
        'has_negatives': False,
        'is_temporal': False,
        'n_series': 1,
    })
    combo_chart = build_combo_story_chart(
        title=f'Concentracion por {top_dimension["column"]}',
        subtitle=f'Registros y participacion relativa dentro de {table["name"]}',
        data=build_semantic_colors([
            {
                'label': item['label'],
                'value': item['count'],
                'secondary_value': round(item['share'] * 100, 1),
            }
            for item in values
        ], top_dimension['column']),
        value_label='registros',
        secondary_label='% participacion',
        secondary_domain=[0, 100],
    )
    combo_chart['chart_type'] = 'combo' if chart_choice in {'combo', 'bar_horizontal'} else chart_choice
    combo_chart['orientation'] = 'horizontal' if chart_choice == 'bar_horizontal' else 'vertical'
    combo_chart['annotations'] = build_chart_annotations(combo_chart['data'], combo_chart['chart_type'])
    combo_chart['reference_lines'] = build_reference_lines(combo_chart['data'], top_dimension['column'], table.get('business_context', ''))

    share_gap = (
        round((dominant['share'] - runner_up['share']) * 100, 1)
        if runner_up
        else round(dominant['share'] * 100, 1)
    )
    dominant_benchmark = float(dominant.get('benchmark_delta_pct', 0) or 0)
    business_context = table.get('business_context', 'dataset de negocio')

    if dominant['share'] >= 0.6:
        concentration_conclusion = (
            f'{dominant["label"]} domina con {round(dominant["share"] * 100, 1)}%: '
            'el dataset es altamente dependiente de este segmento.'
        )
    elif dominant['share'] >= 0.45:
        conclusion_base = 'La concentracion es relevante pero no critica.'
        if dominant_benchmark > 20:
            concentration_conclusion = (
                f'{conclusion_base} Ademas, {dominant["label"]} rinde '
                f'{dominant_benchmark:.1f}% sobre el promedio, lo que refuerza su peso estrategico.'
            )
        elif dominant_benchmark < -10:
            concentration_conclusion = (
                f'{conclusion_base} Sin embargo, {dominant["label"]} rinde '
                f'{abs(dominant_benchmark):.1f}% bajo el promedio: volumen no es equivalente a performance.'
            )
        else:
            concentration_conclusion = f'{conclusion_base} El segmento lider esta alineado con el promedio.'
    else:
        concentration_conclusion = (
            'La distribucion es balanceada, lo que permite comparar segmentos sin sesgo de concentracion.'
        )

    if dominant['share'] >= 0.6:
        recommendation = (
            f'Protege a {dominant["label"]} como segmento critico dentro de {business_context}, '
            'pero construye alertas de dependencia y una estrategia de diversificacion.'
        )
    elif dominant['share'] >= 0.45 and dominant_benchmark > 20:
        recommendation = (
            f'Usa a {dominant["label"]} como referencia comercial y replica sus practicas sobre los segmentos secundarios.'
        )
    elif dominant['share'] >= 0.45 and dominant_benchmark < -10:
        recommendation = (
            f'Separa volumen de performance: {dominant["label"]} necesita una lectura propia antes de asignar mas recursos.'
        )
    else:
        recommendation = (
            f'Usa {top_dimension["column"]} como eje de comparacion en el dashboard para detectar que categorias escalan mejor.'
        )

    return make_chart_slide(
        combo_chart,
        build_story_payload(
            stage='Segmentacion',
            question=f'Que segmentos concentran el mayor peso en {table["name"]}?',
            finding=(
                f'{dominant["label"]} lidera con {round(dominant["share"] * 100, 1)}% de participacion'
                + (
                    f', {share_gap} puntos por encima de {runner_up["label"]}.'
                    if runner_up
                    else '.'
                )
            ),
            complication=(
                f'El benchmark interno muestra que {dominant["label"]} esta '
                f'{float(dominant.get("benchmark_delta_pct", 0) or 0):+.1f}% frente al promedio.'
            ),
            conclusion=concentration_conclusion,
            recommendation=recommendation,
            signal_value=f'{round(dominant["share"] * 100, 1)}%',
            signal_label=f'participacion de {dominant["label"]}',
            evidence=[
                f'Categorias visibles: {len(values)}',
                f'Segmento lider: {dominant["label"]}',
                f'Registros lideres: {format_compact_number(dominant["count"])}',
            ],
            business_context=table.get('business_context', ''),
            insight_type='segment',
            table=table,
        ),
        table=table,
    )


def build_benchmark_story_slide(table: dict) -> dict | None:
    benchmark_chart = build_benchmark_chart(table)
    benchmarks = table.get('segment_benchmarks') or []
    if not benchmark_chart or not benchmarks:
        return None

    best_segment = max(benchmarks, key=lambda item: item['delta_pct'])
    worst_segment = min(benchmarks, key=lambda item: item['delta_pct'])
    gap = abs(float(best_segment['delta_pct']) - float(worst_segment['delta_pct']))
    benchmark_chart['data'] = build_semantic_colors(benchmark_chart['data'], table.get('focus_measure_column') or '')
    benchmark_chart['annotations'] = build_chart_annotations(benchmark_chart['data'], benchmark_chart['chart_type'])
    benchmark_chart['reference_lines'] = build_reference_lines(benchmark_chart['data'], table.get('focus_measure_column'), table.get('business_context', ''))

    if gap >= 50:
        complication = (
            f'La brecha entre {best_segment["label"]} y {worst_segment["label"]} '
            f'es de {gap:.1f}% — una diferencia estructural que invalida el promedio como referencia.'
        )
    elif gap >= 20:
        complication = (
            f'{best_segment["label"]} y {worst_segment["label"]} divergen {gap:.1f}%: '
            'el promedio global oculta una diferencia operativa real.'
        )
    else:
        complication = 'Las variaciones son moderadas pero ya indican segmentos con diferente traccion.'

    conclusion = (
        f'Con una brecha de {gap:.1f}% entre el mejor y el peor segmento, '
        'el benchmark interno es la herramienta mas directa para asignar recursos y prioridades.'
        if gap >= 20
        else 'El benchmark permite vigilar que segmentos estan divergiendo antes de que la brecha se amplíe.'
    )

    return make_chart_slide(
        benchmark_chart,
        build_story_payload(
            stage='Benchmarking',
            question='Que segmentos rinden por encima o por debajo del promedio interno?',
            finding=(
                f'{best_segment["label"]} rinde {best_segment["delta_pct"]}% sobre el baseline, '
                f'mientras {worst_segment["label"]} queda {abs(worst_segment["delta_pct"])}% por debajo.'
            ),
            complication=complication,
            conclusion=conclusion,
            recommendation='Replica practicas del segmento lider y corrige fricciones donde el desvio negativo ya es estructural.',
            signal_value=f'{best_segment["delta_pct"]:+.1f}%',
            signal_label=f'brecha de {best_segment["label"]}',
            evidence=[
                f'Segmentos benchmarkeados: {len(benchmarks)}',
                f'Baseline: {format_compact_number(best_segment["baseline"])}',
            ],
            business_context=table.get('business_context', ''),
            insight_type='segment',
            table=table,
        ),
        table=table,
    )


def build_change_contribution_story_slide(table: dict) -> dict | None:
    contribution_chart = build_change_contribution_chart(table)
    contributions = table.get('change_contribution') or []
    if not contribution_chart or not contributions:
        return None

    lead_change = contributions[0]
    delta_direction = 'impulso' if float(lead_change.get('delta', 0) or 0) >= 0 else 'arrastre'
    pct_abs = abs(float(lead_change.get('contribution_pct', 0) or 0))
    contribution_chart['data'] = build_semantic_colors(contribution_chart['data'], table.get('focus_measure_column') or '')
    contribution_chart['annotations'] = build_chart_annotations(contribution_chart['data'], contribution_chart['chart_type'])
    contribution_chart['reference_lines'] = build_reference_lines(contribution_chart['data'], table.get('focus_measure_column'), table.get('business_context', ''))

    complication = (
        f'{lead_change["label"]} es el principal {delta_direction} con '
        f'{format_compact_number(abs(float(lead_change["delta"] or 0)))} de variacion '
        f'({float(lead_change["contribution_pct"]):+.1f}% del cambio total).'
    )
    recommendation = (
        f'{"Escala" if float(lead_change.get("delta", 0) or 0) >= 0 else "Investiga"} a {lead_change["label"]} primero: '
        f'{"replicar su dinamica" if float(lead_change.get("delta", 0) or 0) >= 0 else "frenar su deterioro"} '
        'tiene el mayor impacto posible sobre el total.'
        if pct_abs >= 40
        else f'Revisa {lead_change["label"]} junto con las demas categorias antes de ajustar el forecast.'
    )

    return make_chart_slide(
        contribution_chart,
        build_story_payload(
            stage='Causalidad',
            question='Quien explica la mayor parte del cambio entre la primera y la segunda mitad del periodo?',
            finding=(
                f'{lead_change["label"]} es la categoria que mas mueve el resultado con un delta de '
                f'{format_compact_number(lead_change["delta"])} y {lead_change["contribution_pct"]}% de contribucion.'
            ),
            complication=complication,
            conclusion='La contribucion al cambio permite asignar responsabilidad analitica a los segmentos que realmente movieron el total.',
            recommendation=recommendation,
            signal_value=f'{float(lead_change["contribution_pct"]):+.1f}%',
            signal_label=f'contribucion de {lead_change["label"]}',
            evidence=[
                f'Categorias comparadas: {len(contributions)}',
                f'Antes: {format_compact_number(lead_change["before"])} | Despues: {format_compact_number(lead_change["after"])}',
            ],
            business_context=table.get('business_context', ''),
            insight_type='segment',
            table=table,
        ),
        table=table,
    )


def build_relationship_story_slide(table: dict) -> dict | None:
    strongest = (table.get('correlation_pairs') or [None])[0]
    if not strongest:
        return None

    chart = table.get('scatter_chart') or table.get('heatmap_chart') or build_correlation_chart(table)
    if not chart:
        return None

    strength_percent = round(strongest['absolute_correlation'] * 100, 1)
    direction = strongest['direction']
    all_pairs = table.get('correlation_pairs') or []
    n_pairs = len(all_pairs)
    lead_dimension_col = (table.get('top_dimensions') or [{}])[0].get('column', 'la dimension principal')

    if strongest['absolute_correlation'] >= 0.75:
        impact_summary = (
            f'La relacion {direction} de {strength_percent}% entre estas variables es suficientemente '
            f'fuerte para usarlas como indicador adelantado dentro del {table.get("business_context", "negocio")}.'
        )
    elif strongest['absolute_correlation'] >= 0.55:
        impact_summary = (
            f'La senal {direction} existe pero es moderada ({strength_percent}%); '
            f'valida si se mantiene al segmentar por {lead_dimension_col}.'
        )
    else:
        impact_summary = (
            f'La correlacion {direction} de {strength_percent}% es debil y puede ser incidental '
            'o depender de un subconjunto de los datos.'
        )
    if n_pairs > 1:
        impact_summary += f' Existen {n_pairs} pares relevantes en total para explorar.'

    return make_chart_slide(
        chart,
        build_story_payload(
            stage='Drivers',
            question='Que variables parecen explicar mejor el comportamiento del dataset?',
            finding=(
                f'{strongest["left_column"]} y {strongest["right_column"]} muestran una relacion '
                f'{direction} de {strength_percent}%.'
            ),
            complication='Una relacion fuerte no siempre implica causalidad y puede romperse si cambia la calidad del dato o el mix de segmentos.',
            conclusion=impact_summary,
            recommendation=(
                f'Monitorea {strongest["left_column"]} y {strongest["right_column"]} como pareja analitica y '
                'crea alertas cuando la relacion se rompa.'
            ),
            signal_value=f'{strength_percent}%',
            signal_label='fuerza de correlacion',
            evidence=[
                f'Par lider: {strongest["left_column"]} x {strongest["right_column"]}',
                f'Direccion: {direction}',
                f'Pares relevantes: {n_pairs}',
            ],
            business_context=table.get('business_context', ''),
            insight_type='correlation',
            table=table,
        ),
        table=table,
    )


def build_quality_story_slide(table: dict) -> dict | None:
    quality_watchlist = table.get('quality_watchlist') or []
    if quality_watchlist:
        worst = quality_watchlist[0]
        worst_impact = ((table.get('null_impact') or [None])[0] or {})
        null_patterns = table.get('null_patterns') or []
        worst_pattern = next((item for item in null_patterns if item.get('column') == worst['column']), None)
        worst_completeness = float(worst.get('completeness_percent', 100) or 100)
        null_impact_pct = float(worst_impact.get('measure_impact_pct', 0) or 0)
        if worst_completeness < 60:
            conclusion = (
                f'Con {worst_completeness:.1f}% de completitud en {worst["column"]} y un impacto '
                f'del {null_impact_pct:.1f}% sobre la medida central, las decisiones basadas en este campo tienen un riesgo alto de sesgo.'
            )
        elif worst_completeness < 85:
            conclusion = (
                f'La calidad es parcial: {worst["column"]} ya impacta el {null_impact_pct:.1f}% '
                'de la medida central y puede distorsionar segmentacion y forecasting.'
            )
        else:
            conclusion = (
                'El dataset esta cerca de estar completo. Los vacios restantes son puntuales '
                'y de bajo impacto sobre la metrica principal.'
            )
        combo_chart = build_combo_story_chart(
            title='Riesgo de calidad por campo',
            subtitle=f'Vacios detectados y completitud visible en {table["name"]}',
            data=[
                {
                    'label': item['column'],
                    'value': item['null_count'],
                    'secondary_value': item['completeness_percent'],
                }
                for item in quality_watchlist[:5]
            ],
            value_label='vacios',
            secondary_label='% completitud',
            secondary_domain=[0, 100],
        )
        return make_chart_slide(
            combo_chart,
            build_story_payload(
                stage='Riesgo',
                question='Que tan confiable es la base para soportar decisiones ejecutivas?',
                finding=(
                    f'El mayor foco esta en {worst["column"]}, con {format_compact_number(worst["null_count"])} vacios '
                    f'y {worst["completeness_percent"]}% de completitud.'
                ),
                complication=(
                    f'Esos nulos ya impactan {null_impact_pct:.1f}% de la medida central'
                    + (
                        f' y se concentran en {worst_impact["most_affected_segment"]}.'
                        if worst_impact.get('most_affected_segment') not in {'', 'Sin segmentacion'}
                        else '.'
                    )
                    if worst_impact
                    else (
                        f'El patron de nulos no es uniforme: {worst_pattern["detail"]}.'
                        if worst_pattern
                        else 'Los vacios pueden sesgar ranking, forecasting o segmentacion.'
                    )
                ),
                conclusion=conclusion,
                recommendation=(
                    f'Prioriza reglas de captura o imputacion para {worst["column"]} antes de automatizar decisiones sobre esa variable.'
                ),
                signal_value=f'{worst["completeness_percent"]}%',
                signal_label=f'completitud de {worst["column"]}',
                evidence=[
                    f'Campos en alerta: {len(quality_watchlist)}',
                    f'Completitud total: {round(table.get("completeness_ratio", 0) * 100, 1)}%',
                    f'Tipo del campo critico: {worst["inferred_type"]}',
                ],
                business_context=table.get('business_context', ''),
                insight_type='outlier',
                table=table,
            ),
            table=table,
        )

    outlier_watchlist = table.get('outlier_watchlist') or []
    if not outlier_watchlist:
        return None

    worst = outlier_watchlist[0]
    return make_chart_slide(
        build_outlier_chart(table),
        build_story_payload(
            stage='Riesgo',
            question='Hay anomalias que puedan distorsionar la lectura ejecutiva?',
            finding=(
                f'{worst["column"]} concentra {worst["outlier_percent"]}% de valores fuera del rango esperado.'
            ),
            complication='Los extremos pueden exagerar la tendencia o esconder el comportamiento del bloque principal.',
            conclusion='La historia principal puede estar amplificada por picos puntuales y conviene separar senal estructural de ruido.',
            recommendation=(
                f'Revisa outliers de {worst["column"]} con criterio de negocio y prepara una vista limpia para comparar escenarios con y sin extremos.'
            ),
            signal_value=f'{worst["outlier_percent"]}%',
            signal_label=f'outliers en {worst["column"]}',
            evidence=[
                f'Rango esperado: {worst["lower_bound"]} a {worst["upper_bound"]}',
                f'Columnas con outliers: {len(outlier_watchlist)}',
            ],
            business_context=table.get('business_context', ''),
            insight_type='outlier',
            table=table,
        ),
        table=table,
    )


def build_discovery_story_slide(table: dict) -> dict | None:
    if table.get('geo_map_chart'):
        chart = table['geo_map_chart']
        top_point = max(chart.get('data', []), key=lambda item: item['value'])
        return make_chart_slide(
            chart,
            build_story_payload(
                stage='Patron Oculto',
                question='Existe una concentracion geografica que cambie la lectura del negocio?',
                finding=(
                    f'{top_point["label"]} aparece como el punto de mayor peso con {format_compact_number(top_point["value"])}.'
                ),
                complication='La geografia dominante puede ocultar que el rendimiento real depende de pocos mercados o plazas.',
                conclusion='La geografia no solo distribuye volumen: tambien puede explicar diferencias en demanda, cobertura o riesgo operativo.',
                recommendation='Prioriza comparativos regionales y adapta la lectura ejecutiva a territorios con mayor concentracion.',
                signal_value=format_compact_number(top_point['value']),
                signal_label=f'valor en {top_point["label"]}',
                evidence=[f'Puntos mapeados: {len(chart.get("data", []))}'],
                business_context=table.get('business_context', ''),
                insight_type='segment',
                table=table,
            ),
            table=table,
        )

    if table.get('sankey_chart'):
        chart = table['sankey_chart']
        strongest_link = max(chart['data']['links'], key=lambda item: item['value'])
        source_node = chart['data']['nodes'][strongest_link['source']]['name']
        target_node = chart['data']['nodes'][strongest_link['target']]['name']
        return make_chart_slide(
            chart,
            build_story_payload(
                stage='Patron Oculto',
                question='Como fluye el valor entre las categorias del dataset?',
                finding=(
                    f'El flujo mas intenso conecta {source_node} con {target_node} y moviliza {format_compact_number(strongest_link["value"])}.'
                ),
                complication='La dependencia de unos pocos pasos o transiciones deja menos margen si cambia el mix operativo.',
                conclusion='Las transiciones dominantes ayudan a entender que combinaciones explican mejor el resultado agregado.',
                recommendation='Usa este flujo para redisenar segmentacion, funnels o vistas de cohortes alrededor de los nodos principales.',
                signal_value=format_compact_number(strongest_link['value']),
                signal_label='flujo principal',
                evidence=[f'Links visibles: {len(chart["data"]["links"])}'],
                business_context=table.get('business_context', ''),
                insight_type='segment',
                table=table,
            ),
            table=table,
        )

    if table.get('radar_chart'):
        chart = table['radar_chart']
        series = chart.get('series', [])
        data = chart.get('data', [])
        segment_scores = {segment: 0 for segment in series}
        segment_top_metric = {}
        for metric_row in data:
            available_segments = [segment for segment in series if segment in metric_row]
            if not available_segments:
                continue
            leader = max(available_segments, key=lambda segment: metric_row.get(segment, 0))
            leader_value = float(metric_row.get(leader, 0) or 0)
            segment_scores[leader] += 1
            current_top = segment_top_metric.get(leader)
            if current_top is None or leader_value > current_top['value']:
                segment_top_metric[leader] = {
                    'metric': metric_row.get('metric', 'la metrica principal'),
                    'value': leader_value,
                }
        top_segment = max(segment_scores, key=segment_scores.get) if segment_scores else 'el segmento lider'
        top_metric = segment_top_metric.get(top_segment, {}).get('metric', 'la metrica principal')
        return make_chart_slide(
            chart,
            build_story_payload(
                stage='Patron Oculto',
                question='Que perfil distingue a los segmentos mas relevantes?',
                finding=(
                    f'{top_segment} lidera en {segment_scores.get(top_segment, 0)} de {len(data)} metricas, '
                    f'destacando especialmente en {top_metric}.'
                ),
                complication='Eso vuelve riesgoso tomar decisiones con una sola metrica agregada.',
                conclusion='El perfil relativo permite identificar que categoria lidera por amplitud y cual destaca por eficiencia puntual.',
                recommendation='Convierte esta comparacion en una matriz de desempeno para definir prioridades por segmento.',
                signal_value=len(chart.get('series', [])),
                signal_label='segmentos comparados',
                evidence=[f'Metricas incluidas: {len(chart.get("data", []))}'],
                business_context=table.get('business_context', ''),
                insight_type='segment',
                table=table,
            ),
            table=table,
        )

    if table.get('treemap_chart'):
        chart = table['treemap_chart']
        largest = max(chart.get('data', []), key=lambda item: item['value'])
        return make_chart_slide(
            chart,
            build_story_payload(
                stage='Patron Oculto',
                question='Que categoria captura la mayor porcion del valor observado?',
                finding=f'{largest["name"]} ocupa la mayor area relativa con {format_compact_number(largest["value"])}.',
                complication='Si la cartera se concentra, el crecimiento total depende de pocas categorias de alto peso.',
                conclusion='La lectura del dataset cambia cuando el peso relativo se observa de forma proporcional y no solo por ranking lineal.',
                recommendation='Prioriza decisiones sobre las categorias con mayor huella y revisa el resto como cartera de expansion.',
                signal_value=format_compact_number(largest['value']),
                signal_label=f'valor de {largest["name"]}',
                evidence=[f'Categorias visibles: {len(chart.get("data", []))}'],
                business_context=table.get('business_context', ''),
                insight_type='segment',
                table=table,
            ),
            table=table,
        )

    if table.get('heatmap_chart'):
        chart = table['heatmap_chart']
        strongest = (table.get('correlation_pairs') or [None])[0]
        if not strongest:
            return None
        return make_chart_slide(
            chart,
            build_story_payload(
                stage='Patron Oculto',
                question='Que relaciones secundarias emergen al ver todas las metricas juntas?',
                finding=(
                    f'El mapa confirma que {strongest["left_column"]} y {strongest["right_column"]} son la pareja mas intensa del conjunto.'
                ),
                complication='El resto de variables aporta bastante menos y puede distraer la lectura si se sobrecarga el dashboard.',
                conclusion='No todas las variables pesan igual; el heatmap separa drivers robustos de correlaciones incidentales.',
                recommendation='Usa esta matriz para simplificar el dashboard y quedarte con las pocas variables que realmente mueven el resultado.',
                signal_value=f'{round(strongest["absolute_correlation"] * 100, 1)}%',
                signal_label='relacion dominante',
                evidence=[f'Cruces visibles: {len(chart.get("data", []))}'],
                business_context=table.get('business_context', ''),
                insight_type='correlation',
                table=table,
            ),
            table=table,
        )

    return None


def build_table_action_slide(table: dict) -> dict:
    top_dimension = (table.get('top_dimensions') or [None])[0]
    top_metric = (table.get('top_numeric_metrics') or [None])[0]
    strongest = (table.get('correlation_pairs') or [None])[0]

    cards = build_field_focus_cards(table)
    cards.append({
        'name': 'Siguiente accion',
        'detail': (
            f'Cruza {top_metric["column"] if top_metric else "la medida central"} con '
            f'{top_dimension["column"] if top_dimension else "la principal dimension"} para priorizar decisiones.'
        ),
        'highlight': 'Playbook',
    })

    if strongest:
        cards.append({
            'name': 'KPI sugerido',
            'detail': f'Sigue {strongest["left_column"]} x {strongest["right_column"]} como alerta temprana.',
            'highlight': 'Monitoreo',
        })

    return {
        'type': 'table_focus',
        'title': 'Campos y acciones a priorizar',
        'subtitle': 'Resumen final para convertir el analisis en decisiones',
        'question': 'Con que variables conviene construir la siguiente capa de decision?',
        'situation': 'Los campos destacados concentran estructura, medida, segmentacion y riesgo dentro del dataset.',
        'complication': 'Si se mezclan demasiadas variables en el dashboard inicial, se diluye la senal accionable.',
        'implication': 'Un set pequeno de campos acelera el paso de exploracion a seguimiento ejecutivo.',
        'action': 'Empieza por estos campos en reporting, alertas y exploracion guiada con AI.',
        'finding': 'Las variables destacadas concentran estructura, medida, segmentacion y riesgo dentro del dataset.',
        'conclusion': 'Estas columnas son suficientes para montar un tablero ejecutivo inicial sin perder foco.',
        'recommendation': 'Empieza por estos campos en reporting, alertas y exploracion guiada con AI.',
        'confidence': table.get('insight_confidence', {}).get('segment'),
        'hero_kpi': table.get('hero_kpi'),
        'layout_hint': build_slide_layout({'hero_kpi': table.get('hero_kpi')}, table),
        'tables': cards[:4],
    }


def build_field_focus_cards(table: dict) -> list[dict]:
    cards = [
        {
            'name': item['column'],
            'detail': item['detail'],
            'highlight': item['role'],
        }
        for item in table.get('field_highlights', [])
    ]

    if cards:
        return cards[:4]

    return [
        {
            'name': table['name'],
            'detail': f'{table["row_count"]:,} filas | {table["column_count"]} columnas',
            'highlight': table.get('primary_key_name') or 'sin campo foco',
        }
    ]


def build_single_table_dashboard(table: dict, dataset_name: str, relationships: list[dict]) -> dict:
    focus_metric = (table.get('top_numeric_metrics') or [None])[0]
    focus_dimension = (table.get('top_dimensions') or [None])[0]
    time_series = table.get('time_series')
    trend_summary = table.get('trend_summary')
    quality_chart = build_quality_chart(table)
    correlation_chart = build_correlation_chart(table)
    outlier_chart = build_outlier_chart(table)

    kpis = [
        {'metric_type': 'rows', 'label': 'Filas', 'value': table['row_count'], 'unit': '#', 'caption': f'registros en {table["name"]}'},
        {
            'metric_type': 'completeness',
            'label': 'Completitud',
            'value': round(table['completeness_ratio'] * 100, 1),
            'unit': '%',
            'caption': 'celdas con informacion',
        },
    ]

    def push_kpi(metric):
        existing = {item['metric_type'] for item in kpis}
        if metric and metric['metric_type'] not in existing:
            kpis.append(metric)

    if focus_metric:
        push_kpi({
            'metric_type': f'{focus_metric["column"]}_sum',
            'label': focus_metric['column'],
            'value': focus_metric['sum'],
            'unit': '#',
            'caption': 'suma de la medida principal',
        })

    if time_series:
        if trend_summary and trend_summary['change_percent'] is not None:
            push_kpi({
                'metric_type': 'trend_change',
                'label': 'Cambio',
                'value': abs(trend_summary['change_percent']),
                'unit': '%',
                'caption': (
                    f'{"sube" if trend_summary["change_value"] >= 0 else "cae"} '
                    f'entre {trend_summary["start_label"]} y {trend_summary["end_label"]}'
                ),
            })
        else:
            push_kpi({
                'metric_type': 'time_points',
                'label': 'Periodos',
                'value': len(time_series.get('points', [])),
                'unit': '#',
                'caption': f'lecturas en {time_series["date_column"]}',
            })

    if focus_dimension and focus_dimension.get('top_values'):
        push_kpi({
            'metric_type': f'{focus_dimension["column"]}_share',
            'label': focus_dimension['column'],
            'value': round(focus_dimension['top_values'][0]['share'] * 100, 1),
            'unit': '%',
            'caption': f'participacion de {focus_dimension["top_values"][0]["label"]}',
        })

    strongest_correlation = (table.get('correlation_pairs') or [None])[0]
    if len(kpis) < 4 and strongest_correlation:
        push_kpi({
            'metric_type': 'correlation_strength',
            'label': 'Correlacion',
            'value': round(strongest_correlation['absolute_correlation'] * 100, 1),
            'unit': '%',
            'caption': f'{strongest_correlation["left_column"]} x {strongest_correlation["right_column"]}',
        })

    if len(kpis) < 4 and table.get('quality_watchlist'):
        push_kpi({
            'metric_type': 'quality_watchlist',
            'label': 'Campos criticos',
            'value': len(table['quality_watchlist']),
            'unit': '#',
            'caption': 'columnas con vacios visibles',
        })

    outlier_risk = (table.get('outlier_watchlist') or [None])[0]
    if len(kpis) < 4 and outlier_risk:
        push_kpi({
            'metric_type': 'outlier_watchlist',
            'label': 'Outliers',
            'value': outlier_risk['outlier_percent'],
            'unit': '%',
            'caption': f'valores atipicos en {outlier_risk["column"]}',
        })

    if len(kpis) < 4:
        push_kpi({
            'metric_type': 'columns',
            'label': 'Columnas',
            'value': table['column_count'],
            'unit': '#',
            'caption': 'campos detectados',
        })

    if time_series:
        primary_chart = {
            'chart_type': 'trend',
            'title': f'{time_series["value_label"]} a lo largo del tiempo',
            'subtitle': f'{table["name"]} usando {time_series["date_column"]}',
            'data': time_series['points'],
            'value_label': time_series['value_label'],
        }
    elif focus_dimension and focus_dimension.get('top_values'):
        primary_chart = {
            'chart_type': 'bar',
            'title': f'Distribucion de {focus_dimension["column"]}',
            'subtitle': f'Categorias dominantes en {table["name"]}',
            'data': [
                {'label': item['label'], 'value': item['count']}
                for item in focus_dimension['top_values']
            ],
            'value_label': 'registros',
        }
    else:
        primary_chart = {
            'chart_type': 'bar',
            'title': f'Medidas detectadas en {table["name"]}',
            'subtitle': 'Comparacion por suma',
            'data': [
                {'label': metric['column'], 'value': metric['sum']}
                for metric in table.get('top_numeric_metrics', [])[:5]
            ],
            'value_label': 'suma',
        }

    if focus_dimension and focus_dimension.get('top_values') and primary_chart.get('title') != f'Distribucion de {focus_dimension["column"]}':
        secondary_chart = {
            'chart_type': 'bar',
            'title': f'Distribucion de {focus_dimension["column"]}',
            'subtitle': 'Categorias con mayor peso',
            'data': [
                {'label': item['label'], 'value': item['count']}
                for item in focus_dimension['top_values']
            ],
            'value_label': 'registros',
        }
    elif correlation_chart:
        secondary_chart = correlation_chart
    elif outlier_chart:
        secondary_chart = outlier_chart
    elif quality_chart:
        secondary_chart = quality_chart
    else:
        secondary_chart = {
            'chart_type': 'bar',
            'title': 'Metricas numericas destacadas',
            'subtitle': f'Comparacion de medidas en {table["name"]}',
            'data': [
                {'label': metric['column'], 'value': metric['mean']}
                for metric in table.get('top_numeric_metrics', [])[:5]
            ],
            'value_label': 'promedio',
        }

    return {
        'headline': f'{dataset_name} ya revela patrones concretos en {table["name"]}',
        'subheadline': (
            f'Analisis especifico sobre {table["row_count"]:,} registros '
            f'dentro de un {table.get("business_context", "dataset de negocio")}.'
        ),
        'kpis': kpis[:4],
        'primary_chart': primary_chart,
        'secondary_chart': secondary_chart,
        'type_distribution': build_column_mix_chart(table),
        'insights': story_engine.build_single_table_insights(table, relationships),
        'table_spotlights': [compact_table_record(table)],
    }


def build_single_table_presentation_slides(dataset_name: str, table: dict, insights: list[str]) -> list[dict]:
    hero_kpi = table.get('hero_kpi') or build_hero_kpi(table, table.get('business_context', 'dataset de negocio'))
    slides = [
        {
            'type': 'hero',
            'eyebrow': 'Executive Story',
            'title': dataset_name,
            'subtitle': (
                f'Lectura ejecutiva de {table["name"]} sobre {table["row_count"]:,} registros '
                f'y {table["column_count"]} columnas detectadas en un {table.get("business_context", "dataset de negocio")}.'
            ),
            'accent_value': hero_kpi['value'],
            'accent_label': hero_kpi['label'],
            'bullets': insights,
            'question': 'Donde esta la senal principal del dataset y que decision habilita?',
            'finding': insights[0] if insights else f'{table["name"]} ya tiene suficiente estructura para una lectura ejecutiva.',
            'conclusion': (
                'La historia combina volumen, segmentacion, relaciones numericas y calidad para separar senal util de ruido.'
            ),
            'recommendation': (
                'Usa las siguientes vistas como ruta de decision: tendencia, concentracion, drivers y riesgos.'
            ),
            'situation': insights[0] if insights else '',
            'complication': insights[1] if len(insights) > 1 else '',
            'implication': insights[2] if len(insights) > 2 else '',
            'action': insights[3] if len(insights) > 3 else 'Sigue la secuencia de vistas para pasar de contexto a accion.',
            'confidence': table.get('insight_confidence', {}).get('trend'),
            'hero_kpi': hero_kpi,
            'layout_hint': build_slide_layout({'hero_kpi': hero_kpi, 'question': 'hero'}, table),
        }
    ]

    for candidate in [
        build_time_story_slide(table),
        build_dimension_story_slide(table),
        build_benchmark_story_slide(table),
        build_change_contribution_story_slide(table),
        build_relationship_story_slide(table),
        build_discovery_story_slide(table),
        build_quality_story_slide(table),
    ]:
        if candidate:
            slides.append(candidate)

    if len(slides) < 5:
        slides.append(make_chart_slide(
            build_column_mix_chart(table),
            build_story_payload(
                stage='Contexto',
                question='Que tan compleja es la estructura del dataset?',
                finding=(
                    f'La tabla combina {table["numeric_columns_count"]} columnas numericas, '
                    f'{table["categorical_columns_count"]} categoricas y {table["datetime_columns_count"]} temporales.'
                ),
                conclusion='La estructura disponible soporta una narrativa ejecutiva sin depender de demasiadas variables.',
                recommendation='Usa esta huella para limitar el tablero inicial a unas pocas columnas de alto impacto.',
                signal_value=table['column_count'],
                signal_label='columnas totales',
                business_context=table.get('business_context', ''),
                insight_type='segment',
                table=table,
            ),
            table=table,
        ))

    slides.append(build_table_action_slide(table))

    return slides


def build_slide_index_entries(core_slides: list[dict]) -> list[dict]:
    entries = [
        {
            'number': 2,
            'title': 'Proceso seguido para el analisis',
            'detail': 'Metodologia aplicada sobre el dataset cargado.',
        }
    ]

    for index, slide in enumerate(core_slides, start=3):
        title = slide.get('title') or 'Vista analitica'
        if slide.get('type') == 'hero':
            title = 'Resumen ejecutivo'

        entries.append({
            'number': index,
            'title': title,
            'detail': slide.get('subtitle') or 'Lectura priorizada para la presentacion.',
        })

    return entries


def build_workflow_steps(overview: dict, tables: list[dict], core_slides: list[dict]) -> list[dict]:
    primary_table = tables[0] if tables else None
    quality_issues = sum(len(table.get('quality_watchlist', [])) for table in tables)
    tables_count = overview.get('tables_count', len(tables))
    total_rows = overview.get('total_rows', sum(table.get('row_count', 0) for table in tables))
    total_columns = overview.get('total_columns', sum(table.get('column_count', 0) for table in tables))
    completeness_ratio = overview.get('completeness_ratio', 0)

    explored_lenses = []
    if overview.get('best_trend'):
        explored_lenses.append('series temporales')
    if 'seasonality' in overview.get('available_lenses', []):
        explored_lenses.append('estacionalidad')
    if overview.get('relationships_count'):
        explored_lenses.append('relaciones')
    if 'correlation' in overview.get('available_lenses', []):
        explored_lenses.append('correlaciones')
    if 'outliers' in overview.get('available_lenses', []):
        explored_lenses.append('outliers')
    if 'text' in overview.get('available_lenses', []):
        explored_lenses.append('texto')
    if any(table.get('top_dimensions') for table in tables):
        explored_lenses.append('segmentacion')
    if 'clusters' in overview.get('available_lenses', []):
        explored_lenses.append('clusters')

    lens_summary = ', '.join(explored_lenses[:4]) if explored_lenses else 'metricas estructurales'
    primary_focus = (
        f'{primary_table["name"]} como tabla foco'
        if primary_table
        else 'sin una tabla foco dominante'
    )

    return [
        {
            'title': 'Carga y normalizacion',
            'detail': (
                f'Se consolidaron {tables_count} tabla(s) con '
                f'{total_rows:,} filas para construir una base analizable.'
            ),
            'signal': f'{tables_count} tablas',
        },
        {
            'title': 'Tipado e inferencia',
            'detail': (
                f'Se clasificaron {total_columns} columnas y se priorizo '
                f'{primary_focus}.'
            ),
            'signal': f'{total_columns} columnas',
        },
        {
            'title': 'Calidad y consistencia',
            'detail': (
                f'Se reviso completitud media de {round(completeness_ratio * 100, 1)}% '
                f'y {quality_issues} alertas de calidad visibles.'
            ),
            'signal': f'{quality_issues} alertas',
        },
        {
            'title': 'Patrones y metricas',
            'detail': f'Se exploraron {lens_summary} para aislar senales con impacto analitico.',
            'signal': 'EDA dirigido',
        },
        {
            'title': 'Sintesis ejecutiva',
            'detail': (
                f'Se ordenaron {len(core_slides)} vistas clave para traducir el analisis '
                'a decisiones mas accionables.'
            ),
            'signal': f'{len(core_slides)} vistas',
        },
    ]


def prepend_storytelling_slides(dataset_name: str, overview: dict, tables: list[dict], core_slides: list[dict]) -> list[dict]:
    index_entries = build_slide_index_entries(core_slides)
    workflow_steps = build_workflow_steps(overview, tables, core_slides)

    return [
        {
            'type': 'index',
            'eyebrow': 'Presentation Roadmap',
            'title': 'Indice del analisis',
            'subtitle': f'Ruta de lectura generada para {dataset_name}.',
            'entries': index_entries,
        },
        {
            'type': 'workflow',
            'eyebrow': 'Analysis Workflow',
            'title': 'Proceso seguido para construir este analisis',
            'subtitle': 'Secuencia aplicada desde la carga del dataset hasta la sintesis ejecutiva.',
            'steps': workflow_steps,
        },
        *core_slides,
    ]


def build_presentation_slides(
    dataset_name: str,
    overview: dict,
    tables: list[dict],
    insights: list[str],
    relationships: list[dict] | None = None,
) -> list[dict]:
    if len(tables) == 1:
        core_slides = build_single_table_presentation_slides(dataset_name, tables[0], insights)
        return prepend_storytelling_slides(dataset_name, overview, tables, core_slides)

    largest_table = max(tables, key=lambda item: item['row_count']) if tables else None
    weakest_quality = min(tables, key=lambda item: item.get('completeness_ratio', 1)) if tables else None
    focus_table = tables[0] if tables else None
    business_context = overview.get('business_context', 'dataset de negocio')
    hero_kpi = (
        build_hero_kpi(largest_table, business_context)
        if largest_table
        else {'value': overview.get('total_rows', 0), 'label': 'filas analizadas'}
    )

    core_slides = [
        {
            'type': 'hero',
            'eyebrow': 'Executive Story',
            'title': dataset_name,
            'subtitle': (
                f'{overview["tables_count"]} tablas, {overview["total_rows"]:,} filas y '
                f'{overview["relationships_count"]} relaciones inferidas en un {business_context}.'
            ),
            'accent_value': hero_kpi['value'],
            'accent_label': hero_kpi['label'],
            'bullets': insights,
            'question': 'Que estructura del dataset concentra la mayor oportunidad analitica?',
            'finding': insights[0] if insights else f'{dataset_name} ya tiene una base suficiente para una lectura ejecutiva.',
            'conclusion': (
                'La historia combina topologia de tablas, volumen, calidad y senales analiticas para priorizar decisiones.'
            ),
            'recommendation': 'Sigue la secuencia: estructura, volumen vs calidad, tendencia, foco analitico y riesgo.',
            'situation': insights[0] if insights else '',
            'complication': insights[1] if len(insights) > 1 else '',
            'implication': insights[2] if len(insights) > 2 else '',
            'action': insights[3] if len(insights) > 3 else '',
            'hero_kpi': hero_kpi,
            'layout_hint': build_slide_layout({'hero_kpi': hero_kpi, 'question': 'hero'}, largest_table or {}),
        },
    ]

    relationship_sankey = build_relationship_sankey_chart(tables, relationships or [])
    if relationship_sankey:
        strongest_relation = max(relationships or [], key=lambda item: item['confidence']) if relationships else None
        core_slides.append(make_chart_slide(
            relationship_sankey,
            build_story_payload(
                stage='Contexto',
                question='Como viaja la informacion entre las tablas del dataset?',
                finding=(
                    f'La topologia conecta {len(relationships or [])} relaciones inferidas'
                    + (
                        f'; la mas solida une {strongest_relation["source_table_name"]}.{strongest_relation["source_column_name"]} '
                        f'con {strongest_relation["target_table_name"]}.{strongest_relation["target_column_name"]}.'
                        if strongest_relation
                        else '.'
                    )
                ),
                conclusion='La calidad de la lectura ejecutiva dependera tanto de cada tabla como de la forma en que se conectan.',
                recommendation='Usa esta red para definir tabla foco, llaves confiables y orden de exploracion.',
                signal_value=len(relationships or []),
                signal_label='relaciones activas',
                evidence=[
                    f'Tabla lider: {largest_table["name"]}' if largest_table else 'Sin tabla lider',
                    f'Tablas visibles: {overview["tables_count"]}',
                ],
                business_context=business_context,
                insight_type='segment',
                table=largest_table,
            ),
            table=largest_table,
        ))

    core_slides.append(make_chart_slide(
        build_combo_story_chart(
            title='Volumen y calidad por tabla',
            subtitle='Cruce entre densidad de registros y completitud estimada',
            data=[
                {
                    'label': table['name'],
                    'value': table['row_count'],
                    'secondary_value': round(table['completeness_ratio'] * 100, 1),
                }
                for table in tables[:8]
            ],
            value_label='filas',
            secondary_label='% completitud',
            secondary_domain=[0, 100],
        ),
        build_story_payload(
            stage='Exploracion',
            question='Donde vive el volumen y que tan confiable es esa lectura?',
            finding=(
                f'{largest_table["name"]} concentra {largest_table["row_count"]:,} filas'
                if largest_table
                else 'El dataset reparte su volumen en multiples tablas.'
            )
            + (
                f', mientras {weakest_quality["name"]} cae a {round(weakest_quality["completeness_ratio"] * 100, 1)}% de completitud.'
                if weakest_quality
                else ''
            ),
            conclusion='No toda la data pesa igual: la mejor tabla para profundizar es la que combina masa critica y calidad suficiente.',
            recommendation='Prioriza las tablas con alto volumen y buena completitud como capa base del deck y trata las demas como soporte.',
            signal_value=largest_table['row_count'] if largest_table else overview['total_rows'],
            signal_label='filas en la tabla foco',
            evidence=[
                f'Completitud global: {round(overview.get("completeness_ratio", 0) * 100, 1)}%',
                f'Tablas comparadas: {min(len(tables), 8)}',
            ],
            business_context=business_context,
            insight_type='segment',
            table=largest_table,
        ),
        table=largest_table,
    ))

    if len(tables) > 1 and overview.get('best_trend'):
        best_trend = overview['best_trend']
        combo_points = []
        for index, point in enumerate(best_trend['points']):
            window = best_trend['points'][max(0, index - 2):index + 1]
            rolling_average = sum(float(item['value']) for item in window) / len(window)
            combo_points.append({
                'label': point['label'],
                'value': point['value'],
                'secondary_value': round(rolling_average, 4),
            })
        peak_point = max(best_trend['points'], key=lambda item: item['value'])
        core_slides.append(make_chart_slide(
            build_combo_story_chart(
                title='La historia temporal mas util',
                subtitle=(
                    f'{best_trend["table_name"]}.{best_trend["date_column"]} '
                    f'vs {best_trend["value_label"]}'
                ),
                data=combo_points,
                value_label=best_trend['value_label'],
                secondary_label='Media movil',
            ),
            build_story_payload(
                stage='Descubrimiento',
                question=f'Que nos dice la mejor serie temporal del dataset sobre {best_trend["value_label"]}?',
                finding=(
                    f'El pico ocurre en {peak_point["label"]} con {format_compact_number(peak_point["value"])} '
                    f'en la tabla {best_trend["table_name"]}.'
                ),
                complication='La serie lider ayuda a priorizar, pero no necesariamente representa a todas las tablas del bundle.',
                conclusion='La mejor historia temporal ayuda a priorizar cuando profundizar en demanda, operaciones o revenue.',
                recommendation='Convierte esta serie en lectura recurrente del dashboard y usa la media movil para aislar cambios estructurales.',
                signal_value=format_compact_number(peak_point['value']),
                signal_label='pico temporal',
                evidence=[
                    f'Periodos visibles: {len(best_trend["points"])}',
                    f'Tabla fuente: {best_trend["table_name"]}',
                ],
                business_context=business_context,
                insight_type='trend',
                table=focus_table,
            ),
            table=focus_table,
        ))

    if focus_table:
        appended = 0
        for candidate in [
            build_dimension_story_slide(focus_table),
            build_benchmark_story_slide(focus_table),
            build_change_contribution_story_slide(focus_table),
            build_relationship_story_slide(focus_table),
            build_discovery_story_slide(focus_table),
            build_quality_story_slide(focus_table),
        ]:
            if candidate:
                core_slides.append(candidate)
                appended += 1
                if appended >= 3:
                    break

    risk_cards = [
        {
            'name': table['name'],
            'detail': (
                f'{table["row_count"]:,} filas | {round(table.get("completeness_ratio", 0) * 100, 1)}% completitud'
            ),
            'highlight': (
                table['top_numeric_metrics'][0]['column']
                if table.get('top_numeric_metrics')
                else table.get('primary_key_name') or 'sin medida dominante'
            ),
        }
        for table in tables[:4]
    ]
    core_slides.append({
        'type': 'table_focus',
        'title': 'Tablas a mirar primero',
        'subtitle': 'Prioriza estas piezas para analisis de negocio',
        'question': 'Que tablas merecen atencion inmediata despues de esta lectura?',
        'situation': 'Las primeras tablas concentran volumen, calidad util o variables clave para profundizar.',
        'complication': 'Si se empieza por tablas secundarias, el analisis se vuelve mas lento y menos accionable.',
        'implication': 'El orden de exploracion define que tan rapido se convierte el EDA en decisiones.',
        'action': 'Empieza por estas tablas para dashboards, QA de datos y preguntas dirigidas a AI.',
        'finding': 'Las primeras tablas concentran volumen, calidad util o variables clave para profundizar.',
        'conclusion': 'Una buena secuencia de exploracion acelera el paso de EDA a decision ejecutiva.',
        'recommendation': 'Empieza por estas tablas para dashboards, QA de datos y preguntas dirigidas a AI.',
        'confidence': focus_table.get('insight_confidence', {}).get('segment') if focus_table else None,
        'hero_kpi': hero_kpi,
        'layout_hint': build_slide_layout({'hero_kpi': hero_kpi, 'question': 'tables'}, focus_table or {}),
        'tables': risk_cards,
    })

    return prepend_storytelling_slides(dataset_name, overview, tables, core_slides)


def build_dataset_analysis(
    dataset_name: str,
    prepared_tables: list[dict],
    relationships: list[dict],
    progress_guard=None,
) -> dict:
    all_column_names = [
        column['name']
        for profile in prepared_tables
        for column in profile['columns']
    ]
    total_profile_columns = sum(len(profile.get('columns', [])) for profile in prepared_tables)
    numeric_profile_columns = sum(
        1
        for profile in prepared_tables
        for column in profile.get('columns', [])
        if column.get('inferred_type') in {'integer', 'decimal'}
    )
    business_context = insight_engine.build_business_context(
        None,
        all_column_names,
        numeric_ratio=safe_ratio(numeric_profile_columns, total_profile_columns or 1),
    )

    tables = []
    for profile in prepared_tables:
        if progress_guard:
            progress_guard()
        tables.append(build_table_analysis(profile, business_context, progress_guard=progress_guard))
    tables.sort(key=lambda item: item['row_count'], reverse=True)
    if progress_guard:
        progress_guard()

    total_rows = sum(table['row_count'] for table in tables)
    total_columns = sum(table['column_count'] for table in tables)
    weighted_non_null = sum(table['completeness_ratio'] * table['row_count'] * table['column_count'] for table in tables)
    weighted_total = sum(table['row_count'] * table['column_count'] for table in tables)
    overview = {
        'dataset_name': dataset_name,
        'business_context': business_context,
        'tables_count': len(tables),
        'relationships_count': len(relationships),
        'total_rows': total_rows,
        'total_columns': total_columns,
        'numeric_columns': sum(table['numeric_columns_count'] for table in tables),
        'categorical_columns': sum(table['categorical_columns_count'] for table in tables),
        'datetime_columns': sum(table['datetime_columns_count'] for table in tables),
        'completeness_ratio': safe_ratio(weighted_non_null, weighted_total),
        'generated_at': datetime.utcnow().isoformat(),
        'available_lenses': sorted({mode for table in tables for mode in table.get('analysis_modes', [])}),
    }

    trend_candidates = [table['time_series'] | {'table_name': table['name']} for table in tables if table.get('time_series')]
    if trend_candidates:
        trend_candidates.sort(key=lambda item: len(item['points']), reverse=True)
        overview['best_trend'] = trend_candidates[0]

    relationship_cards = [
        {
            'source_table_name': relationship['source_table_name'],
            'source_column_name': relationship['source_column_name'],
            'target_table_name': relationship['target_table_name'],
            'target_column_name': relationship['target_column_name'],
            'confidence': relationship['confidence'],
        }
        for relationship in relationships
    ]

    insights = story_engine.build_headline_insights(overview, tables, relationship_cards, business_context)
    overview['headline_insights'] = insights

    if len(tables) == 1:
        dashboard = build_single_table_dashboard(tables[0], dataset_name, relationship_cards)
        overview['focus_table'] = tables[0]['name']
    else:
        dashboard = {
            'headline': f'{dataset_name} ya tiene un dashboard vivo',
            'subheadline': f'{len(tables)} tablas conectan {total_rows:,} filas dentro de un {business_context}.',
            'kpis': [
                {'metric_type': 'tables', 'label': 'Tablas', 'value': len(tables), 'unit': '#', 'caption': 'detectadas en el upload'},
                {'metric_type': 'rows', 'label': 'Filas', 'value': total_rows, 'unit': '#', 'caption': 'registros totales'},
                {'metric_type': 'columns', 'label': 'Columnas', 'value': total_columns, 'unit': '#', 'caption': 'campos disponibles'},
                {
                    'metric_type': 'completeness',
                    'label': 'Completitud',
                    'value': round(overview['completeness_ratio'] * 100, 1),
                    'unit': '%',
                    'caption': 'celdas con informacion',
                },
            ],
            'primary_chart': {
                'chart_type': 'bar',
                'title': 'Volumen por tabla',
                'subtitle': 'Las tablas con mayor densidad de registros',
                'data': [{'label': table['name'], 'value': table['row_count']} for table in tables[:8]],
                'value_label': 'filas',
            },
            'secondary_chart': {
                'chart_type': 'bar',
                'title': 'Completitud por tabla',
                'subtitle': 'Que tan poblada esta cada tabla',
                'data': [
                    {'label': table['name'], 'value': round(table['completeness_ratio'] * 100, 1)}
                    for table in tables[:8]
                ],
                'value_label': '%',
            },
            'type_distribution': {
                'title': 'Mix de columnas',
                'data': [
                    {'label': 'Numericas', 'value': overview['numeric_columns']},
                    {'label': 'Categoricas', 'value': overview['categorical_columns']},
                    {'label': 'Fecha', 'value': overview['datetime_columns']},
                ],
            },
            'insights': insights,
            'table_spotlights': [compact_table_record(table) for table in tables[:4]],
        }

    return {
        'overview': overview,
        'tables': [compact_table_record(table) for table in tables],
        'relationships': relationship_cards,
        'dashboard': dashboard,
        'presentation': {
            'title': f'Lectura ejecutiva de {dataset_name}',
            'slides': story_engine.build_presentation_slides(
                dataset_name,
                overview,
                tables,
                insights,
                relationship_cards,
            ),
        },
    }


def build_schema_only_summary(schema_profile: dict) -> dict:
    tables = sorted(schema_profile.get('tables', []), key=lambda item: item['row_count'], reverse=True)
    relationships_data = schema_profile.get('relationships', [])
    schema_column_names = schema_profile.get('column_names', [])
    business_context = insight_engine.build_business_context(
        None,
        schema_column_names,
        numeric_ratio=safe_ratio(
            sum(table.get('numeric_columns_count', 0) for table in tables),
            sum(table.get('column_count', 0) for table in tables) or 1,
        ),
    )

    total_rows = sum(table['row_count'] for table in tables)
    total_columns = sum(table['column_count'] for table in tables)
    weighted_non_null = sum(
        table['completeness_ratio'] * table['row_count'] * table['column_count']
        for table in tables
    )
    weighted_total = sum(table['row_count'] * table['column_count'] for table in tables)
    insights = story_engine.build_headline_insights(
        {
            'tables_count': schema_profile['tables_count'],
            'relationships_count': schema_profile['relationships_count'],
            'business_context': business_context,
        },
        tables,
        relationships_data,
        business_context,
    )

    return {
        'overview': {
            'dataset_name': schema_profile['name'],
            'business_context': business_context,
            'tables_count': schema_profile['tables_count'],
            'relationships_count': schema_profile['relationships_count'],
            'total_rows': total_rows,
            'total_columns': total_columns,
            'numeric_columns': sum(table['numeric_columns_count'] for table in tables),
            'categorical_columns': sum(table['categorical_columns_count'] for table in tables),
            'datetime_columns': sum(table['datetime_columns_count'] for table in tables),
            'completeness_ratio': safe_ratio(weighted_non_null, weighted_total),
            'generated_at': datetime.utcnow().isoformat(),
            'available_lenses': ['quality', 'numeric', 'categorical', 'time_series'],
            'headline_insights': insights,
        },
        'tables': [compact_table_record(table) for table in tables],
        'relationships': relationships_data,
        'dashboard': {
            'headline': f'{schema_profile["name"]} esta listo para explorarse',
            'subheadline': f'Este resumen proviene del schema guardado para un {business_context}. Para mas narrativa, vuelve a importar el dataset.',
            'kpis': [
                {'metric_type': 'tables', 'label': 'Tablas', 'value': schema_profile['tables_count'], 'unit': '#', 'caption': 'detectadas en el schema'},
                {'metric_type': 'rows', 'label': 'Filas', 'value': total_rows, 'unit': '#', 'caption': 'registros declarados'},
                {'metric_type': 'columns', 'label': 'Columnas', 'value': total_columns, 'unit': '#', 'caption': 'campos modelados'},
                {'metric_type': 'relations', 'label': 'Relaciones', 'value': schema_profile['relationships_count'], 'unit': '#', 'caption': 'vinculos detectados'},
            ],
            'primary_chart': {
                'title': 'Volumen por tabla',
                'subtitle': 'A partir del schema guardado',
                'data': [{'label': table['name'], 'value': table['row_count']} for table in tables[:8]],
                'value_label': 'filas',
            },
            'secondary_chart': {
                'title': 'Columnas por tabla',
                'subtitle': 'Complejidad estructural',
                'data': [{'label': table['name'], 'value': table['column_count']} for table in tables[:8]],
                'value_label': 'columnas',
            },
            'type_distribution': {
                'title': 'Mix de columnas',
                'data': [
                    {'label': 'Numericas', 'value': sum(table['numeric_columns_count'] for table in tables)},
                    {'label': 'Categoricas', 'value': sum(table['categorical_columns_count'] for table in tables)},
                    {'label': 'Fecha', 'value': sum(table['datetime_columns_count'] for table in tables)},
                ],
            },
            'insights': insights,
            'table_spotlights': [compact_table_record(table) for table in tables[:4]],
        },
        'presentation': {
            'title': f'Lectura estructural de {schema_profile["name"]}',
            'slides': story_engine.build_presentation_slides(
                schema_profile['name'],
                {
                    'tables_count': schema_profile['tables_count'],
                    'relationships_count': schema_profile['relationships_count'],
                    'total_rows': total_rows,
                    'completeness_ratio': safe_ratio(weighted_non_null, weighted_total),
                    'business_context': business_context,
                },
                tables,
                insights,
                relationships_data,
            ),
        },
    }


def get_latest_ready_dataset_import(user):
    return (
        DatasetImport.objects.filter(user=user, status='ready')
        .prefetch_related(
            'tables__columns',
            'relationships__source_table',
            'relationships__source_column',
            'relationships__target_table',
            'relationships__target_column',
        )
        .first()
    )


def get_dataset_analysis_summary(dataset_import: DatasetImport) -> dict:
    summary = dataset_import.analysis_summary or {}
    if summary:
        overview = summary.get('overview', {})
        tables = summary.get('tables', [])
        relationships = summary.get('relationships', [])
        insights = (
            overview.get('headline_insights')
            or summary.get('dashboard', {}).get('insights')
            or story_engine.build_headline_insights(
                overview,
                tables,
                relationships,
                overview.get('business_context', ''),
            )
        )
        summary['overview'] = {
            **overview,
            'headline_insights': insights,
            'dataset_name': overview.get('dataset_name') or dataset_import.name,
        }
        summary['presentation'] = {
            'title': f'Lectura ejecutiva de {dataset_import.name}',
            'slides': story_engine.build_presentation_slides(
                dataset_import.name,
                summary['overview'],
                tables,
                insights,
                relationships,
            ),
        }
        return summary
    return build_schema_only_summary(extract_schema_profile(dataset_import))
