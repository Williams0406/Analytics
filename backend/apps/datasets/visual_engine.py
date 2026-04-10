from __future__ import annotations

from copy import deepcopy

from .analysis_enrichment import (
    build_chart_annotations,
    build_hero_kpi,
    build_reference_lines,
    build_semantic_colors,
    build_slide_layout,
)

DESIGN_TOKENS = {
    'base': {
        'theme_name': 'light_editorial',
        'spacing': [8, 16, 24, 40, 64],
        'typography': {'eyebrow': 12, 'headline': 48, 'title': 28, 'body': 16, 'caption': 12},
        'colors': {
            'canvas': '#F7F8FC',
            'surface': '#FFFFFF',
            'surface_alt': '#EEF2FF',
            'text_primary': '#0F172A',
            'text_secondary': '#475569',
            'border': '#D8E1F0',
            'accent': '#3258FF',
            'accent_alt': '#0EA5A4',
            'warning': '#D4A72C',
            'alert': '#F46D43',
            'success': '#1F9D72',
        },
        'radius': {'card': 24, 'badge': 999},
        'chart_palette': ['#3258FF', '#0EA5A4', '#F46D43', '#D4A72C', '#111827'],
    },
    'alert': {
        'theme_name': 'alert_editorial',
        'colors': {
            'surface_alt': '#FFF1EC',
            'accent': '#F46D43',
            'accent_alt': '#B91C1C',
            'alert': '#C2410C',
            'border': '#F7C7B8',
        },
        'chart_palette': ['#F46D43', '#B91C1C', '#F97316', '#F59E0B', '#111827'],
    },
    'opportunity': {
        'theme_name': 'opportunity_editorial',
        'colors': {
            'surface_alt': '#E8FFFA',
            'accent': '#0EA5A4',
            'accent_alt': '#1F9D72',
            'success': '#0F766E',
            'border': '#BEE9E3',
        },
        'chart_palette': ['#0EA5A4', '#1F9D72', '#3258FF', '#D4A72C', '#0F172A'],
    },
    'performance': {
        'theme_name': 'performance_editorial',
        'colors': {
            'surface_alt': '#EEF2FF',
            'accent': '#3258FF',
            'accent_alt': '#1D4ED8',
            'border': '#CBD5F5',
        },
    },
}

VISUAL_INTENT_MAP = {
    ('hero', '*', '*'): 'executive_summary',
    ('chart', 'diagnostic', 'high'): 'root_cause_story',
    ('chart', 'diagnostic', 'medium'): 'root_cause_story',
    ('chart', 'diagnostic', 'low'): 'evidence_context',
    ('chart', 'trend', 'high'): 'hero_trend_story',
    ('chart', 'trend', 'medium'): 'hero_trend_story',
    ('chart', 'trend', 'low'): 'trend_context',
    ('chart', 'segment', '*'): 'segment_comparison',
    ('chart', 'benchmark', '*'): 'benchmark_comparison',
    ('chart', 'correlation', '*'): 'correlation_story',
    ('chart', 'outlier', '*'): 'risk_alert',
    ('chart', 'risk', '*'): 'risk_alert',
    ('chart', 'structure', '*'): 'exploration_overview',
    ('chart', 'default', '*'): 'exploration_overview',
    ('*', '*', '*'): 'exploration_overview',
}

