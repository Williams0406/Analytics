from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.datasets.schema_inference import import_dataset_bundle
from apps.users.models import LumiqUser

from .views import build_ai_prompt, build_dataset_context


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
