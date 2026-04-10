from __future__ import annotations

import json

from .analysis_enrichment import (
    ANALYTICS_USE_LLM_NARRATIVE,
    _llm_json_response,
    _severity_from_ranked_insights,
)
from .insight_engine import build_insight_bundle, build_insight_confidence
from .visual_engine import build_hero_kpi


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


def resolve_story_objective(insight_bundle: dict) -> dict:
    ranked_insights = insight_bundle.get('ranked_insights') or []
    lead_insight = (ranked_insights or [None])[0] or {}
    dominant_signal = insight_bundle.get('dominant_signal') or {}
    lead_type = str(lead_insight.get('type') or dominant_signal.get('type') or 'segment').lower()
    business_impact = insight_bundle.get('business_impact') or {}
    impact_label = str(business_impact.get('impact_label') or '').lower()
    urgency_value = float(lead_insight.get('urgency', 0) or 0)
    score = float(lead_insight.get('score', dominant_signal.get('score') or 0) or 0)

    if urgency_value >= 0.8 or score >= 85:
        urgency_tone = 'high'
    elif urgency_value >= 0.55 or score >= 60:
        urgency_tone = 'medium'
    else:
        urgency_tone = 'low'

    if lead_type in {'diagnostic', 'outlier', 'risk'} or 'riesgo' in impact_label:
        return {
            'objective_type': 'risk_mitigation',
            'framework': 'scqa',
            'urgency_tone': urgency_tone,
            'decision_label': 'Reducir el riesgo prioritario',
            'primary_action_hint': lead_insight.get('action_hint', ''),
        }

    if (
        lead_type in {'segment', 'benchmark'}
        or any(keyword in impact_label for keyword in ['oportunidad', 'uplift', 'ganancia', 'expansion'])
    ):
        return {
            'objective_type': 'opportunity_capture',
            'framework': 'pyramid',
            'urgency_tone': urgency_tone,
            'decision_label': 'Capturar la oportunidad principal',
            'primary_action_hint': lead_insight.get('action_hint', ''),
        }

    return {
        'objective_type': 'performance_review',
        'framework': 'pyramid',
        'urgency_tone': urgency_tone,
        'decision_label': 'Revisar el desempeno principal',
        'primary_action_hint': lead_insight.get('action_hint', ''),
    }


def build_message_hierarchy(insight_bundle: dict, story_objective: dict) -> dict:
    top_insights = (insight_bundle.get('top_insights') or insight_bundle.get('ranked_insights') or [])[:3]
    diagnostic_chain = insight_bundle.get('diagnostic_chain') or {}
    lead_insight = (top_insights or [None])[0] or {}
    main_message = (
        diagnostic_chain.get('root_cause_hypothesis')
        or lead_insight.get('title')
        or (insight_bundle.get('dominant_signal') or {}).get('title')
        or story_objective.get('decision_label')
        or 'La senal principal ya fue priorizada para decision ejecutiva.'
    )

    arguments = []
    for insight in top_insights:
        arguments.append({
            'label': insight.get('title') or insight.get('type') or 'Insight priorizado',
            'evidence': (
                f'Impacto {insight.get("impact", 0):.2f} | '
                f'Confianza {insight.get("confidence", 0):.2f} | '
                f'Urgencia {insight.get("urgency", 0):.2f}'
            ),
            'confidence': round(float(insight.get('confidence', 0) or 0), 2),
        })

    return {
        'main_message': main_message,
        'arguments': arguments,
    }