LAYOUT_RULES = {
    'executive_summary': {
        'template_name': 'situation_full',
        'zones': {'headline': [0, 0, 12, 2], 'visual': [0, 2, 12, 4], 'insight': [0, 6, 12, 2], 'footer': [0, 8, 12, 2]},
        'proportions': {'headline': 0.2, 'visual': 0.4, 'insight': 0.22, 'footer': 0.18},
    },
    'hero_trend_story': {
        'template_name': 'hero_split',
        'zones': {'headline': [0, 0, 12, 2], 'visual': [0, 2, 8, 6], 'insight': [8, 2, 4, 6], 'footer': [0, 8, 12, 2]},
        'proportions': {'headline': 0.18, 'visual': 0.52, 'insight': 0.22, 'footer': 0.08},
    },
    'trend_context': {
        'template_name': 'chart_dominant',
        'zones': {'headline': [0, 0, 12, 2], 'visual': [0, 2, 12, 5], 'insight': [0, 7, 12, 2], 'footer': [0, 9, 12, 1]},
        'proportions': {'headline': 0.18, 'visual': 0.5, 'insight': 0.22, 'footer': 0.1},
    },
    'segment_comparison': {
        'template_name': 'split_horizontal',
        'zones': {'headline': [0, 0, 12, 2], 'visual': [0, 2, 7, 6], 'insight': [7, 2, 5, 6], 'footer': [0, 8, 12, 2]},
        'proportions': {'headline': 0.18, 'visual': 0.48, 'insight': 0.24, 'footer': 0.1},
    },
    'benchmark_comparison': {
        'template_name': 'dual_chart',
        'zones': {'headline': [0, 0, 12, 2], 'visual': [0, 2, 7, 6], 'insight': [7, 2, 5, 6], 'footer': [0, 8, 12, 2]},
        'proportions': {'headline': 0.16, 'visual': 0.5, 'insight': 0.24, 'footer': 0.1},
    },
    'root_cause_story': {
        'template_name': 'evidence_grid',
        'zones': {'headline': [0, 0, 12, 2], 'visual': [0, 2, 8, 6], 'insight': [8, 2, 4, 6], 'footer': [0, 8, 12, 2]},
        'proportions': {'headline': 0.18, 'visual': 0.48, 'insight': 0.24, 'footer': 0.1},
    },
    'evidence_context': {
        'template_name': 'split_horizontal',
        'zones': {'headline': [0, 0, 12, 2], 'visual': [0, 2, 8, 5], 'insight': [8, 2, 4, 5], 'footer': [0, 7, 12, 3]},
        'proportions': {'headline': 0.18, 'visual': 0.42, 'insight': 0.2, 'footer': 0.2},
    },
    'correlation_story': {
        'template_name': 'dual_chart',
        'zones': {'headline': [0, 0, 12, 2], 'visual': [0, 2, 8, 6], 'insight': [8, 2, 4, 6], 'footer': [0, 8, 12, 2]},
        'proportions': {'headline': 0.16, 'visual': 0.5, 'insight': 0.24, 'footer': 0.1},
    },
    'risk_alert': {
        'template_name': 'dual_chart',
        'zones': {'headline': [0, 0, 12, 2], 'visual': [0, 2, 7, 6], 'insight': [7, 2, 5, 6], 'footer': [0, 8, 12, 2]},
        'proportions': {'headline': 0.16, 'visual': 0.46, 'insight': 0.28, 'footer': 0.1},
    },
    'exploration_overview': {
        'template_name': 'chart_dominant',
        'zones': {'headline': [0, 0, 12, 2], 'visual': [0, 2, 12, 5], 'insight': [0, 7, 12, 2], 'footer': [0, 9, 12, 1]},
        'proportions': {'headline': 0.18, 'visual': 0.5, 'insight': 0.22, 'footer': 0.1},
    },
}

