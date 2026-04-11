import json
from unittest.mock import patch

from django.test import SimpleTestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.datasets.schema_inference import import_dataset_bundle
from apps.users.models import LumiqUser

from .ai_service import get_ai_provider_and_model
from .models import AIInsight
from .views import (
    build_ai_presentation_prompt,
    build_ai_prompt,
    build_dataset_context,
    dedupe_slides,
)


class SingleDatasetInsightsContextTests(TestCase):
    def setUp(self):
        self.user = LumiqUser.objects.create_user(
            username='insights-dataset-user',
            email='insights-dataset@example.com',
            password='Str0ngPass!123',
            first_name='Ines',
            last_name='Insights',
        )

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

        import_dataset_bundle(user=self.user, files=[sales], name='Ventas insights')

    def test_prompt_includes_specific_single_dataset_context(self):
        context = build_dataset_context(self.user, 'Que pasa con discount y revenue?')
        prompt = build_ai_prompt(context, 'Que pasa con discount y revenue?')

        self.assertTrue(context['single_table_mode'])
        self.assertIn('revenue', prompt)
        self.assertIn('discount', prompt)
        self.assertIn('Riesgos de calidad', prompt)
        self.assertIn('Campos a priorizar', prompt)


class AIServiceConfigTests(SimpleTestCase):
    @override_settings(AI_PROVIDER='groq', GROQ_MODEL='llama-3.3-70b-versatile')
    def test_groq_provider_uses_groq_model_setting(self):
        provider, model = get_ai_provider_and_model()

        self.assertEqual(provider, 'groq')
        self.assertEqual(model, 'llama-3.3-70b-versatile')


class AIPresentationCompositionTests(SimpleTestCase):
    def test_dedupe_slides_removes_repeated_chart_signatures(self):
        repeated_map = {
            'chart_type': 'map',
            'value_label': 'revenue',
            'data': [
                {'label': 'Lima', 'value': 1200, 'x': 26, 'y': 31},
                {'label': 'Bogota', 'value': 980, 'x': 30, 'y': 24},
                {'label': 'CDMX', 'value': 1500, 'x': 18, 'y': 19},
            ],
        }

        deduped = dedupe_slides([
            {'type': 'chart', 'title': 'Mapa base', **repeated_map},
            {'type': 'chart', 'title': 'Mapa repetido con otro titular', **repeated_map},
        ])

        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0]['type'], 'chart')

    def test_presentation_prompt_requests_compact_copy_for_visual_slides(self):
        prompt = build_ai_presentation_prompt(
            {
                'mode': 'metrics',
                'company': 'Acme',
                'metrics': {},
                'recent_revenue': [],
            },
            'Que debo mirar primero?',
        )

        self.assertIn('maximo 90 palabras', prompt)
        self.assertIn('deja aire visual', prompt)


class AIInsightPresentationEndpointTests(APITestCase):
    def setUp(self):
        self.user = LumiqUser.objects.create_user(
            username='insights-api-user',
            email='insights-api@example.com',
            password='Str0ngPass!123',
            first_name='Ivo',
            last_name='Slides',
        )
        self.client.force_authenticate(self.user)

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

        import_dataset_bundle(user=self.user, files=[sales], name='Ventas slides')

    @patch('apps.insights.views.get_ai_response')
    def test_generate_insight_returns_presentation_and_serialized_context(self, mock_get_ai_response):
        mock_get_ai_response.return_value = json.dumps({
            'title': 'Respuesta sobre revenue',
            'summary_markdown': '## Resumen\n- `revenue` crece en el periodo observado.',
            'slides': [
                {
                    'type': 'hero',
                    'title': 'Revenue en crecimiento',
                    'subtitle': 'Lectura principal del dataset',
                    'question': 'Que esta pasando con `revenue`?',
                    'bullets': [
                        '`revenue` mantiene una trayectoria ascendente.',
                        'La columna `discount` merece validacion adicional.',
                    ],
                    'accent_value': '2',
                    'accent_label': 'hallazgos',
                    'finding': 'El crecimiento es visible en la serie.',
                    'conclusion': 'La tendencia es positiva.',
                    'recommendation': 'Conviene revisar el impacto de `discount`.',
                },
                {
                    'type': 'rich_text',
                    'title': 'Formula',
                    'subtitle': 'Notacion matematica',
                    'body': 'La variacion puede expresarse como \\(\\Delta revenue = revenue_t - revenue_0\\).',
                    'callouts': [
                        {'label': 'Modo', 'value': 'dataset'},
                    ],
                },
            ],
        })

        response = self.client.post(
            '/api/insights/generate/',
            {'question': 'Que esta pasando con revenue?'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        presentation = response.data['insight']['presentation']
        self.assertEqual(presentation['title'], 'Respuesta sobre revenue')
        self.assertGreaterEqual(len(presentation['slides']), 3)
        self.assertEqual(presentation['slides'][0]['type'], 'hero')
        self.assertTrue(any(slide['type'] == 'chart' for slide in presentation['slides']))
        self.assertEqual(presentation['slides'][-1]['type'], 'rich_text')

        stored = self.user.insights.first()
        self.assertIn('analysis_context', stored.metrics_context)
        self.assertIn('presentation', stored.metrics_context)
        self.assertIsInstance(stored.metrics_context['analysis_context'].get('dataset_import'), dict)

    def test_delete_single_insight_endpoint(self):
        insight = AIInsight.objects.create(
            user=self.user,
            insight_type='summary',
            priority='medium',
            title='Insight temporal',
            content='Contenido a eliminar',
            metrics_context={'presentation': {'slides': []}},
        )

        response = self.client.delete(f'/api/insights/{insight.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(AIInsight.objects.filter(pk=insight.pk).exists())

    def test_clear_history_endpoint(self):
        AIInsight.objects.create(
            user=self.user,
            insight_type='summary',
            priority='medium',
            title='Insight 1',
            content='Contenido 1',
            metrics_context={'presentation': {'slides': []}},
        )
        AIInsight.objects.create(
            user=self.user,
            insight_type='summary',
            priority='medium',
            title='Insight 2',
            content='Contenido 2',
            metrics_context={'presentation': {'slides': []}},
        )

        response = self.client.delete('/api/insights/clear/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AIInsight.objects.filter(user=self.user).count(), 0)
