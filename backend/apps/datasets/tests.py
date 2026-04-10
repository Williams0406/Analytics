import warnings
import time
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.utils import OperationalError
import pandas as pd
from rest_framework import status
from rest_framework.test import APITransactionTestCase

from apps.datasets.analysis_enrichment import build_business_context, choose_best_chart
from apps.datasets.analysis_summary import (
    _decorate_supporting_chart,
    _resolve_signal_color,
    build_numeric_summaries,
    build_table_analysis,
    build_text_blocks_for_slide,
    build_time_story_slide,
    compact_table_record,
)
from apps.datasets.insight_engine import build_insight_bundle
from apps.datasets import schema_inference
from apps.datasets.schema_inference import infer_series_type
from apps.datasets.models import DatasetImport
from apps.datasets.story_engine import (
    build_executive_ask,
    build_message_hierarchy,
    resolve_story_objective,
)
from apps.users.models import LumiqUser
from apps.datasets.visual_engine import render_slide, resolve_layout


class DatasetImportTests(APITransactionTestCase):
    def setUp(self):
        self.user = LumiqUser.objects.create_user(
            username='schema-user',
            email='schema@example.com',
            password='Str0ngPass!123',
            first_name='Schema',
            last_name='Tester',
        )
        self.client.force_authenticate(self.user)

    def wait_for_import(self, dataset_id: int, timeout: float = 10.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                dataset_import = DatasetImport.objects.get(pk=dataset_id)
            except OperationalError:
                time.sleep(0.05)
                continue
            if dataset_import.status in {'ready', 'failed'}:
                return dataset_import
            time.sleep(0.05)
        self.fail(f'El import {dataset_id} no termino dentro del timeout')

    def test_import_bundle_infers_schema_and_relationships(self):
        customers = SimpleUploadedFile(
            'customers.csv',
            (
                b'id,name,email\n'
                b'1,Ana,ana@example.com\n'
                b'2,Luis,luis@example.com\n'
            ),
            content_type='text/csv',
        )
        orders = SimpleUploadedFile(
            'orders.csv',
            (
                b'id,customer_id,total\n'
                b'10,1,120.50\n'
                b'11,2,98.20\n'
            ),
            content_type='text/csv',
        )

        response = self.client.post(
            '/api/datasets/imports/',
            {'name': 'Prueba de schema', 'files': [customers, orders]},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['status'], 'processing')

        dataset_import = self.wait_for_import(response.data['id'])
        self.assertEqual(dataset_import.status, 'ready')

        detail_response = self.client.get(f'/api/datasets/imports/{dataset_import.id}/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['tables_count'], 2)
        self.assertEqual(len(detail_response.data['tables']), 2)
        self.assertEqual(len(detail_response.data['relationships']), 1)
        self.assertIn('analysis_summary', detail_response.data)
        self.assertEqual(detail_response.data['analysis_summary']['overview']['tables_count'], 2)
        self.assertEqual(detail_response.data['analysis_summary']['dashboard']['kpis'][0]['metric_type'], 'tables')
        story_slides = detail_response.data['analysis_summary']['presentation']['slides']
        first_chart_slide = next(slide for slide in story_slides if slide.get('type') == 'chart')
        self.assertIn('question', first_chart_slide)
        self.assertIn('finding', first_chart_slide)
        self.assertIn('recommendation', first_chart_slide)
        relationship = detail_response.data['relationships'][0]
        self.assertEqual(relationship['source_table_name'], 'orders')
        self.assertEqual(relationship['source_column_name'], 'customer_id')
        self.assertEqual(relationship['target_table_name'], 'customers')
        self.assertEqual(relationship['target_column_name'], 'id')

    def test_import_bundle_detects_implicit_relationship_without_id_suffix(self):
        customers = SimpleUploadedFile(
            'customers.csv',
            (
                b'id,name\n'
                b'1,Ana\n'
                b'2,Luis\n'
                b'3,Maria\n'
            ),
            content_type='text/csv',
        )
        orders = SimpleUploadedFile(
            'orders.csv',
            (
                b'id,customer,total\n'
                b'10,1,120.50\n'
                b'11,2,98.20\n'
                b'12,1,75.00\n'
                b'13,3,150.00\n'
            ),
            content_type='text/csv',
        )

        response = self.client.post(
            '/api/datasets/imports/',
            {'name': 'FK implicita', 'files': [customers, orders]},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        dataset_import = self.wait_for_import(response.data['id'])
        self.assertEqual(dataset_import.status, 'ready')

        detail_response = self.client.get(f'/api/datasets/imports/{dataset_import.id}/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(detail_response.data['relationships']), 1)
        relationship = detail_response.data['relationships'][0]
        self.assertEqual(relationship['source_table_name'], 'orders')
        self.assertEqual(relationship['source_column_name'], 'customer')
        self.assertEqual(relationship['target_table_name'], 'customers')
        self.assertEqual(relationship['target_column_name'], 'id')

    def test_upload_rejects_file_over_size_limit(self):
        oversized = SimpleUploadedFile(
            'oversized.csv',
            b'id,value\n1,1234567890\n',
            content_type='text/csv',
        )

        with patch.object(schema_inference, 'MAX_FILE_SIZE_BYTES', 10):
            response = self.client.post(
                '/api/datasets/imports/',
                {'name': 'Demasiado grande', 'files': [oversized]},
                format='multipart',
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('excede el limite', response.data['error'])

    def test_single_file_import_builds_specific_analysis_summary(self):
        sales = SimpleUploadedFile(
            'sales_dataset.csv',
            (
                b'order_id,order_date,region,revenue,discount\n'
                b'1,2025-01-01,Norte,1200,10\n'
                b'2,2025-02-01,Sur,1450,\n'
                b'3,2025-03-01,Norte,1325,\n'
                b'4,2025-04-01,Centro,1710,25\n'
            ),
            content_type='text/csv',
        )

        response = self.client.post(
            '/api/datasets/imports/',
            {'name': 'Ventas especificas', 'files': [sales]},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['status'], 'processing')

        dataset_import = self.wait_for_import(response.data['id'])
        self.assertEqual(dataset_import.status, 'ready')

        detail_response = self.client.get(f'/api/datasets/imports/{dataset_import.id}/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['tables_count'], 1)
        summary = detail_response.data['analysis_summary']
        dashboard = summary['dashboard']
        table = summary['tables'][0]

        self.assertEqual(dashboard['primary_chart']['title'], 'revenue a lo largo del tiempo')
        self.assertEqual(dashboard['secondary_chart']['title'], 'Distribucion de region')
        self.assertIn('finanzas', summary['overview']['business_context'])
        self.assertEqual(table['quality_watchlist'][0]['column'], 'discount')
        self.assertTrue(any(item['role'] == 'Medida central' for item in table['field_highlights']))
        self.assertTrue(table['time_series']['forecast_points'])
        self.assertTrue(table['segment_benchmarks'])
        self.assertTrue(table['change_contribution'])
        self.assertIn('diagnostic_chain', table)
        self.assertIn('business_impact', table)
        self.assertTrue(table['ranked_insights'])
        self.assertIn('diagnostic', table['insight_confidence'])
        self.assertEqual(table['hero_kpi']['label'], 'Cambio en revenue')
        self.assertGreaterEqual(len(summary['presentation']['slides']), 4)
        self.assertEqual(summary['presentation']['slides'][0]['type'], 'index')
        self.assertEqual(summary['presentation']['slides'][1]['type'], 'workflow')
        chart_slides = [slide for slide in summary['presentation']['slides'] if slide.get('type') == 'chart']
        self.assertTrue(any(slide.get('chart_type') == 'combo' for slide in chart_slides))
        self.assertTrue(any(slide.get('chart_type') in {'bullet', 'waterfall'} for slide in chart_slides))
        self.assertTrue(all(slide.get('question') for slide in chart_slides))
        self.assertTrue(all(slide.get('finding') for slide in chart_slides))
        self.assertTrue(all(slide.get('conclusion') for slide in chart_slides))
        self.assertTrue(all(slide.get('recommendation') for slide in chart_slides))
        self.assertTrue(all(slide.get('confidence') for slide in chart_slides))
        self.assertTrue(all(slide.get('severity') for slide in chart_slides))
        self.assertTrue(all(slide.get('charts') for slide in chart_slides))
        self.assertTrue(all('layout' in slide for slide in chart_slides))
        self.assertTrue(any(len(slide.get('charts', [])) > 1 for slide in chart_slides))
        self.assertTrue(any(slide.get('text_blocks') for slide in chart_slides))

    def test_import_can_be_deleted(self):
        sales = SimpleUploadedFile(
            'sales_dataset.csv',
            (
                b'order_id,order_date,region,revenue\n'
                b'1,2025-01-01,Norte,1200\n'
                b'2,2025-02-01,Sur,1450\n'
            ),
            content_type='text/csv',
        )

        create_response = self.client.post(
            '/api/datasets/imports/',
            {'name': 'Dataset para borrar', 'files': [sales]},
            format='multipart',
        )

        self.assertEqual(create_response.status_code, status.HTTP_202_ACCEPTED)
        dataset_id = create_response.data['id']
        self.assertEqual(self.wait_for_import(dataset_id).status, 'ready')

        delete_response = self.client.delete(f'/api/datasets/imports/{dataset_id}/')

        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        self.assertIn('fue eliminado correctamente', delete_response.data['message'])
        self.assertFalse(DatasetImport.objects.filter(pk=dataset_id).exists())

    def test_universal_profile_detects_correlations_outliers_and_text(self):
        notebook_style_dataset = SimpleUploadedFile(
            'notebook_style_dataset.csv',
            (
                b'recorded_at,segment,revenue,profit,marketing_spend,notes\n'
                b'2025-01-01,SMB,100,20,60,Cliente pequeno con renovacion manual y feedback positivo\n'
                b'2025-02-01,SMB,200,40,120,Cliente pequeno con tickets de soporte frecuentes y observacion larga\n'
                b'2025-03-01,Mid,300,60,180,Segmento medio con contrato trimestral y comentarios operativos extensos\n'
                b'2025-04-01,Mid,400,80,240,Cuenta mediana con expansion comercial y descripcion larga del caso\n'
                b'2025-05-01,Enterprise,500,100,300,Cuenta enterprise con multiples stakeholders y notas detalladas\n'
                b'2025-06-01,Enterprise,600,120,360,Cuenta enterprise con renovacion prioritaria y seguimiento especial\n'
                b'2025-07-01,SMB,700,140,420,Cliente pequeno con onboarding extendido y narrativa descriptiva\n'
                b'2025-08-01,Mid,800,160,480,Segmento medio con cambio de plan y comentarios adicionales amplios\n'
                b'2025-09-01,Enterprise,900,180,540,Cuenta enterprise con despliegue regional y texto cualitativo rico\n'
                b'2025-10-01,Enterprise,5000,1000,3000,Caso extremo con pico anomalo de revenue y reporte muy detallado\n'
            ),
            content_type='text/csv',
        )

        response = self.client.post(
            '/api/datasets/imports/',
            {'name': 'Notebook style dataset', 'files': [notebook_style_dataset]},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        dataset_import = self.wait_for_import(response.data['id'])
        self.assertEqual(dataset_import.status, 'ready')

        detail_response = self.client.get(f'/api/datasets/imports/{dataset_import.id}/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        summary = detail_response.data['analysis_summary']
        table = summary['tables'][0]

        self.assertIn('correlation', table['analysis_modes'])
        self.assertIn('outliers', table['analysis_modes'])
        self.assertIn('text', table['analysis_modes'])
        self.assertTrue(any(
            {pair['left_column'], pair['right_column']} == {'revenue', 'profit'}
            for pair in table['correlation_pairs']
        ))
        self.assertEqual(table['outlier_watchlist'][0]['column'], 'revenue')
        self.assertEqual(table['text_watchlist'][0]['column'], 'notes')
        self.assertTrue(table['segment_clusters'])
        self.assertEqual(table['segment_clusters']['k'], 3)
        self.assertTrue(table['insight_confidence']['correlation']['score'] > 0)

    def test_infer_series_type_silences_per_value_datetime_warning(self):
        series = pd.Series([
            '2025-01-01',
            '2025/02/01',
            '2025-03-01T08:30:00',
            '2025-04-01 10:45:00',
        ])

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always')
            inferred_type = infer_series_type(series)

        self.assertEqual(inferred_type, 'datetime')
        self.assertFalse(any('Could not infer format' in str(item.message) for item in captured))

    def test_business_context_and_chart_selector(self):
        frame = pd.DataFrame(columns=['order_date', 'revenue', 'profit', 'region'])
        self.assertIn('finanzas', build_business_context(frame, frame.columns.tolist()))
        self.assertEqual(
            choose_best_chart('trend', {'is_temporal': True, 'n_categories': 12, 'n_points': 12, 'n_series': 1}),
            'combo',
        )
        self.assertEqual(
            choose_best_chart('deviation', {'is_temporal': False, 'n_categories': 4, 'n_points': 4, 'n_series': 1}),
            'bullet',
        )

    def test_numeric_summary_includes_dispersion_metrics(self):
        frame = pd.DataFrame({
            'revenue': [100, 120, 140, 160, 180],
        })

        summaries = build_numeric_summaries(frame, ['revenue'])

        self.assertEqual(len(summaries), 1)
        summary = summaries[0]
        self.assertIn('std', summary)
        self.assertIn('p25', summary)
        self.assertIn('median', summary)
        self.assertIn('p75', summary)
        self.assertGreater(summary['std'], 0)

    def test_story_helpers_keep_action_and_respect_lower_is_better_metrics(self):
        self.assertEqual(_resolve_signal_color('+8%', 'Benchmarking', 'churn_rate'), 'negative')
        self.assertEqual(_resolve_signal_color('-8%', 'Benchmarking', 'churn_rate'), 'positive')

        blocks = build_text_blocks_for_slide(
            {
                'stage': 'Benchmarking',
                'finding': 'Hallazgo principal',
                'conclusion': 'Conclusion ejecutiva',
                'action': 'Siguiente paso concreto',
                'signal_value': '+8%',
                'signal_label': 'churn_rate',
            },
            {'focus_measure_column': 'churn_rate', 'hero_kpi': {}},
            {'chart_type': 'bar'},
            [],
        )

        self.assertTrue(any(block['role'] == 'conclusion' for block in blocks))
        self.assertTrue(any(block['role'] == 'action' for block in blocks))

    def test_supporting_chart_decorator_adds_annotations_and_reference_lines(self):
        chart = _decorate_supporting_chart(
            {
                'chart_type': 'line',
                'data': [
                    {'label': 'Jan', 'value': 100},
                    {'label': 'Feb', 'value': 120},
                    {'label': 'Mar', 'value': 140},
                ],
            },
            metric_context='revenue',
            business_context='dataset de finanzas',
        )

        self.assertTrue(chart['annotations'])
        self.assertTrue(chart['reference_lines'])

    def test_table_analysis_builds_and_serializes_diagnostic_chain(self):
        frame = pd.DataFrame({
            'recorded_at': [
                '2025-01-01', '2025-01-01',
                '2025-02-01', '2025-02-01',
                '2025-03-01', '2025-03-01',
                '2025-04-01', '2025-04-01',
                '2025-05-01', '2025-05-01',
                '2025-06-01', '2025-06-01',
            ],
            'region': [
                'Sur', 'Norte',
                'Sur', 'Norte',
                'Sur', 'Norte',
                'Sur', 'Norte',
                'Sur', 'Norte',
                'Sur', 'Norte',
            ],
            'revenue': [220, 210, 205, 215, 195, 220, 175, 225, 120, 230, 60, 235],
            'idle_time': [12, 3, 14, 4, 18, 4, 21, 5, 36, 5, 58, 4],
        })
        profile = {
            'name': 'fleet_ops',
            'dataframe': frame,
            'columns': [
                {'name': 'recorded_at', 'inferred_type': 'datetime'},
                {'name': 'region', 'inferred_type': 'string'},
                {'name': 'revenue', 'inferred_type': 'integer'},
                {'name': 'idle_time', 'inferred_type': 'integer'},
            ],
            'primary_key_name': '',
        }

        table = build_table_analysis(profile, 'dataset de operaciones')
        compact = compact_table_record(table)

        self.assertEqual(table['diagnostic_chain']['issue'], 'revenue_drop')
        self.assertEqual(table['diagnostic_chain']['primary_driver']['label'], 'Sur')
        self.assertGreaterEqual(len(table['diagnostic_chain']['evidence_chain']), 2)
        self.assertTrue(table['business_impact'])
        self.assertTrue(table['ranked_insights'])
        self.assertEqual(table['ranked_insights'][0]['rank'], 1)
        self.assertIn('diagnostic', table['insight_confidence'])
        self.assertIn(table['insight_confidence']['diagnostic']['level'], {'alta', 'media', 'baja'})
        self.assertEqual(compact['diagnostic_chain']['primary_driver']['label'], 'Sur')
        self.assertTrue(compact['ranked_insights'])
        self.assertEqual(compact['insight_bundle']['primary_insight']['rank'], 1)

    def test_engine_contract_layers_can_consume_insight_bundle(self):
        table = {
            'name': 'ops',
            'business_context': 'dataset de operaciones',
            'focus_measure_column': 'utilization',
            'trend_summary': {'change_percent': -17.0, 'change_value': -42.0},
            'diagnostic_chain': {
                'primary_driver': {'label': 'Sur', 'metric': 'utilization'},
                'root_cause_hypothesis': 'La caida se concentra en Sur y coincide con mayor idle time.',
            },
            'business_impact': {
                'impact_value': 41990,
                'impact_unit': 'USD',
                'impact_label': 'riesgo de ingreso mensual',
            },
            'ranked_insights': [
                {
                    'rank': 1,
                    'type': 'diagnostic',
                    'title': 'La caida de utilizacion se concentra en Sur.',
                    'score': 92,
                    'impact': 0.9,
                    'confidence': 0.88,
                    'urgency': 0.84,
                    'action_hint': 'Revisar disponibilidad de flota en la region Sur.',
                },
                {
                    'rank': 2,
                    'type': 'correlation',
                    'title': 'Idle time se correlaciona con menor utilizacion.',
                    'score': 78,
                    'impact': 0.6,
                    'confidence': 0.81,
                    'urgency': 0.65,
                    'action_hint': 'Monitorear idle time por equipo.',
                },
            ],
            'insight_confidence': {
                'diagnostic': {'score': 88, 'level': 'alta', 'caveat': 'Cadena consistente.'},
            },
        }

        bundle = build_insight_bundle(table)
        objective = resolve_story_objective(bundle)
        hierarchy = build_message_hierarchy(bundle, objective)
        executive_ask = build_executive_ask(objective, bundle['diagnostic_chain'])

        self.assertEqual(bundle['dominant_signal']['type'], 'diagnostic')
        self.assertEqual(objective['objective_type'], 'risk_mitigation')
        self.assertTrue(hierarchy['main_message'])
        self.assertGreaterEqual(len(hierarchy['arguments']), 1)
        self.assertIn('Sur', executive_ask['success_metric'])
        layout = resolve_layout('hero', objective)
        self.assertEqual(layout['template_name'], 'situation_full')
        self.assertIn('zones', layout)

    def test_render_slide_builds_full_visual_contract(self):
        slide = render_slide(
            {
                'slide_type': 'chart',
                'primary_chart': {
                    'chart_type': 'line',
                    'title': 'Revenue trimestral',
                    'subtitle': 'Tendencia reciente',
                    'data': [
                        {'label': 'Q1', 'value': 100},
                        {'label': 'Q2', 'value': 115},
                        {'label': 'Q3', 'value': 132},
                        {'label': 'Q4', 'value': 128},
                    ],
                    'value_label': 'revenue',
                },
                'narrative': {
                    'stage': 'Exploracion Temporal',
                    'question': 'Como cambia revenue a lo largo del tiempo?',
                    'finding': 'Revenue acelera durante el tercer trimestre.',
                    'conclusion': 'La tendencia sigue positiva pero con desaceleracion al cierre.',
                    'recommendation': 'Monitorea la inflexion de Q4 antes de replanificar.',
                    'signal_value': '+28.0%',
                    'signal_label': 'variacion acumulada',
                    'insight_type': 'trend',
                },
            },
            table={
                'focus_measure_column': 'revenue',
                'business_context': 'finanzas',
                'hero_kpi': {
                    'value': '+28.0%',
                    'label': 'Cambio en revenue',
                    'comparison': 'vs Q1',
                    'color_signal': 'positive',
                },
            },
            story_objective={
                'objective_type': 'performance_review',
                'urgency_tone': 'high',
            },
        )

        self.assertEqual(slide['visual_intent'], 'hero_trend_story')
        self.assertEqual(slide['layout']['template_name'], 'hero_split')
        self.assertEqual(slide['template']['template_name'], 'HeroSlide')
        self.assertEqual(slide['motion']['entrance'], 'line_draw')
        self.assertIn('chart_palette', slide['design_tokens'])
        self.assertTrue(slide['primitives']['headline']['title'])

    def test_table_analysis_fallback_context_builds_richer_time_story(self):
        frame = pd.DataFrame({
            'order_date': pd.date_range('2025-01-01', periods=12, freq='MS'),
            'region': ['Norte'] * 6 + ['Sur'] * 6,
            'revenue': [120, 180, 240, 150, 260, 320, 90, 110, 80, 70, 60, 50],
            'discount': [5, 8, None, 7, None, 6, 5, None, 4, 4, None, 3],
        })
        profile = {
            'name': 'sales',
            'dataframe': frame,
            'columns': [
                {'name': 'order_date', 'inferred_type': 'datetime'},
                {'name': 'region', 'inferred_type': 'string'},
                {'name': 'revenue', 'inferred_type': 'decimal'},
                {'name': 'discount', 'inferred_type': 'decimal'},
            ],
        }

        table = build_table_analysis(profile)
        slide = build_time_story_slide(table)

        self.assertIn('finanzas', table['business_context'])
        self.assertIn('seasonality', table['analysis_modes'])
        self.assertIsNotNone(slide)
        self.assertIn('patron estacional', slide['finding'])
        self.assertIn('principal responsable', slide['conclusion'])