TEMPLATE_REGISTRY = {
    'executive_summary': {'template_name': 'ExecutiveSummary', 'required_primitives': ['headline', 'kpi_badge', 'primary_chart', 'callouts']},
    'hero_trend_story': {'template_name': 'HeroSlide', 'required_primitives': ['headline', 'kpi_badge', 'primary_chart', 'annotations', 'reference_lines', 'callouts']},
    'trend_context': {'template_name': 'TrendContextSlide', 'required_primitives': ['headline', 'primary_chart', 'annotations', 'reference_lines', 'callouts']},
    'segment_comparison': {'template_name': 'SplitSlide', 'required_primitives': ['headline', 'kpi_badge', 'primary_chart', 'supporting_charts', 'callouts']},
    'benchmark_comparison': {'template_name': 'ComparisonSlide', 'required_primitives': ['headline', 'primary_chart', 'supporting_charts', 'reference_lines', 'callouts']},
    'root_cause_story': {'template_name': 'DiagnosticSlide', 'required_primitives': ['headline', 'kpi_badge', 'primary_chart', 'supporting_charts', 'annotations', 'reference_lines', 'callouts']},
    'evidence_context': {'template_name': 'EvidenceSlide', 'required_primitives': ['headline', 'primary_chart', 'supporting_charts', 'callouts']},
    'correlation_story': {'template_name': 'RelationshipSlide', 'required_primitives': ['headline', 'primary_chart', 'supporting_charts', 'annotations', 'callouts']},
    'risk_alert': {'template_name': 'AlertSlide', 'required_primitives': ['headline', 'kpi_badge', 'primary_chart', 'supporting_charts', 'annotations', 'callouts']},
    'exploration_overview': {'template_name': 'ChartSlide', 'required_primitives': ['headline', 'primary_chart', 'supporting_charts', 'annotations', 'reference_lines', 'callouts']},
}

_NARRATIVE_STAGE_TO_SIGNAL = {
    'Exploracion Temporal': 'trend',
    'Segmentacion': 'segment',
    'Benchmarking': 'benchmark',
    'Causalidad': 'diagnostic',
    'Drivers': 'diagnostic',
    'Riesgo': 'risk',
    'Contexto': 'structure',
    'Exploracion': 'trend',
}


def _deep_merge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _lookup_visual_intent(slide_type: str, signal_type: str, urgency_tone: str) -> str:
    candidates = [
        (slide_type, signal_type, urgency_tone),
        (slide_type, signal_type, '*'),
        (slide_type, '*', urgency_tone),
        (slide_type, '*', '*'),
        ('*', signal_type, urgency_tone),
        ('*', signal_type, '*'),
        ('*', '*', urgency_tone),
        ('*', '*', '*'),
    ]
    for key in candidates:
        if key in VISUAL_INTENT_MAP:
            return VISUAL_INTENT_MAP[key]
    return 'exploration_overview'


def _find_layout_by_name(layout_name: str | None) -> dict | None:
    if not layout_name:
        return None
    for value in LAYOUT_RULES.values():
        if value.get('template_name') == layout_name:
            return deepcopy(value)
    return None


def _normalize_slide_payload(slide_payload: dict | None) -> dict:
    payload = deepcopy(slide_payload or {})
    if 'primary_chart' not in payload:
        if payload.get('charts'):
            payload['primary_chart'] = deepcopy((payload['charts'] or [None])[0] or {})
            payload['supporting_charts'] = deepcopy((payload['charts'] or [])[1:])
        elif payload.get('chart_type'):
            payload['primary_chart'] = {
                key: value
                for key, value in payload.items()
                if key not in {'type', 'layout', 'layout_name', 'layout_hint', 'template', 'primitives', 'design_tokens', 'motion', 'narrative_overlays', 'text_blocks', 'supporting_charts'}
            }
    payload.setdefault('slide_type', payload.get('type') or 'chart')
    payload.setdefault('narrative', payload.get('narrative') or {})
    payload.setdefault('supporting_charts', deepcopy(payload.get('supporting_charts') or []))
    return payload


