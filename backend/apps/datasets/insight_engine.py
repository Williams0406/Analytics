from __future__ import annotations

from .analysis_enrichment import (
    DOMAIN_KEYWORDS,
    HIGHER_IS_BETTER_KEYWORDS,
    IMPACT_FORMULAS,
    LOWER_IS_BETTER_KEYWORDS,
    _default_action_hint,
    _derive_urgency_score,
    _normalize_impact_score,
    _resolve_impact_formula,
    build_business_context,
    build_business_impact,
    build_change_contribution,
    build_diagnostic_chain,
    build_insight_confidence,
    build_seasonality_analysis,
    build_segment_benchmarks,
    build_segment_clusters,
    build_trend_forecast,
    infer_higher_is_better,
    rank_table_insights,
)


def build_time_series(*args, **kwargs):
    from .analysis_summary import build_time_series as legacy_build_time_series

    return legacy_build_time_series(*args, **kwargs)


def build_trend_summary(*args, **kwargs):
    from .analysis_summary import build_trend_summary as legacy_build_trend_summary

    return legacy_build_trend_summary(*args, **kwargs)


def build_correlation_pairs(*args, **kwargs):
    from .analysis_summary import build_correlation_pairs as legacy_build_correlation_pairs

    return legacy_build_correlation_pairs(*args, **kwargs)


def build_outlier_watchlist(*args, **kwargs):
    from .analysis_summary import build_outlier_watchlist as legacy_build_outlier_watchlist

    return legacy_build_outlier_watchlist(*args, **kwargs)


def _resolve_dominant_signal_type(table: dict, ranked_insights: list[dict]) -> str:
    lead_ranked = (ranked_insights or [None])[0] or {}
    lead_type = str(lead_ranked.get('type') or '').strip().lower()
    if lead_type:
        return lead_type
    if table.get('trend_summary'):
        return 'trend'
    if table.get('diagnostic_chain'):
        return 'diagnostic'
    if table.get('segment_benchmarks') or table.get('top_dimensions'):
        return 'segment'
    if table.get('correlation_pairs'):
        return 'correlation'
    if table.get('outlier_watchlist') or table.get('quality_watchlist'):
        return 'risk'
    return 'structure'


def build_insight_bundle(table: dict) -> dict:
    ranked_insights = table.get('ranked_insights') or rank_table_insights(table)
    diagnostic_chain = table.get('diagnostic_chain') or build_diagnostic_chain(table) or {}
    insight_confidence = table.get('insight_confidence') or {
        'trend': build_insight_confidence(table, 'trend'),
        'correlation': build_insight_confidence(table, 'correlation'),
        'segment': build_insight_confidence(table, 'segment'),
        'diagnostic': build_insight_confidence(table, 'diagnostic'),
        'outlier': build_insight_confidence(table, 'outlier'),
    }
    dominant_signal_type = _resolve_dominant_signal_type(table, ranked_insights)
    primary_insight = (ranked_insights or [None])[0] or {}

    return {
        'table_name': table.get('name', ''),
        'business_context': table.get('business_context', ''),
        'focus_measure_column': table.get('focus_measure_column', ''),
        'dominant_signal': {
            'type': dominant_signal_type,
            'title': primary_insight.get('title') or diagnostic_chain.get('root_cause_hypothesis', ''),
            'score': primary_insight.get('score'),
            'metric': (
                primary_insight.get('metric')
                or ((diagnostic_chain or {}).get('primary_driver') or {}).get('metric')
                or table.get('focus_measure_column', '')
            ),
        },
        'primary_insight': primary_insight,
        'top_insights': ranked_insights[:3],
        'ranked_insights': ranked_insights,
        'diagnostic_chain': diagnostic_chain,
        'business_impact': table.get('business_impact'),
        'insight_confidence': insight_confidence,
        'hero_kpi': table.get('hero_kpi'),
        'signals': {
            'trend_summary': table.get('trend_summary'),
            'seasonality_analysis': table.get('seasonality_analysis'),
            'correlation_pairs': table.get('correlation_pairs', []),
            'outlier_watchlist': table.get('outlier_watchlist', []),
            'segment_benchmarks': table.get('segment_benchmarks', []),
            'change_contribution': table.get('change_contribution', []),
            'quality_watchlist': table.get('quality_watchlist', []),
        },
    }