def build_executive_ask(story_objective: dict, diagnostic_chain: dict | None) -> dict:
    diagnostic_chain = diagnostic_chain or {}
    objective_type = story_objective.get('objective_type')
    primary_driver = diagnostic_chain.get('primary_driver') or {}
    root_cause = diagnostic_chain.get('root_cause_hypothesis') or 'Validar el driver principal identificado.'
    action_hint = story_objective.get('primary_action_hint') or story_objective.get('decision_label') or 'Priorizar la accion principal sugerida.'

    if objective_type == 'risk_mitigation':
        owner = 'Operacion y data owner'
        timeline = '7-14 dias'
    elif objective_type == 'opportunity_capture':
        owner = 'Lider comercial o de crecimiento'
        timeline = '30 dias'
    else:
        owner = 'Lider funcional y BI'
        timeline = '2 semanas'

    success_metric = (
        f'Mover {primary_driver.get("metric", "el KPI principal")} en la direccion esperada '
        f'partiendo por {primary_driver.get("label", "el driver principal")}.'
    )

    return {
        'decision': f'{action_hint} Base diagnostica: {root_cause}',
        'owner': owner,
        'timeline': timeline,
        'success_metric': success_metric,
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
    insight_bundle = build_insight_bundle(table or {}) if table else {}
    story_objective = resolve_story_objective(insight_bundle) if insight_bundle else {}
    message_hierarchy = build_message_hierarchy(insight_bundle, story_objective) if insight_bundle else {}
    executive_ask = build_executive_ask(story_objective, insight_bundle.get('diagnostic_chain')) if insight_bundle else {}
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
        'story_objective': story_objective,
        'message_hierarchy': message_hierarchy,
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
        'story_objective': story_objective,
        'message_hierarchy': message_hierarchy,
        'executive_ask': executive_ask,
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


def build_time_story_slide(*args, **kwargs):
    from .analysis_summary import build_time_story_slide as legacy_build_time_story_slide

    return legacy_build_time_story_slide(*args, **kwargs)


def build_segment_story_slide(*args, **kwargs):
    from .analysis_summary import build_dimension_story_slide as legacy_build_dimension_story_slide

    return legacy_build_dimension_story_slide(*args, **kwargs)


def build_dimension_story_slide(*args, **kwargs):
    return build_segment_story_slide(*args, **kwargs)


def build_benchmark_story_slide(*args, **kwargs):
    from .analysis_summary import build_benchmark_story_slide as legacy_build_benchmark_story_slide

    return legacy_build_benchmark_story_slide(*args, **kwargs)


def build_change_contribution_story_slide(*args, **kwargs):
    from .analysis_summary import (
        build_change_contribution_story_slide as legacy_build_change_contribution_story_slide,
    )

    return legacy_build_change_contribution_story_slide(*args, **kwargs)


def build_relationship_story_slide(*args, **kwargs):
    from .analysis_summary import build_relationship_story_slide as legacy_build_relationship_story_slide

    return legacy_build_relationship_story_slide(*args, **kwargs)


def build_risk_story_slide(*args, **kwargs):
    from .analysis_summary import build_quality_story_slide as legacy_build_quality_story_slide

    return legacy_build_quality_story_slide(*args, **kwargs)


def build_quality_story_slide(*args, **kwargs):
    return build_risk_story_slide(*args, **kwargs)


def build_discovery_story_slide(*args, **kwargs):
    from .analysis_summary import build_discovery_story_slide as legacy_build_discovery_story_slide

    return legacy_build_discovery_story_slide(*args, **kwargs)


def build_table_action_slide(*args, **kwargs):
    from .analysis_summary import build_table_action_slide as legacy_build_table_action_slide

    return legacy_build_table_action_slide(*args, **kwargs)


def build_single_table_insights(*args, **kwargs):
    from .analysis_summary import build_single_table_insights as legacy_build_single_table_insights

    return legacy_build_single_table_insights(*args, **kwargs)


def build_headline_insights(*args, **kwargs):
    from .analysis_summary import build_headline_insights as legacy_build_headline_insights

    return legacy_build_headline_insights(*args, **kwargs)


def build_single_table_presentation_slides(*args, **kwargs):
    from .analysis_summary import (
        build_single_table_presentation_slides as legacy_build_single_table_presentation_slides,
    )

    return legacy_build_single_table_presentation_slides(*args, **kwargs)


def build_slide_index_entries(*args, **kwargs):
    from .analysis_summary import build_slide_index_entries as legacy_build_slide_index_entries

    return legacy_build_slide_index_entries(*args, **kwargs)


def build_workflow_steps(*args, **kwargs):
    from .analysis_summary import build_workflow_steps as legacy_build_workflow_steps

    return legacy_build_workflow_steps(*args, **kwargs)


def prepend_storytelling_slides(*args, **kwargs):
    from .analysis_summary import prepend_storytelling_slides as legacy_prepend_storytelling_slides

    return legacy_prepend_storytelling_slides(*args, **kwargs)


def build_presentation_slides(*args, **kwargs):
    from .analysis_summary import build_presentation_slides as legacy_build_presentation_slides

    return legacy_build_presentation_slides(*args, **kwargs)