def _resolve_signal_type(payload: dict, table: dict | None = None) -> str:
    narrative = payload.get('narrative') or {}
    signal_type = payload.get('signal_type') or narrative.get('signal_type') or narrative.get('insight_type')
    if signal_type:
        return str(signal_type).lower()
    stage = narrative.get('stage')
    if stage in _NARRATIVE_STAGE_TO_SIGNAL:
        return _NARRATIVE_STAGE_TO_SIGNAL[stage]
    dominant_signal = ((table or {}).get('insight_bundle') or {}).get('dominant_signal') or {}
    if dominant_signal.get('type'):
        return str(dominant_signal['type']).lower()
    chart_type = (payload.get('primary_chart') or {}).get('chart_type')
    if chart_type in {'combo', 'line', 'trend'}:
        return 'trend'
    if chart_type in {'scatter', 'heatmap'}:
        return 'correlation'
    if chart_type in {'bullet', 'waterfall'}:
        return 'diagnostic'
    if chart_type in {'bar', 'bar_horizontal', 'treemap', 'donut'}:
        return 'segment'
    return 'default'


def resolve_visual_intent(
    slide_type: str,
    story_objective: dict | None = None,
    signal_type: str | None = None,
    urgency_tone: str | None = None,
) -> str:
    story_objective = story_objective or {}
    normalized_signal = str(signal_type or 'default').lower()
    normalized_urgency = str(urgency_tone or story_objective.get('urgency_tone') or 'low').lower()
    return _lookup_visual_intent(str(slide_type or 'chart').lower(), normalized_signal, normalized_urgency)


def resolve_layout(
    slide_type: str,
    story_objective: dict | None = None,
    default_layout: str = 'chart_dominant',
    *,
    visual_intent: str | None = None,
    signal_type: str | None = None,
) -> dict:
    intent = visual_intent or resolve_visual_intent(
        slide_type,
        story_objective,
        signal_type=signal_type,
        urgency_tone=(story_objective or {}).get('urgency_tone'),
    )
    resolved = deepcopy(LAYOUT_RULES.get(intent) or {})
    if not resolved:
        resolved = _find_layout_by_name(default_layout) or deepcopy(LAYOUT_RULES['exploration_overview'])
    resolved['visual_intent'] = intent
    return resolved


def resolve_template(visual_intent: str) -> dict:
    template = deepcopy(TEMPLATE_REGISTRY.get(visual_intent) or TEMPLATE_REGISTRY['exploration_overview'])
    template['visual_intent'] = visual_intent
    return template


def _resolve_story_metadata(
    narrative: dict,
    table: dict | None = None,
    explicit_story_objective: dict | None = None,
) -> tuple[dict, dict]:
    narrative = deepcopy(narrative or {})
    story_objective = deepcopy(explicit_story_objective or narrative.get('story_objective') or {})
    if not table:
        if story_objective:
            narrative['story_objective'] = story_objective
        return narrative, story_objective

    insight_bundle = table.get('insight_bundle') or {}
    if not insight_bundle:
        try:
            from .insight_engine import build_insight_bundle
        except ImportError:
            build_insight_bundle = None
        if build_insight_bundle:
            insight_bundle = build_insight_bundle(table)

    if not insight_bundle:
        if story_objective:
            narrative['story_objective'] = story_objective
        return narrative, story_objective

    from .story_engine import build_executive_ask, build_message_hierarchy, resolve_story_objective as resolve_story_goal

    if not story_objective:
        story_objective = resolve_story_goal(insight_bundle)
    if story_objective:
        narrative['story_objective'] = story_objective
    if not narrative.get('message_hierarchy'):
        narrative['message_hierarchy'] = build_message_hierarchy(insight_bundle, story_objective)
    if not narrative.get('executive_ask'):
        narrative['executive_ask'] = build_executive_ask(story_objective, insight_bundle.get('diagnostic_chain'))
    return narrative, story_objective


