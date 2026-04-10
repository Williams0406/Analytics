import json
import logging
import threading

from decouple import config
import numpy as np
import pandas as pd

from apps.insights.ai_service import get_ai_response

from .datetime_utils import parse_datetime_series
from .utils import (
    chi_square_is_significant,
    format_compact_number,
    format_percent,
    safe_ratio,
    score_column_keywords,
)

DOMAIN_KEYWORDS = {
    'finanzas': [
        'revenue', 'sales', 'sale', 'price', 'profit', 'margin', 'cost', 'expense',
        'amount', 'invoice', 'payment', 'mrr', 'arr', 'billing', 'discount',
    ],
    'rrhh': [
        'employee', 'department', 'salary', 'payroll', 'hire', 'staff', 'manager',
        'headcount', 'tenure', 'benefit', 'position',
    ],
    'logistica': [
        'sku', 'stock', 'inventory', 'warehouse', 'shipment', 'delivery', 'supplier',
        'fulfillment', 'route', 'carrier', 'dispatch',
    ],
    'marketing': [
        'campaign', 'click', 'impression', 'lead', 'conversion', 'traffic', 'channel',
        'ad', 'roas', 'ctr', 'cpc', 'cac',
    ],
    'ecommerce': [
        'order', 'cart', 'checkout', 'basket', 'refund', 'customer', 'product',
        'sku', 'store', 'merchant',
    ],
    'educacion': [
        'student', 'course', 'grade', 'exam', 'attendance', 'teacher', 'class',
        'school', 'subject',
    ],
    'salud': [
        'patient', 'diagnosis', 'treatment', 'hospital', 'medication', 'claim',
        'provider', 'visit', 'therapy',
    ],
    'operaciones': [
        'ticket', 'sla', 'incident', 'queue', 'task', 'throughput', 'resolution',
        'downtime', 'failure', 'support',
    ],
    'saas': [
        'feature', 'subscription', 'plan', 'trial', 'churn', 'activation', 'onboarding',
        'seat', 'tenant', 'workspace', 'usage', 'event', 'session',
    ],
    'inmobiliario': [
        'property', 'listing', 'sqft', 'bedroom', 'bathroom', 'rent', 'lease',
        'mortgage', 'appraisal', 'zoning', 'lot', 'unit',
    ],
}

IMPACT_FORMULAS = {
    'finanzas': {
        'metric_keyword': ['revenue', 'sales', 'profit', 'margin', 'arr', 'mrr', 'ingreso', 'venta'],
        'formula_type': 'delta_times_total',
        'unit_label': 'USD',
        'risk_label': 'riesgo de ingreso',
        'opportunity_label': 'oportunidad de ingreso',
    },
    'operaciones': {
        'metric_keyword': ['utilization', 'utilizacion', 'throughput', 'uptime', 'downtime', 'idle', 'output'],
        'formula_type': 'delta_times_total',
        'unit_label': 'USD',
        'risk_label': 'riesgo de ingreso mensual',
        'opportunity_label': 'ganancia operativa estimada',
    },
    'saas': {
        'metric_keyword': ['churn', 'retention', 'subscription', 'arr', 'mrr', 'activation', 'seat'],
        'formula_type': 'churn_revenue',
        'unit_label': 'USD',
        'risk_label': 'riesgo de ARR',
        'opportunity_label': 'expansion potencial de ARR',
    },
    'logistica': {
        'metric_keyword': ['delivery', 'shipment', 'fulfillment', 'delay', 'inventory', 'stock', 'route'],
        'formula_type': 'delta_times_rate_times_volume',
        'unit_label': 'USD',
        'risk_label': 'costo logistico estimado',
        'opportunity_label': 'ahorro logistico estimado',
    },
    'marketing': {
        'metric_keyword': ['lead', 'conversion', 'roas', 'ctr', 'cpc', 'cac', 'campaign'],
        'formula_type': 'delta_times_total',
        'unit_label': 'USD',
        'risk_label': 'riesgo de pipeline',
        'opportunity_label': 'uplift potencial de pipeline',
    },
    'ecommerce': {
        'metric_keyword': ['order', 'checkout', 'basket', 'refund', 'customer', 'cart'],
        'formula_type': 'delta_times_total',
        'unit_label': 'USD',
        'risk_label': 'riesgo de venta mensual',
        'opportunity_label': 'uplift de ventas',
    },
    'rrhh': {
        'metric_keyword': ['salary', 'payroll', 'headcount', 'tenure', 'employee'],
        'formula_type': 'delta_times_total',
        'unit_label': 'unidades',
        'risk_label': 'impacto operativo estimado',
        'opportunity_label': 'mejora operativa estimada',
    },
    'educacion': {
        'metric_keyword': ['attendance', 'grade', 'student', 'course'],
        'formula_type': 'delta_times_total',
        'unit_label': 'unidades',
        'risk_label': 'riesgo academico estimado',
        'opportunity_label': 'mejora academica estimada',
    },
    'salud': {
        'metric_keyword': ['patient', 'claim', 'visit', 'therapy', 'provider'],
        'formula_type': 'delta_times_total',
        'unit_label': 'unidades',
        'risk_label': 'riesgo asistencial estimado',
        'opportunity_label': 'mejora asistencial estimada',
    },
    'inmobiliario': {
        'metric_keyword': ['rent', 'lease', 'property', 'listing', 'mortgage'],
        'formula_type': 'delta_times_total',
        'unit_label': 'USD',
        'risk_label': 'riesgo de ingreso inmobiliario',
        'opportunity_label': 'uplift inmobiliario',
    },
    'default': {
        'metric_keyword': [],
        'formula_type': 'delta_times_total',
        'unit_label': 'USD',
        'risk_label': 'impacto estimado',
        'opportunity_label': 'oportunidad estimada',
    },
}


def _resolve_impact_formula(metric_column: str, business_context: str) -> tuple[str, dict]:
    metric_text = f'{metric_column} {business_context}'.lower()
    ordered_domains = [
        domain
        for domain in IMPACT_FORMULAS
        if domain != 'default'
    ]
    ordered_domains.sort(
        key=lambda domain: (
            domain in business_context.lower(),
            any(keyword in metric_text for keyword in IMPACT_FORMULAS[domain].get('metric_keyword', [])),
        ),
        reverse=True,
    )

    for domain in ordered_domains:
        formula = IMPACT_FORMULAS[domain]
        keywords = formula.get('metric_keyword', [])
        if domain in business_context.lower() or any(keyword in metric_text for keyword in keywords):
            return domain, formula

    return 'default', IMPACT_FORMULAS['default']


