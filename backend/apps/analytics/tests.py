from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from apps.datasets.schema_inference import import_dataset_bundle
from apps.users.models import LumiqUser


class DatasetAnalyticsTests(APITestCase):
    def setUp(self):
        self.user = LumiqUser.objects.create_user(
            username='analytics-user',
            email='analytics@example.com',
            password='Str0ngPass!123',
            first_name='Ana',
            last_name='Analitica',
        )
        self.client.force_authenticate(self.user)

        customers = SimpleUploadedFile(
            'customers.csv',
            (
                b'id,segment\n'
                b'1,Enterprise\n'
                b'2,SMB\n'
            ),
            content_type='text/csv',
        )
        orders = SimpleUploadedFile(
            'orders.csv',
            (
                b'id,customer_id,created_at,total\n'
                b'10,1,2025-01-01,120.50\n'
                b'11,2,2025-02-01,98.20\n'
            ),
            content_type='text/csv',
        )

        import_dataset_bundle(user=self.user, files=[customers, orders], name='Ventas demo')

    def test_dashboard_endpoint_uses_latest_dataset_summary(self):
        response = self.client.get('/api/analytics/dashboard/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['source'], 'dataset')
        self.assertEqual(response.data['dataset_import']['name'], 'Ventas demo')
        self.assertGreaterEqual(len(response.data['kpis']), 4)
        self.assertEqual(response.data['primary_chart']['title'], 'Volumen por tabla')

    def test_presentation_endpoint_returns_slide_deck(self):
        response = self.client.get('/api/analytics/presentation/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['source'], 'dataset')
        self.assertGreaterEqual(len(response.data['slides']), 4)
        self.assertEqual(response.data['slides'][0]['type'], 'index')
        self.assertEqual(response.data['slides'][1]['type'], 'workflow')
        self.assertEqual(response.data['slides'][2]['type'], 'hero')


class SingleDatasetAnalyticsTests(APITestCase):
    def setUp(self):
        self.user = LumiqUser.objects.create_user(
            username='single-dataset-user',
            email='single-dataset@example.com',
            password='Str0ngPass!123',
            first_name='Sofia',
            last_name='Dataset',
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

        import_dataset_bundle(user=self.user, files=[sales], name='Ventas unitarias')

    def test_dashboard_endpoint_prioritizes_single_dataset_analysis(self):
        response = self.client.get('/api/analytics/dashboard/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['source'], 'dataset')
        self.assertEqual(response.data['dataset_import']['name'], 'Ventas unitarias')
        self.assertEqual(response.data['primary_chart']['title'], 'revenue a lo largo del tiempo')
        self.assertEqual(response.data['secondary_chart']['title'], 'Distribucion de region')
        self.assertNotEqual(response.data['primary_chart']['title'], 'Volumen por tabla')
        self.assertEqual(response.data['table_spotlights'][0]['quality_watchlist'][0]['column'], 'discount')
        self.assertTrue(response.data['table_spotlights'][0]['ranked_insights'])
        self.assertTrue(response.data['table_spotlights'][0]['insight_bundle'])

    def test_presentation_endpoint_uses_single_dataset_storyline(self):
        response = self.client.get('/api/analytics/presentation/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['source'], 'dataset')
        titles = [slide.get('title') for slide in response.data['slides']]
        self.assertEqual(titles[0], 'Indice del analisis')
        self.assertEqual(titles[1], 'Proceso seguido para construir este analisis')
        self.assertNotIn('Donde vive el volumen', titles)
        self.assertIn('Benchmark interno por segmento', titles)
        self.assertIn('Campos y acciones a priorizar', titles)
        chart_slides = [slide for slide in response.data['slides'] if slide.get('type') == 'chart']
        self.assertTrue(any(len(slide.get('charts', [])) > 1 for slide in chart_slides))
        self.assertTrue(all(isinstance(slide.get('text_blocks', []), list) for slide in chart_slides))
        self.assertTrue(all(slide.get('severity') for slide in chart_slides))

    def test_presentation_endpoint_exposes_dataset_context(self):
        response = self.client.get('/api/analytics/presentation/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('dataset_context', response.data)
        self.assertEqual(response.data['dataset_context']['tables'][0]['name'], 'sales_dataset')
        self.assertTrue(any(field['name'] == 'revenue' for field in response.data['dataset_context']['tables'][0]['fields']))


class UniversalDatasetAnalyticsTests(APITestCase):
    def setUp(self):
        self.user = LumiqUser.objects.create_user(
            username='universal-dataset-user',
            email='universal-dataset@example.com',
            password='Str0ngPass!123',
            first_name='Una',
            last_name='Dataset',
        )
        self.client.force_authenticate(self.user)

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

        import_dataset_bundle(user=self.user, files=[notebook_style_dataset], name='Universal analytics')

    def test_dashboard_endpoint_exposes_universal_analysis_lenses(self):
        response = self.client.get('/api/analytics/dashboard/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('correlation', response.data['overview']['available_lenses'])
        self.assertIn('outliers', response.data['overview']['available_lenses'])
        self.assertIn('text', response.data['overview']['available_lenses'])

    def test_presentation_endpoint_adds_notebook_style_slides(self):
        response = self.client.get('/api/analytics/presentation/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [slide.get('title') for slide in response.data['slides']]
        self.assertEqual(titles[0], 'Indice del analisis')
        self.assertTrue(
            'Correlaciones mas fuertes' in titles
            or 'Mapa de calor de correlaciones' in titles
            or 'Relacion entre revenue y profit' in titles
        )
        self.assertIn('Columnas con mas outliers', titles)


class AdvancedVisualizationAnalyticsTests(APITestCase):
    def setUp(self):
        self.user = LumiqUser.objects.create_user(
            username='advanced-viz-user',
            email='advanced-viz@example.com',
            password='Str0ngPass!123',
            first_name='Vera',
            last_name='Viz',
        )
        self.client.force_authenticate(self.user)

        geo_dataset = SimpleUploadedFile(
            'global_pipeline.csv',
            (
                b'recorded_at,country,segment,channel,revenue,profit,marketing_spend\n'
                b'2025-01-01,Peru,SMB,Direct,120,24,60\n'
                b'2025-02-01,Peru,Mid,Partner,150,31,70\n'
                b'2025-03-01,Chile,SMB,Partner,180,36,80\n'
                b'2025-04-01,Chile,Enterprise,Direct,260,52,120\n'
                b'2025-05-01,Mexico,Mid,Online,310,64,150\n'
                b'2025-06-01,Mexico,Enterprise,Partner,360,74,175\n'
                b'2025-07-01,USA,SMB,Online,420,86,210\n'
                b'2025-08-01,USA,Enterprise,Direct,470,96,230\n'
                b'2025-09-01,Spain,Mid,Partner,520,108,255\n'
                b'2025-10-01,Spain,Enterprise,Online,610,124,300\n'
            ),
            content_type='text/csv',
        )

        import_dataset_bundle(user=self.user, files=[geo_dataset], name='Advanced viz dataset')

    def test_presentation_endpoint_generates_advanced_visualizations_when_needed(self):
        response = self.client.get('/api/analytics/presentation/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        chart_types = []
        chart_slides = [slide for slide in response.data['slides'] if slide.get('type') == 'chart']
        for slide in chart_slides:
            chart_types.extend(
                chart.get('chart_type')
                for chart in (slide.get('charts') or [slide])
            )
        self.assertTrue(any(len(slide.get('charts', [])) > 1 for slide in chart_slides))
        self.assertIn('combo', chart_types)
        self.assertIn('line', chart_types)
        self.assertIn('map', chart_types)
        self.assertIn('scatter', chart_types)
        self.assertIn('heatmap', chart_types)