def _decorate_chart(
    chart: dict,
    *,
    role: str,
    size_hint: str,
    metric_context: str = '',
    business_context: str = '',
) -> dict:
    decorated = deepcopy(chart or {})
    decorated['role'] = decorated.get('role', role)
    decorated['size_hint'] = decorated.get('size_hint', size_hint)
    chart_type = decorated.get('chart_type')
    chart_data = [deepcopy(item) for item in (decorated.get('data') or [])]
    supports_series = chart_type in {'bar', 'bar_horizontal', 'bullet', 'waterfall', 'line', 'combo'}

    if chart_data and supports_series and all(isinstance(item, dict) and 'value' in item for item in chart_data):
        if not all('color_signal' in item for item in chart_data):
            chart_data = build_semantic_colors(chart_data, metric_context or business_context or '')
        decorated['data'] = chart_data

    if chart_data and supports_series and not decorated.get('annotations'):
        decorated['annotations'] = build_chart_annotations(chart_data, chart_type)
    if chart_data and chart_type in {'bar', 'bar_horizontal', 'line', 'combo'} and not decorated.get('reference_lines'):
        decorated['reference_lines'] = build_reference_lines(chart_data, metric_context, business_context)
    return decorated


def _resolve_supporting_charts(
    template_config: dict,
    payload: dict,
    table: dict | None,
    *,
    metric_context: str,
    business_context: str,
) -> list[dict]:
    explicit_supporting = deepcopy(payload.get('supporting_charts') or [])
    if explicit_supporting:
        raw_supporting = explicit_supporting
    elif table and (payload.get('narrative') or {}):
        from .analysis_summary import _select_supporting_charts

        raw_supporting = _select_supporting_charts(table, payload.get('primary_chart') or {}, payload.get('narrative') or {})
    else:
        raw_supporting = []

    if 'supporting_charts' not in template_config.get('required_primitives', []) and not explicit_supporting:
        return []

    return [
        _decorate_chart(
            chart,
            role=chart.get('role', 'supporting'),
            size_hint=chart.get('size_hint', 'small'),
            metric_context=metric_context,
            business_context=business_context,
        )
        for chart in raw_supporting
    ]


def _build_primitive_callouts(narrative: dict, table: dict | None = None) -> list[dict]:
    callouts = []
    signal_value = narrative.get('signal_value')
    signal_label = narrative.get('signal_label')
    if signal_value not in (None, '') and signal_label:
        callouts.append({
            'type': 'metric_signal',
            'label': signal_label,
            'value': signal_value,
            'tone': 'accent',
        })

    for field in ['finding', 'conclusion', 'recommendation']:
        text = narrative.get(field)
        if text:
            callouts.append({
                'type': field,
                'label': field,
                'text': text,
                'tone': 'neutral',
            })

    diagnostic_chain = (table or {}).get('diagnostic_chain') or {}
    primary_driver = diagnostic_chain.get('primary_driver') or {}
    if primary_driver.get('label'):
        callouts.insert(0, {
            'type': 'primary_driver',
            'label': primary_driver['label'],
            'text': (
                f'{primary_driver["label"]} explica '
                f'{primary_driver.get("contribution_pct", 0)}% del cambio en '
                f'{primary_driver.get("metric", "el KPI principal")}.'
            ),
            'tone': 'highlight',
        })
    return callouts[:4]