def build_business_impact(
    delta_pct,
    metric_column: str,
    business_context: str,
    reference_value,
) -> dict | None:
    if delta_pct is None or reference_value in (None, ''):
        return None

    try:
        delta_ratio = abs(float(delta_pct)) / 100.0
        reference = abs(float(reference_value))
    except (TypeError, ValueError):
        return None

    if reference <= 0:
        return None

    domain, formula = _resolve_impact_formula(metric_column, business_context)
    formula_type = formula.get('formula_type', 'delta_times_total')
    if formula_type in {'delta_times_total', 'delta_times_rate_times_volume', 'churn_revenue'}:
        impact_value = delta_ratio * reference
    else:
        impact_value = delta_ratio * reference

    higher_is_better = infer_higher_is_better(metric_column, business_context)
    is_risk = (float(delta_pct) < 0 and higher_is_better) or (float(delta_pct) > 0 and not higher_is_better)
    confidence = 0.5
    if domain != 'default':
        confidence += 0.2
    if any(keyword in metric_column.lower() for keyword in formula.get('metric_keyword', [])):
        confidence += 0.2
    confidence = round(min(0.95, confidence), 2)

    return {
        'impact_value': round(float(impact_value), 2),
        'impact_unit': formula.get('unit_label', 'USD'),
        'impact_label': formula.get('risk_label') if is_risk else formula.get('opportunity_label'),
        'formula_used': f'{domain}:{formula_type}',
        'confidence': confidence,
        'reference_value': round(float(reference), 2),
        'delta_pct': round(float(delta_pct), 2),
    }


def _normalize_impact_score(business_impact: dict | None) -> float:
    if not business_impact:
        return 0.0

    impact_value = abs(float(business_impact.get('impact_value', 0) or 0))
    reference_value = abs(float(business_impact.get('reference_value', 0) or 0))
    denominator = max(reference_value, impact_value, 1.0)
    return max(0.0, min(1.0, impact_value / denominator))


def _derive_urgency_score(table: dict) -> float:
    time_series = table.get('time_series') or {}
    forecast = time_series.get('forecast') or {}
    points = time_series.get('points') or []
    slope = float(forecast.get('slope', 0) or 0)
    baseline_value = abs(float(points[-1].get('value', 0) or 0)) if points else 0.0
    trend_summary = table.get('trend_summary') or {}
    change_percent = float(trend_summary.get('change_percent', 0) or 0)

    normalized_slope = abs(slope) / max(baseline_value, 1.0)
    if slope < 0:
        urgency = 0.45 + min(0.4, normalized_slope * 8)
        if change_percent < 0:
            urgency += min(0.15, abs(change_percent) / 100.0)
    else:
        urgency = 0.3 + min(0.2, normalized_slope * 4)

    return round(max(0.2, min(1.0, urgency)), 4)


def _default_action_hint(insight_type: str, table: dict) -> str:
    focus_measure = table.get('focus_measure_column') or 'la metrica principal'
    if insight_type == 'diagnostic':
        diagnostic = table.get('diagnostic_chain') or {}
        hypothesis = diagnostic.get('root_cause_hypothesis')
        if hypothesis:
            return hypothesis
        return f'Valida la causa raiz del cambio en {focus_measure} antes de escalar decisiones.'
    if insight_type == 'trend':
        return f'Monitorea la tendencia de {focus_measure} y confirma si el cambio es estructural.'
    if insight_type == 'segment':
        top_dimension = (table.get('top_dimensions') or [None])[0] or {}
        return f'Profundiza por {top_dimension.get("column", "segmento")} para aislar donde se concentra la desviacion.'
    if insight_type == 'correlation':
        strongest = (table.get('correlation_pairs') or [None])[0] or {}
        return (
            f'Valida si {strongest.get("left_column", "la variable lider")} y '
            f'{strongest.get("right_column", "su driver")} mantienen la relacion fuera de la muestra actual.'
        )
    return f'Revisa la calidad y dispersion de {focus_measure} antes de automatizar decisiones.'


def rank_table_insights(table: dict) -> list[dict]:
    business_impact = table.get('business_impact') or {}
    impact_score = _normalize_impact_score(business_impact)
    urgency_score = _derive_urgency_score(table)
    trend_summary = table.get('trend_summary') or {}
    diagnostic_chain = table.get('diagnostic_chain') or {}
    top_dimension = (table.get('top_dimensions') or [None])[0] or {}
    strongest_correlation = (table.get('correlation_pairs') or [None])[0] or {}
    top_outlier = (table.get('outlier_watchlist') or [None])[0] or {}

    candidates = []
    candidate_specs = [
        (
            'diagnostic',
            diagnostic_chain,
            (
                f'Diagnostico: {diagnostic_chain.get("primary_driver", {}).get("label", "driver principal")} '
                f'explica la variacion de {table.get("focus_measure_column") or "la metrica"}'
            ),
        ),
        (
            'trend',
            trend_summary if trend_summary.get('change_percent') is not None else None,
            (
                f'Tendencia: {table.get("focus_measure_column") or "la metrica"} '
                f'{format_percent(trend_summary.get("change_percent"), signed=True)}'
            ) if trend_summary.get('change_percent') is not None else '',
        ),
        (
            'segment',
            top_dimension if top_dimension else None,
            (
                f'Segmentacion: {top_dimension.get("column", "segmento")} concentra la desviacion principal'
            ) if top_dimension else '',
        ),
        (
            'correlation',
            strongest_correlation if strongest_correlation else None,
            (
                f'Driver correlacional: {strongest_correlation.get("left_column")} x {strongest_correlation.get("right_column")}'
            ) if strongest_correlation else '',
        ),
        (
            'outlier',
            top_outlier if top_outlier else None,
            (
                f'Riesgo de dispersion: {top_outlier.get("column")} tiene {top_outlier.get("outlier_percent", 0)}% de outliers'
            ) if top_outlier else '',
        ),
    ]

    for insight_type, payload, title in candidate_specs:
        if not payload:
            continue
        confidence = float(((table.get('insight_confidence') or {}).get(insight_type) or {}).get('score', 0) or 0) / 100.0
        score = impact_score * confidence * urgency_score * 100.0
        candidates.append({
            'type': insight_type,
            'title': title,
            'score': round(score, 1),
            'impact': round(impact_score * 100, 1),
            'confidence': round(confidence * 100, 1),
            'urgency': round(urgency_score * 100, 1),
            'action_hint': _default_action_hint(insight_type, table),
        })

    candidates.sort(key=lambda item: (item['score'], item['confidence'], item['impact']), reverse=True)
    for rank, candidate in enumerate(candidates[:3], start=1):
        candidate['rank'] = rank
    return candidates[:3]


def _severity_from_ranked_insights(ranked_insights: list[dict] | None) -> str:
    lead_score = float(((ranked_insights or [None])[0] or {}).get('score', 0) or 0)
    if lead_score >= 70:
        return f'Alta ({round(lead_score, 1)}/100)'
    if lead_score >= 40:
        return f'Media ({round(lead_score, 1)}/100)'
    return f'Baja ({round(lead_score, 1)}/100)'

HIGHER_IS_BETTER_KEYWORDS = {
    'revenue', 'sales', 'profit', 'margin', 'conversion', 'retention', 'throughput',
    'attendance', 'grade', 'satisfaction', 'output', 'orders',
}
LOWER_IS_BETTER_KEYWORDS = {
    'cost', 'expense', 'error', 'null', 'churn', 'delay', 'defect', 'incident',
    'downtime', 'refund', 'cancellation', 'complaint', 'variance',
}

ANALYTICS_USE_LLM_NARRATIVE = config('ANALYTICS_USE_LLM_NARRATIVE', default='false').lower() in {
    '1', 'true', 'yes', 'on'
}
ANALYTICS_NARRATIVE_MODEL = config('ANALYTICS_NARRATIVE_MODEL', default='phi3:mini')
ANALYTICS_LLM_TIMEOUT = float(config('ANALYTICS_LLM_TIMEOUT_SECONDS', default='8'))
MAX_NULL_PATTERN_ITEMS = 5
logger = logging.getLogger(__name__)


def build_business_context(dataframe, column_names, numeric_ratio: float | None = None) -> str:
    domain_scores = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = score_column_keywords(column_names, keywords)
        if score:
            domain_scores.append((score, domain))

    if not domain_scores:
        if numeric_ratio is None:
            if dataframe is None:
                numeric_ratio = 0.0
            else:
                numeric_ratio = safe_ratio(
                    len(dataframe.select_dtypes(include=['number']).columns),
                    len(column_names) or 1,
                )
        if numeric_ratio >= 0.45:
            return 'dataset analitico de operaciones y performance'
        return 'dataset general de negocio'

    domain_scores.sort(reverse=True)
    top_domains = [domain_scores[0][1]]
    if len(domain_scores) > 1 and domain_scores[1][0] >= max(1, domain_scores[0][0] - 1):
        top_domains.append(domain_scores[1][1])

    if len(top_domains) == 1:
        return f'dataset de {top_domains[0]}'
    return f'dataset de {top_domains[0]} y {top_domains[1]}'


def infer_higher_is_better(metric_context: str, business_context: str = '') -> bool:
    metric_text = f'{metric_context} {business_context}'.lower()
    if any(keyword in metric_text for keyword in LOWER_IS_BETTER_KEYWORDS):
        return False
    if any(keyword in metric_text for keyword in HIGHER_IS_BETTER_KEYWORDS):
        return True
    return True


def build_semantic_colors(data_points, metric_context, threshold=0.05):
    if not data_points:
        return data_points

    values = [float(item.get('value', 0) or 0) for item in data_points]
    if not values:
        return data_points

    average_value = float(np.mean(values))
    baseline = average_value or 1
    higher_is_better = infer_higher_is_better(metric_context)
    colored_points = []

    for item in data_points:
        value = float(item.get('value', 0) or 0)
        delta_ratio = (value - average_value) / baseline
        if abs(delta_ratio) < threshold:
            signal = 'neutral'
        elif higher_is_better:
            signal = 'positive' if delta_ratio > 0 else 'negative'
        else:
            signal = 'positive' if delta_ratio < 0 else 'negative'

        colored_points.append({
            **item,
            'color_signal': signal,
            'delta_vs_average_pct': round(delta_ratio * 100, 1),
        })

    return colored_points


def _fit_linear_trend(values):
    y = np.asarray(values, dtype=float)
    x = np.arange(len(y), dtype=float)
    if len(y) < 2:
        return np.zeros_like(y), 0.0, 0.0

    slope, intercept = np.polyfit(x, y, 1)
    fitted = slope * x + intercept
    residual_std = float(np.std(y - fitted)) if len(y) > 2 else 0.0
    return fitted, float(slope), residual_std


def _advance_period_label(last_label, steps):
    try:
        period = pd.Period(str(last_label), freq='M')
        return str(period + steps)
    except Exception:
        return f'Forecast {steps}'