def compose_slide_primitives(template_config: dict, slide_data: dict, table: dict | None = None) -> dict:
    payload = _normalize_slide_payload(slide_data)
    narrative = payload.get('narrative') or {}
    primary_chart = payload.get('primary_chart') or {}
    metric_context = (
        (table or {}).get('focus_measure_column')
        or primary_chart.get('value_label')
        or narrative.get('signal_label', '')
    )
    business_context = (table or {}).get('business_context', '')
    hero_kpi = narrative.get('hero_kpi') or (table or {}).get('hero_kpi') or (
        build_hero_kpi(table, business_context or 'dataset de negocio') if table else None
    )

    decorated_primary = _decorate_chart(
        primary_chart,
        role='primary',
        size_hint='large',
        metric_context=metric_context,
        business_context=business_context,
    )
    supporting_charts = _resolve_supporting_charts(
        template_config,
        payload,
        table,
        metric_context=metric_context,
        business_context=business_context,
    )

    from .analysis_summary import build_text_blocks_for_slide

    text_blocks = payload.get('text_blocks')
    if text_blocks is None and narrative and table:
        text_blocks = build_text_blocks_for_slide(narrative, table, decorated_primary, supporting_charts)

    headline = {
        'title': decorated_primary.get('title') or narrative.get('question') or narrative.get('finding') or 'Insight principal',
        'subtitle': decorated_primary.get('subtitle') or narrative.get('situation') or narrative.get('conclusion') or '',
    }

    return {
        'headline': headline,
        'kpi_badge': hero_kpi,
        'primary_chart': decorated_primary,
        'supporting_charts': supporting_charts,
        'annotations': decorated_primary.get('annotations', []),
        'reference_lines': decorated_primary.get('reference_lines', []),
        'callouts': _build_primitive_callouts(narrative, table),
        'text_blocks': text_blocks or [],
    }


def build_narrative_overlays(
    visual_intent: str,
    slide_payload: dict,
    diagnostic_chain: dict | None,
) -> dict:
    payload = _normalize_slide_payload(slide_payload)
    primary_chart = payload.get('primary_chart') or {}
    narrative = payload.get('narrative') or {}
    diagnostic_chain = diagnostic_chain or {}

    overlays = {
        'overlays': [],
        'callouts': [],
        'connectors': [],
        'highlight_zones': [],
    }

    primary_driver = diagnostic_chain.get('primary_driver') or {}
    if visual_intent == 'root_cause_story' and primary_driver.get('label'):
        overlays['callouts'].append({
            'type': 'driver_callout',
            'target': primary_driver['label'],
            'text': (
                f'{primary_driver["label"]} es el principal driver y aporta '
                f'{primary_driver.get("contribution_pct", 0)}% del cambio.'
            ),
            'tone': 'high',
        })
        overlays['connectors'].append({
            'type': 'arrow',
            'from': 'visual',
            'to': primary_driver['label'],
            'style': 'editorial_arrow',
        })

    if visual_intent == 'risk_alert':
        risk_source = (
            (primary_chart.get('annotations') or [None])[0]
            or (payload.get('narrative', {}).get('evidence') or [None])[0]
        )
        if risk_source:
            overlays['highlight_zones'].append({
                'target': risk_source.get('x') if isinstance(risk_source, dict) else 'visual_outlier',
                'label': risk_source.get('label', 'Outlier') if isinstance(risk_source, dict) else str(risk_source),
                'tone': 'alert',
            })

    if visual_intent in {'trend_context', 'hero_trend_story'}:
        inflections = primary_chart.get('annotations') or build_chart_annotations(
            primary_chart.get('data') or [],
            primary_chart.get('chart_type'),
        )
        for annotation in inflections:
            if annotation.get('type') == 'inflection':
                overlays['overlays'].append({
                    'type': 'inflection_annotation',
                    'target': annotation.get('x'),
                    'label': annotation.get('label'),
                    'tone': 'context',
                })

    if narrative.get('recommendation'):
        overlays['callouts'].append({
            'type': 'recommendation',
            'target': 'footer',
            'text': narrative['recommendation'],
            'tone': 'neutral',
        })

    return overlays


def resolve_tokens(urgency_tone: str | None, objective_type: str | None) -> dict:
    urgency_tone = str(urgency_tone or 'low').lower()
    objective_type = str(objective_type or 'performance_review').lower()

    tokens = deepcopy(DESIGN_TOKENS['base'])
    if objective_type == 'opportunity_capture':
        tokens = _deep_merge(tokens, DESIGN_TOKENS['opportunity'])
    elif objective_type == 'performance_review':
        tokens = _deep_merge(tokens, DESIGN_TOKENS['performance'])

    if urgency_tone == 'high':
        tokens = _deep_merge(tokens, DESIGN_TOKENS['alert'])

    tokens['urgency_tone'] = urgency_tone
    tokens['objective_type'] = objective_type
    return tokens