def build_trend_forecast(time_series_points, periods_ahead=3):
    if not time_series_points or len(time_series_points) < 4:
        return {'forecast_points': [], 'slope': 0.0, 'residual_std': 0.0}

    n_points = len(time_series_points)
    window_size = max(4, min(6, n_points // 2))
    recent_points = time_series_points[-window_size:]
    values = [float(point.get('value', 0) or 0) for point in recent_points]
    fitted, slope, residual_std = _fit_linear_trend(values)

    forecast_points = []
    for step in range(1, periods_ahead + 1):
        estimate = values[-1] + (slope * step)
        forecast_points.append({
            'label': _advance_period_label(time_series_points[-1]['label'], step),
            'value': round(float(estimate), 4),
            'lower': round(float(estimate - residual_std), 4),
            'upper': round(float(estimate + residual_std), 4),
            'is_forecast': True,
        })

    return {
        'forecast_points': forecast_points,
        'slope': round(float(slope), 4),
        'residual_std': round(float(residual_std), 4),
    }


def build_seasonality_analysis(dataframe, date_column, measure_column):
    if not date_column:
        return None

    parsed_dates = parse_datetime_series(dataframe[date_column])
    valid_mask = parsed_dates.notna()
    if not valid_mask.any():
        return None

    values = (
        pd.to_numeric(dataframe.loc[valid_mask, measure_column], errors='coerce').fillna(0)
        if measure_column
        else pd.Series(np.ones(valid_mask.sum()), index=dataframe.index[valid_mask])
    )
    base_frame = pd.DataFrame({
        'date': parsed_dates[valid_mask],
        'value': values,
    }).dropna()
    if base_frame.empty:
        return None

    period_builders = {
        'weekday': base_frame['date'].dt.day_name(),
        'month': base_frame['date'].dt.month_name(),
        'quarter': base_frame['date'].dt.to_period('Q').astype(str),
    }

    analyses = []
    for period_name, period_series in period_builders.items():
        aggregated = base_frame.groupby(period_series)['value'].mean().dropna()
        if aggregated.shape[0] < 3:
            continue
        mean_value = float(aggregated.mean())
        std_value = float(aggregated.std(ddof=0))
        cv = std_value / mean_value if mean_value else 0.0
        analyses.append({
            'period': period_name,
            'cv': round(float(cv), 4),
            'highest_period': str(aggregated.idxmax()),
            'highest_value': round(float(aggregated.max()), 4),
            'lowest_period': str(aggregated.idxmin()),
            'lowest_value': round(float(aggregated.min()), 4),
            'deviation': round(float(std_value), 4),
        })

    if not analyses:
        return None

    analyses.sort(key=lambda item: item['cv'], reverse=True)
    strongest = analyses[0]
    return {
        'detected': strongest['cv'] > 0.15,
        'strongest_periodicity': strongest['period'],
        'peak_period': strongest['highest_period'],
        'peak_value': strongest['highest_value'],
        'trough_period': strongest['lowest_period'],
        'trough_value': strongest['lowest_value'],
        'deviation': strongest['deviation'],
        'analyses': analyses,
    }


def _min_max_scale(frame):
    minimum = frame.min(axis=0)
    maximum = frame.max(axis=0)
    denominator = (maximum - minimum).replace(0, 1)
    return (frame - minimum) / denominator


def _numpy_kmeans(data, k, iterations=30):
    if data.shape[0] < k:
        return None, None

    quantiles = np.linspace(0.1, 0.9, k)
    initial_indices = []
    seen = set()
    for quantile in quantiles:
        index = int(round((data.shape[0] - 1) * quantile))
        if index not in seen:
            initial_indices.append(index)
            seen.add(index)

    for index in range(data.shape[0]):
        if len(initial_indices) >= k:
            break
        if index not in seen:
            initial_indices.append(index)
            seen.add(index)

    centers = data[np.array(initial_indices[:k])].copy()
    global_centroid = data.mean(axis=0)

    for _ in range(iterations):
        distances = np.linalg.norm(data[:, None, :] - centers[None, :, :], axis=2)
        labels = distances.argmin(axis=1)
        new_centers = []
        for cluster_id in range(k):
            cluster_points = data[labels == cluster_id]
            if cluster_points.size == 0:
                dist_to_global = np.linalg.norm(data - global_centroid, axis=1)
                new_centers.append(data[dist_to_global.argmax()].copy())
            else:
                new_centers.append(cluster_points.mean(axis=0))
        new_centers = np.asarray(new_centers)
        if np.allclose(new_centers, centers, atol=1e-6):
            break
        centers = new_centers

    return labels, centers


def build_segment_clusters(dataframe, numeric_columns, categorical_columns):
    usable_numeric = []
    for column_name in numeric_columns:
        series = pd.to_numeric(dataframe[column_name], errors='coerce')
        if series.notna().sum() >= 6 and series.nunique(dropna=True) > 2:
            usable_numeric.append(column_name)

    if not usable_numeric:
        return None

    cluster_frame = dataframe[usable_numeric].apply(pd.to_numeric, errors='coerce').dropna()
    if cluster_frame.shape[0] < 8:
        return None

    raw_frame = cluster_frame[usable_numeric].copy()
    col_min = raw_frame.min()
    col_max = raw_frame.max()
    col_range = (col_max - col_min).replace(0, 1)
    normalized = _min_max_scale(cluster_frame)
    candidate_k = 4 if cluster_frame.shape[0] >= 20 and len(usable_numeric) >= 2 else 3

    labels = centers = None
    try:
        from sklearn.cluster import KMeans  # type: ignore

        estimator = KMeans(n_clusters=candidate_k, n_init=10, random_state=7)
        labels = estimator.fit_predict(normalized.to_numpy())
        centers = estimator.cluster_centers_
    except Exception:
        labels, centers = _numpy_kmeans(normalized.to_numpy(), candidate_k)

    if labels is None or centers is None:
        return None

    labeled_frame = cluster_frame.copy()
    labeled_frame['cluster_id'] = labels

    best_cat_col = ''
    best_cat_score = -1
    for column_name in categorical_columns:
        series_cat = dataframe[column_name].dropna().astype(str)
        n_unique = int(series_cat.nunique())
        if n_unique < 2 or n_unique > 12:
            continue
        largest_cluster_id = max(
            set(int(label) for label in labels),
            key=lambda cid: int((labeled_frame['cluster_id'] == cid).sum()),
        )
        cluster_cat = dataframe.loc[
            labeled_frame[labeled_frame['cluster_id'] == largest_cluster_id].index,
            column_name,
        ].dropna().astype(str)
        diversity = int(cluster_cat.nunique()) if not cluster_cat.empty else 0
        score = diversity * n_unique
        if score > best_cat_score:
            best_cat_score = score
            best_cat_col = column_name
    dominant_category_column = best_cat_col

    clusters = []
    for cluster_id in sorted(set(int(label) for label in labels)):
        cluster_rows = labeled_frame[labeled_frame['cluster_id'] == cluster_id]
        dominant_category = ''
        if dominant_category_column:
            dominant_series = dataframe.loc[cluster_rows.index, dominant_category_column].dropna().astype(str)
            if not dominant_series.empty:
                dominant_category = dominant_series.mode().iloc[0]

        centroid = {
            column_name: round(float(centers[cluster_id][index] * col_range[column_name] + col_min[column_name]), 4)
            for index, column_name in enumerate(usable_numeric)
        }
        clusters.append({
            'cluster_id': int(cluster_id),
            'size': int(cluster_rows.shape[0]),
            'share': round(float(cluster_rows.shape[0] / cluster_frame.shape[0]), 4),
            'centroid': centroid,
            'dominant_category_column': dominant_category_column,
            'dominant_category': dominant_category or 'Sin categoria dominante',
        })

    clusters.sort(key=lambda item: item['size'], reverse=True)
    return {
        'k': candidate_k,
        'numeric_columns': usable_numeric,
        'clusters': clusters,
    }


def build_segment_benchmarks(dataframe, dimension_column, measure_column):
    if not dimension_column or not measure_column:
        return []

    benchmark_frame = pd.DataFrame({
        'dimension': dataframe[dimension_column].astype('string').str.strip(),
        'value': pd.to_numeric(dataframe[measure_column], errors='coerce'),
    }).dropna()
    if benchmark_frame.empty:
        return []

    global_baseline = float(benchmark_frame['value'].mean())
    grouped = benchmark_frame.groupby('dimension')['value'].mean().sort_values(ascending=False)
    benchmarks = []
    for label, average_value in grouped.head(8).items():
        delta_pct = safe_ratio(float(average_value) - global_baseline, global_baseline or 1) * 100
        if delta_pct > 10:
            status = 'over'
        elif delta_pct < -10:
            status = 'under'
        else:
            status = 'on_par'
        benchmarks.append({
            'label': str(label),
            'average': round(float(average_value), 4),
            'baseline': round(global_baseline, 4),
            'delta_pct': round(float(delta_pct), 1),
            'status': status,
        })
    return benchmarks


def build_change_contribution(dataframe, date_column, dimension_column, measure_column):
    if not date_column or not dimension_column or not measure_column:
        return []

    parsed_dates = parse_datetime_series(dataframe[date_column])
    valid_mask = parsed_dates.notna()
    if valid_mask.sum() < 4:
        return []

    frame = pd.DataFrame({
        'date': parsed_dates[valid_mask],
        'dimension': dataframe.loc[valid_mask, dimension_column].astype('string').str.strip(),
        'value': pd.to_numeric(dataframe.loc[valid_mask, measure_column], errors='coerce'),
    }).dropna()
    if frame.empty:
        return []

    periods = sorted(frame['date'].dt.to_period('M').unique())
    if len(periods) < 2:
        return []

    if len(periods) >= 6:
        midpoint = len(periods) // 2
        first_half = set(periods[:midpoint])
        second_half = set(periods[midpoint:])
    elif len(periods) >= 3:
        first_half = {periods[0]}
        second_half = {periods[-1]}
    else:
        return []

    first_values = frame[frame['date'].dt.to_period('M').isin(first_half)].groupby('dimension')['value'].sum()
    second_values = frame[frame['date'].dt.to_period('M').isin(second_half)].groupby('dimension')['value'].sum()
    all_categories = sorted(set(first_values.index).union(set(second_values.index)))

    contributions = []
    total_change = float(second_values.sum() - first_values.sum())
    denominator = abs(total_change) or 1.0
    for category in all_categories:
        before = float(first_values.get(category, 0))
        after = float(second_values.get(category, 0))
        delta = after - before
        contributions.append({
            'label': str(category),
            'before': round(before, 4),
            'after': round(after, 4),
            'delta': round(delta, 4),
            'contribution_pct': round((delta / denominator) * 100, 1),
        })

    contributions.sort(key=lambda item: abs(item['delta']), reverse=True)
    return contributions[:6]


def _signal_mentions_segment(signal: dict, segment_label: str) -> bool:
    if not signal or not segment_label:
        return False

    normalized_segment = str(segment_label).strip().lower()
    for value in signal.values():
        if normalized_segment and normalized_segment in str(value).strip().lower():
            return True
    return False


def build_diagnostic_chain(table: dict) -> dict | None:
    change_contribution = table.get('change_contribution') or []
    outlier_watchlist = table.get('outlier_watchlist') or []
    correlation_pairs = table.get('correlation_pairs') or []
    focus_measure_column = table.get('focus_measure_column') or 'la metrica principal'
    trend_summary = table.get('trend_summary') or {}

    if not change_contribution:
        return None

    lead_change = change_contribution[0]
    lead_segment = str(lead_change.get('label') or '').strip()
    change_percent = trend_summary.get('change_percent')
    if change_percent is None:
        issue = f'{focus_measure_column}_shift'
    elif float(change_percent) < 0:
        issue = f'{focus_measure_column}_drop'
    elif float(change_percent) > 0:
        issue = f'{focus_measure_column}_increase'
    else:
        issue = f'{focus_measure_column}_shift'

    matching_outlier = next(
        (
            item
            for item in outlier_watchlist
            if _signal_mentions_segment(item, lead_segment)
        ),
        None,
    )
    if matching_outlier is None:
        matching_outlier = next(
            (
                item
                for item in outlier_watchlist
                if item.get('column') == focus_measure_column
            ),
            None,
        ) or (outlier_watchlist[0] if outlier_watchlist else None)

    lead_correlation = next(
        (
            item
            for item in correlation_pairs
            if focus_measure_column in {item.get('left_column'), item.get('right_column')}
        ),
        None,
    ) or (correlation_pairs[0] if correlation_pairs else None)

    evidence_chain = [{
        'signal_type': 'change_contribution',
        'label': lead_segment or 'segmento principal',
        'metric': focus_measure_column,
        'delta': round(float(lead_change.get('delta', 0) or 0), 4),
        'contribution_pct': round(float(lead_change.get('contribution_pct', 0) or 0), 1),
        'supports_issue': True,
    }]

    secondary_driver = None
    correlated_label = ''
    if matching_outlier:
        outlier_signal = {
            'signal_type': 'outlier',
            'label': matching_outlier.get('column'),
            'outlier_percent': round(float(matching_outlier.get('outlier_percent', 0) or 0), 1),
            'matches_primary_driver': _signal_mentions_segment(matching_outlier, lead_segment),
            'supports_issue': True,
        }
        evidence_chain.append(outlier_signal)
        secondary_driver = {
            'type': 'outlier',
            'label': matching_outlier.get('column'),
            'severity': outlier_signal['outlier_percent'],
        }

    if lead_correlation:
        correlated_label = (
            lead_correlation.get('right_column')
            if lead_correlation.get('left_column') == focus_measure_column
            else lead_correlation.get('left_column')
        ) or lead_correlation.get('right_column') or lead_correlation.get('left_column')
        evidence_chain.append({
            'signal_type': 'correlation',
            'label': correlated_label,
            'metric': focus_measure_column,
            'direction': lead_correlation.get('direction'),
            'absolute_correlation': round(float(lead_correlation.get('absolute_correlation', 0) or 0), 4),
            'supports_issue': True,
        })
        if secondary_driver is None:
            secondary_driver = {
                'type': 'correlation',
                'label': correlated_label,
                'strength': round(float(lead_correlation.get('absolute_correlation', 0) or 0), 4),
            }

    if lead_correlation and matching_outlier:
        root_cause_hypothesis = (
            f'La variacion de {focus_measure_column} parece concentrarse en {lead_segment}, '
            f'coincide con dispersion atipica en {matching_outlier.get("column")} y se relaciona '
            f'de forma {lead_correlation.get("direction", "relevante")} con '
            f'{correlated_label or "otra variable clave"}.'
        )
    elif lead_correlation:
        correlated_label = secondary_driver.get('label') if secondary_driver else 'otra variable clave'
        root_cause_hypothesis = (
            f'La variacion de {focus_measure_column} parece concentrarse en {lead_segment} '
            f'y podria estar explicada por movimientos {lead_correlation.get("direction", "relevantes")} '
            f'en {correlated_label}.'
        )
    elif matching_outlier:
        root_cause_hypothesis = (
            f'La variacion de {focus_measure_column} parece concentrarse en {lead_segment} '
            f'y esta amplificada por valores atipicos en {matching_outlier.get("column")}.'
        )
    else:
        root_cause_hypothesis = (
            f'La variacion de {focus_measure_column} se concentra en {lead_segment}, '
            'pero aun faltan senales complementarias para cerrar la causa raiz con alta confianza.'
        )

    return {
        'issue': issue,
        'primary_driver': {
            'type': 'segment',
            'label': lead_segment or 'segmento principal',
            'metric': focus_measure_column,
            'contribution_pct': round(float(lead_change.get('contribution_pct', 0) or 0), 1),
            'delta': round(float(lead_change.get('delta', 0) or 0), 4),
        },
        'secondary_driver': secondary_driver,
        'root_cause_hypothesis': root_cause_hypothesis,
        'evidence_chain': evidence_chain,
    }


def build_null_impact(dataframe, quality_watchlist, measure_column, dimension_column):
    if not quality_watchlist:
        return []

    measure_series = (
        pd.to_numeric(dataframe[measure_column], errors='coerce').fillna(0)
        if measure_column
        else pd.Series(np.ones(len(dataframe.index)), index=dataframe.index)
    )
    total_measure = float(measure_series.sum()) or float(len(dataframe.index)) or 1.0
    impacts = []

    for issue in quality_watchlist:
        column_name = issue['column']
        null_mask = dataframe[column_name].isna()
        if not null_mask.any():
            continue

        impacted_measure = float(measure_series[null_mask].sum())
        most_affected_segment = 'Sin segmentacion'
        if dimension_column:
            dimension_series = dataframe.loc[null_mask, dimension_column].dropna().astype(str).str.strip()
            if not dimension_series.empty:
                most_affected_segment = dimension_series.mode().iloc[0]

        impacts.append({
            'column': column_name,
            'null_count': int(null_mask.sum()),
            'measure_impact_pct': round((impacted_measure / total_measure) * 100, 1),
            'most_affected_segment': most_affected_segment,
        })

    impacts.sort(key=lambda item: (item['measure_impact_pct'], item['null_count']), reverse=True)
    return impacts[:5]


def build_null_patterns(dataframe, date_column, null_columns):
    if not null_columns:
        return []

    categorical_candidates = [
        column_name
        for column_name in dataframe.columns
        if dataframe[column_name].nunique(dropna=True) <= 10
        and dataframe[column_name].notna().sum() >= 4
    ][:3]
    parsed_dates = parse_datetime_series(dataframe[date_column]) if date_column else pd.Series(dtype='datetime64[ns]')
    patterns = []

    for item in null_columns[:MAX_NULL_PATTERN_ITEMS]:
        column_name = item['column'] if isinstance(item, dict) else str(item)
        null_mask = dataframe[column_name].isna()
        if not null_mask.any():
            continue

        pattern_candidates = []
        if date_column and parsed_dates.notna().sum():
            weekday_counts = parsed_dates[null_mask & parsed_dates.notna()].dt.day_name().value_counts()
            if weekday_counts.shape[0] >= 2:
                significant, statistic = chi_square_is_significant(weekday_counts.values)
                if significant:
                    dominant = weekday_counts.idxmax()
                    share = round(float(weekday_counts.max() / weekday_counts.sum()) * 100, 1)
                    pattern_candidates.append({
                        'column': column_name,
                        'pattern': 'systematic',
                        'detail': f'{share}% de nulos ocurre en {dominant}',
                        'basis': 'weekday',
                        'chi_square': statistic,
                    })

            month_counts = parsed_dates[null_mask & parsed_dates.notna()].dt.month_name().value_counts()
            if month_counts.shape[0] >= 2:
                significant, statistic = chi_square_is_significant(month_counts.values)
                if significant:
                    dominant = month_counts.idxmax()
                    share = round(float(month_counts.max() / month_counts.sum()) * 100, 1)
                    pattern_candidates.append({
                        'column': column_name,
                        'pattern': 'systematic',
                        'detail': f'{share}% de nulos ocurre en {dominant}',
                        'basis': 'month',
                        'chi_square': statistic,
                    })

        for category_column in categorical_candidates:
            if category_column == column_name:
                continue
            category_counts = dataframe.loc[null_mask, category_column].dropna().astype(str).value_counts()
            if category_counts.shape[0] < 2:
                continue
            significant, statistic = chi_square_is_significant(category_counts.values)
            if significant:
                dominant = category_counts.idxmax()
                share = round(float(category_counts.max() / category_counts.sum()) * 100, 1)
                pattern_candidates.append({
                    'column': column_name,
                    'pattern': 'systematic',
                    'detail': f'{share}% de nulos ocurre en categoria {dominant}',
                    'basis': category_column,
                    'chi_square': statistic,
                })

        if pattern_candidates:
            pattern_candidates.sort(key=lambda candidate: candidate['chi_square'], reverse=True)
            patterns.append(pattern_candidates[0])

    return patterns[:MAX_NULL_PATTERN_ITEMS]


def build_insight_confidence(table, insight_type):
    row_count = table.get('row_count', 0) or 0
    completeness = float(table.get('completeness_ratio', 0) or 0)
    caveat = 'La senal es util para lectura ejecutiva.'
    score = 50.0

    if insight_type == 'trend':
        time_series = table.get('time_series') or {}
        n_points = len(time_series.get('points', []))
        forecast = time_series.get('forecast') or {}
        residual_std = float(forecast.get('residual_std') or 0)
        variance_penalty = min(20, residual_std)
        score = min(100, 35 + min(40, n_points * 5) + (completeness * 20) - variance_penalty)
        if n_points < 5:
            caveat = 'La serie temporal aun es corta y puede no capturar estacionalidad completa.'
    elif insight_type == 'correlation':
        strongest = (table.get('correlation_pairs') or [None])[0] or {}
        strength = float(strongest.get('absolute_correlation', 0) or 0)
        missing_penalty = min(20, len(table.get('quality_watchlist') or []) * 4)
        left_col = strongest.get('left_column', '')
        right_col = strongest.get('right_column', '')
        watchlist_lookup = {item['column']: item for item in (table.get('quality_watchlist') or [])}
        sparsity_penalty = 0.0
        for col in [left_col, right_col]:
            if col in watchlist_lookup:
                col_completeness = float(watchlist_lookup[col].get('completeness_percent', 100) or 100)
                sparsity_penalty += max(0.0, (85.0 - col_completeness) / 5.0)
        score = min(100, 25 + min(30, row_count / 10) + (strength * 35) + (completeness * 15) - missing_penalty - sparsity_penalty)
        if strength < 0.55:
            caveat = 'La relacion existe, pero su intensidad aun es moderada.'
    elif insight_type == 'segment':
        dimension = (table.get('top_dimensions') or [None])[0] or {}
        top_values = dimension.get('top_values') or []
        dominant_share = float(top_values[0].get('share', 0) or 0) if top_values else 0
        balance_score = max(0.0, 1 - dominant_share)
        score = min(100, 30 + min(30, row_count / 12) + (balance_score * 25) + (completeness * 15))
        if dominant_share > 0.7:
            caveat = 'La segmentacion esta muy concentrada; compara con cautela las categorias menores.'
    elif insight_type == 'diagnostic':
        diagnostic_chain = table.get('diagnostic_chain') or {}
        evidence_chain = diagnostic_chain.get('evidence_chain') or []
        has_change_signal = any(item.get('signal_type') == 'change_contribution' for item in evidence_chain)
        has_secondary_signal = any(
            item.get('signal_type') in {'outlier', 'correlation'}
            for item in evidence_chain
        )
        aligned_outlier = any(
            item.get('signal_type') == 'outlier' and item.get('matches_primary_driver')
            for item in evidence_chain
        )
        score = (
            30
            + min(25, row_count / 12)
            + (completeness * 18)
            + min(18, len(evidence_chain) * 6)
            + (10 if has_change_signal and has_secondary_signal else 0)
            + (8 if aligned_outlier else 0)
        )
        if len(evidence_chain) < 2:
            score -= 18
            caveat = 'El diagnostico aun depende de una sola senal y necesita evidencia adicional.'
        elif not aligned_outlier and any(item.get('signal_type') == 'outlier' for item in evidence_chain):
            caveat = 'La cadena diagnostica es consistente, pero la evidencia de outliers aun no se alinea con el driver principal.'
        else:
            caveat = 'La cadena diagnostica combina driver, evidencia cuantitativa y una hipotesis de causa raiz.'
    else:
        outlier = (table.get('outlier_watchlist') or [None])[0] or {}
        outlier_share = float(outlier.get('outlier_share', 0) or 0)
        score = min(100, 35 + min(25, row_count / 12) + (completeness * 20) + max(0, (0.25 - outlier_share) * 80))
        if outlier_share > 0.2:
            caveat = 'Los valores extremos son relevantes; valida si responden a eventos reales o errores.'

    if score >= 75:
        level = 'alta'
    elif score >= 55:
        level = 'media'
    else:
        level = 'baja'

    return {
        'score': int(round(max(0, min(100, score)))),
        'level': level,
        'caveat': caveat,
    }


def choose_best_chart(intent, data_shape):
    n_categories = int(data_shape.get('n_categories', 0) or 0)
    is_temporal = bool(data_shape.get('is_temporal'))
    n_series = int(data_shape.get('n_series', 1) or 1)

    if intent == 'trend' and is_temporal:
        return 'combo'
    if intent == 'distribution':
        if n_categories <= 5:
            return 'donut'
        if n_categories <= 12:
            return 'bar_horizontal'
        return 'treemap'
    if intent == 'comparison':
        if max(n_categories, n_series) <= 4:
            return 'radar'
        return 'heatmap'
    if intent == 'relationship':
        return 'scatter'
    if intent == 'composition':
        return 'waterfall' if n_categories <= 6 else 'bar_horizontal'
    if intent == 'deviation':
        return 'bullet'
    return 'bar_horizontal'


def build_chart_annotations(chart_data, chart_type):
    if not chart_data:
        return []

    if chart_type in {'combo', 'line'} and len(chart_data) >= 3:
        deltas = []
        for index in range(1, len(chart_data)):
            delta_value = float(chart_data[index]['value']) - float(chart_data[index - 1]['value'])
            deltas.append((abs(delta_value), index, delta_value))
        _, target_index, delta_value = max(deltas, key=lambda item: item[0])
        target_point = chart_data[target_index]
        return [{
            'x': target_point['label'],
            'y': target_point['value'],
            'label': f'Aceleracion {round(delta_value, 1):+}',
            'type': 'inflection',
        }]

    if chart_type in {'bar', 'bar_horizontal', 'bullet', 'waterfall'}:
        average_value = float(np.mean([float(item.get('value', 0) or 0) for item in chart_data]))
        target = max(chart_data, key=lambda item: abs(float(item.get('value', 0) or 0) - average_value))
        return [{
            'x': target.get('label'),
            'y': target.get('value'),
            'label': 'Mayor desvio',
            'type': 'peak' if float(target.get('value', 0) or 0) >= average_value else 'valley',
        }]

    if chart_type == 'scatter' and len(chart_data) >= 5:
        points = np.asarray([[float(item['x']), float(item['y'])] for item in chart_data], dtype=float)
        slope, intercept = np.polyfit(points[:, 0], points[:, 1], 1)
        residuals = np.abs(points[:, 1] - ((slope * points[:, 0]) + intercept))
        top_indices = residuals.argsort()[-3:][::-1]
        return [
            {
                'x': float(chart_data[index]['x']),
                'y': float(chart_data[index]['y']),
                'label': 'Outlier',
                'type': 'outlier',
            }
            for index in top_indices
        ]

    return []


def build_reference_lines(chart_data, measure_column, business_context):
    if not chart_data:
        return []

    values = [float(item.get('value', 0) or 0) for item in chart_data]
    references = [{
        'kind': 'constant',
        'axis': 'y',
        'value': round(float(np.mean(values)), 4),
        'label': 'Promedio',
    }]

    if len(chart_data) >= 3 and all('label' in item for item in chart_data):
        fitted, _, _ = _fit_linear_trend(values)
        for index, item in enumerate(chart_data):
            item['reference_value'] = round(float(fitted[index]), 4)
        references.append({
            'kind': 'series',
            'data_key': 'reference_value',
            'label': 'Tendencia',
        })

    if 'finanzas' in business_context and any('target' in item for item in chart_data):
        target_values = [float(item['target']) for item in chart_data if item.get('target') is not None]
        if target_values:
            references.append({
                'kind': 'constant',
                'axis': 'y',
                'value': round(float(np.mean(target_values)), 4),
                'label': 'Target',
            })

    return references


def build_hero_kpi(table, business_context):
    trend = table.get('trend_summary') or {}
    dominant_dimension = (table.get('top_dimensions') or [None])[0] or {}
    quality_watchlist = table.get('quality_watchlist') or []
    lead_benchmark = (table.get('segment_benchmarks') or [None])[0] or {}
    candidates = []
    if trend.get('change_percent') is not None:
        candidates.append({
            'priority': 120,
            'value': f'{trend["change_percent"]:+.1f}%',
            'label': f'Cambio en {table.get("focus_measure_column") or "la metrica principal"}',
            'comparison': f'vs {trend.get("start_label")}',
        })
    if dominant_dimension.get('top_values'):
        dominant = dominant_dimension['top_values'][0]
        candidates.append({
            'priority': 100,
            'value': f'{round(dominant["share"] * 100, 1)}%',
            'label': f'Concentracion en {dominant["label"]}',
            'comparison': dominant_dimension.get('column', 'segmento'),
        })
    if quality_watchlist:
        worst = quality_watchlist[0]
        candidates.append({
            'priority': 110 if worst['completeness_percent'] < 90 else 70,
            'value': f'{worst["completeness_percent"]}%',
            'label': f'Completitud de {worst["column"]}',
            'comparison': 'riesgo de calidad',
        })
    if lead_benchmark and abs(float(lead_benchmark.get('delta_pct', 0) or 0)) >= 25:
        candidates.append({
            'priority': 115,
            'value': f'{float(lead_benchmark["delta_pct"]):+.1f}%',
            'label': f'Brecha de {lead_benchmark["label"]} vs baseline',
            'comparison': f'baseline: {format_compact_number(lead_benchmark["baseline"])}',
        })

    if not candidates:
        candidates.append({
            'priority': 60,
            'value': format_compact_number(table.get('row_count', 0)),
            'label': f'Filas en {business_context}',
            'comparison': 'base analizada',
        })

    candidates.sort(key=lambda item: item['priority'], reverse=True)
    hero_kpi = candidates[0]
    value_str = str(hero_kpi['value']).replace('%', '').replace('+', '').strip()
    try:
        numeric_value = float(value_str)
        label_text = hero_kpi['label'].lower()
        is_trend_metric = 'cambio' in label_text or 'variacion' in label_text
        is_quality_metric = 'completitud' in label_text
        if is_quality_metric:
            color = 'negative' if numeric_value < 95 else 'positive'
        elif is_trend_metric:
            color = 'positive' if numeric_value >= 0 else 'negative'
        else:
            color = 'neutral'
    except (TypeError, ValueError):
        color = 'neutral'

    hero_kpi['color_signal'] = color
    return hero_kpi


def build_slide_layout(slide, table):
    hero_kpi = slide.get('hero_kpi') or build_hero_kpi(table, table.get('business_context', 'negocio'))
    supporting_elements = [
        item
        for item in ['question', 'situation', 'complication', 'severity', 'implication', 'action', 'confidence']
        if slide.get(item)
    ]
    suppress = []
    if not slide.get('annotations'):
        suppress.append('annotations')
    if not slide.get('reference_lines'):
        suppress.append('reference_lines')
    return {
        'hero_metric': hero_kpi,
        'supporting_elements': supporting_elements,
        'suppress': suppress,
    }


def _llm_json_response(prompt):
    result = [None]
    error = [None]

    def _call():
        try:
            response = get_ai_response(
                prompt,
                max_tokens=500,
                model_override=ANALYTICS_NARRATIVE_MODEL,
            )
            start = response.find('{')
            end = response.rfind('}')
            if start == -1 or end == -1:
                logger.warning('Analytics narrative LLM returned a response without valid JSON boundaries.')
                return
            result[0] = json.loads(response[start:end + 1])
        except Exception as exc:
            error[0] = exc

    thread = threading.Thread(target=_call, daemon=True)
    thread.start()
    thread.join(timeout=ANALYTICS_LLM_TIMEOUT)

    if thread.is_alive():
        logger.warning(
            'LLM timeout tras %.1fs (modelo: %s)',
            ANALYTICS_LLM_TIMEOUT,
            ANALYTICS_NARRATIVE_MODEL,
        )
        return None

    if error[0]:
        logger.warning('Analytics narrative LLM failed to return valid JSON: %s', error[0])
        return None

    return result[0]


def build_narrative_arc(
    *,
    business_context,
    question,
    situation,
    complication,
    implication,
    action,
    stats,
    ranked_insights=None,
    diagnostic_chain=None,
):
    severity = _severity_from_ranked_insights(ranked_insights)
    fallback_arc = {
        'question': question,
        'situation': situation,
        'complication': complication,
        'severity': severity,
        'implication': implication,
        'action': action,
        'llm_used': False,
    }

    if not ANALYTICS_USE_LLM_NARRATIVE:
        return fallback_arc

    prompt = (
        'Actua como un redactor ejecutivo de analitica avanzada. '
        'No descubras hallazgos nuevos: usa exclusivamente los insights priorizados y el diagnostico ya identificados. '
        'Devuelve solo JSON valido con las claves: question, situation, complication, severity, implication, action. '
        f'Contexto de negocio: {business_context}. '
        f'Pregunta central: {question}. '
        f'Insights priorizados: {json.dumps(ranked_insights or [], ensure_ascii=True)}. '
        f'Diagnostico estructurado: {json.dumps(diagnostic_chain or {}, ensure_ascii=True)}. '
        f'Datos de apoyo: {json.dumps(stats, ensure_ascii=True)}. '
        'IMPORTANTE: cada campo del JSON debe citar al menos un numero concreto de los datos cuando exista. '
        'La severidad debe responder explicitamente que tan grave es el hallazgo principal. '
        'No uses frases genericas ni placeholders. Redacta a partir de estos hallazgos ya curados. '
        'Responde en espanol con tono ejecutivo, claro y accionable.'
    )
    llm_arc = _llm_json_response(prompt)
    if not llm_arc:
        return fallback_arc

    return {
        'question': llm_arc.get('question') or question,
        'situation': llm_arc.get('situation') or situation,
        'complication': llm_arc.get('complication') or complication,
        'severity': llm_arc.get('severity') or severity,
        'implication': llm_arc.get('implication') or implication,
        'action': llm_arc.get('action') or action,
        'llm_used': True,
    }