def build_motion_config(visual_intent: str, urgency_tone: str | None) -> dict:
    urgency_tone = str(urgency_tone or 'low').lower()
    presets = {
        'root_cause_story': {'entrance': 'line_draw', 'stagger': True, 'duration_ms': 900, 'hover': 'glow'},
        'risk_alert': {'entrance': 'count_up', 'stagger': False, 'duration_ms': 650, 'hover': 'glow'},
        'hero_trend_story': {'entrance': 'line_draw', 'stagger': True, 'duration_ms': 850, 'hover': None},
        'trend_context': {'entrance': 'fade_in', 'stagger': True, 'duration_ms': 600, 'hover': None},
        'executive_summary': {'entrance': 'fade_in', 'stagger': True, 'duration_ms': 500, 'hover': 'scale'},
    }
    motion = deepcopy(presets.get(visual_intent) or {
        'entrance': 'fade_in',
        'stagger': True,
        'duration_ms': 600,
        'hover': 'scale',
    })
    if urgency_tone == 'high':
        motion['duration_ms'] = min(int(motion['duration_ms']), 700)
    return motion


def render_slide(
    slide_payload: dict,
    table: dict | None = None,
    story_objective: dict | None = None,
) -> dict:
    payload = _normalize_slide_payload(slide_payload)
    narrative, resolved_story_objective = _resolve_story_metadata(
        payload.get('narrative') or {},
        table,
        explicit_story_objective=story_objective,
    )
    payload['narrative'] = narrative

    signal_type = _resolve_signal_type(payload, table)
    visual_intent = resolve_visual_intent(
        payload.get('slide_type', 'chart'),
        resolved_story_objective,
        signal_type=signal_type,
        urgency_tone=resolved_story_objective.get('urgency_tone'),
    )
    layout = resolve_layout(
        payload.get('slide_type', 'chart'),
        resolved_story_objective,
        default_layout=payload.get('layout_name') or payload.get('layout') or 'chart_dominant',
        visual_intent=visual_intent,
        signal_type=signal_type,
    )
    template_config = resolve_template(visual_intent)
    primitives = compose_slide_primitives(template_config, payload, table)

    enriched_payload = {
        **payload,
        'primary_chart': primitives['primary_chart'],
        'supporting_charts': primitives['supporting_charts'],
        'narrative': narrative,
    }
    narrative_overlays = build_narrative_overlays(
        visual_intent,
        enriched_payload,
        (table or {}).get('diagnostic_chain') or {},
    )
    design_tokens = resolve_tokens(
        resolved_story_objective.get('urgency_tone'),
        resolved_story_objective.get('objective_type'),
    )
    motion = build_motion_config(visual_intent, resolved_story_objective.get('urgency_tone'))

    primary_chart = primitives['primary_chart']
    all_charts = [primary_chart, *primitives['supporting_charts']]
    slide = {
        'type': payload.get('slide_type', 'chart'),
        'layout': layout,
        'layout_name': layout.get('template_name'),
        'visual_intent': visual_intent,
        'signal_type': signal_type,
        'template': template_config,
        'template_name': template_config.get('template_name'),
        'primitives': primitives,
        'design_tokens': design_tokens,
        'motion': motion,
        'narrative_overlays': narrative_overlays,
        'overlays': narrative_overlays['overlays'],
        'callouts': narrative_overlays['callouts'],
        'connectors': narrative_overlays['connectors'],
        'highlight_zones': narrative_overlays['highlight_zones'],
        **primary_chart,
        'charts': all_charts,
        'annotations': primitives['annotations'],
        'reference_lines': primitives['reference_lines'],
        'text_blocks': primitives['text_blocks'],
        'story_objective': resolved_story_objective,
    }
    if narrative:
        slide.update(narrative)
    if table:
        slide['layout_hint'] = build_slide_layout(slide, table)
    return slide


def make_chart_slide(
    primary_chart: dict,
    narrative: dict | None = None,
    table: dict | None = None,
    *,
    supporting_charts: list[dict] | None = None,
    text_blocks: list[dict] | None = None,
    story_objective: dict | None = None,
):
    return render_slide(
        {
            'slide_type': 'chart',
            'primary_chart': primary_chart,
            'narrative': narrative or {},
            'supporting_charts': supporting_charts or [],
            'text_blocks': text_blocks,
        },
        table=table,
        story_objective=story_objective or (narrative or {}).get('story_objective'),
    )


def build_dimension_story_chart(*args, **kwargs):
    from .analysis_summary import build_dimension_story_chart as legacy_build_dimension_story_chart

    return legacy_build_dimension_story_chart(*args, **kwargs)


def build_treemap_chart(*args, **kwargs):
    from .analysis_summary import build_treemap_chart as legacy_build_treemap_chart

    return legacy_build_treemap_chart(*args, **kwargs)


def build_scatter_chart(*args, **kwargs):
    from .analysis_summary import build_scatter_chart as legacy_build_scatter_chart

    return legacy_build_scatter_chart(*args, **kwargs)


def build_heatmap_chart(*args, **kwargs):
    from .analysis_summary import build_heatmap_chart as legacy_build_heatmap_chart

    return legacy_build_heatmap_chart(*args, **kwargs)


def build_sankey_chart(*args, **kwargs):
    from .analysis_summary import build_sankey_chart as legacy_build_sankey_chart

    return legacy_build_sankey_chart(*args, **kwargs)


def build_geo_map_chart(*args, **kwargs):
    from .analysis_summary import build_geo_map_chart as legacy_build_geo_map_chart

    return legacy_build_geo_map_chart(*args, **kwargs)


def build_radar_chart(*args, **kwargs):
    from .analysis_summary import build_radar_chart as legacy_build_radar_chart

    return legacy_build_radar_chart(*args, **kwargs)


def build_quality_chart(*args, **kwargs):
    from .analysis_summary import build_quality_chart as legacy_build_quality_chart

    return legacy_build_quality_chart(*args, **kwargs)


def build_correlation_chart(*args, **kwargs):
    from .analysis_summary import build_correlation_chart as legacy_build_correlation_chart

    return legacy_build_correlation_chart(*args, **kwargs)


def build_outlier_chart(*args, **kwargs):
    from .analysis_summary import build_outlier_chart as legacy_build_outlier_chart

    return legacy_build_outlier_chart(*args, **kwargs)


def build_column_mix_chart(*args, **kwargs):
    from .analysis_summary import build_column_mix_chart as legacy_build_column_mix_chart

    return legacy_build_column_mix_chart(*args, **kwargs)


def build_structure_chart(*args, **kwargs):
    from .analysis_summary import build_structure_chart as legacy_build_structure_chart

    return legacy_build_structure_chart(*args, **kwargs)


def build_benchmark_chart(*args, **kwargs):
    from .analysis_summary import build_benchmark_chart as legacy_build_benchmark_chart

    return legacy_build_benchmark_chart(*args, **kwargs)


def build_change_contribution_chart(*args, **kwargs):
    from .analysis_summary import build_change_contribution_chart as legacy_build_change_contribution_chart

    return legacy_build_change_contribution_chart(*args, **kwargs)


def build_relationship_sankey_chart(*args, **kwargs):
    from .analysis_summary import build_relationship_sankey_chart as legacy_build_relationship_sankey_chart

    return legacy_build_relationship_sankey_chart(*args, **kwargs)


def build_combo_story_chart(*args, **kwargs):
    from .analysis_summary import build_combo_story_chart as legacy_build_combo_story_chart

    return legacy_build_combo_story_chart(*args, **kwargs)
