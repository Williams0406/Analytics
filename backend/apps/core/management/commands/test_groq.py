from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Prueba la conexión con Groq'

    def handle(self, *args, **kwargs):
        self.stdout.write('Probando conexión con Groq...\n')

        # Verificar configuración
        api_key = getattr(settings, 'GROQ_API_KEY', '')
        model = getattr(settings, 'GROQ_MODEL', '')
        provider = getattr(settings, 'AI_PROVIDER', '')

        self.stdout.write(f'AI_PROVIDER: {provider}')
        self.stdout.write(f'GROQ_MODEL: {model}')
        self.stdout.write(f'GROQ_API_KEY: {"✅ configurada" if api_key else "❌ vacía"}')

        if not api_key:
            self.stdout.write(self.style.ERROR('Falta GROQ_API_KEY en las variables de entorno'))
            return

        # Probar llamada real a Groq
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente de análisis de datos."
                    },
                    {
                        "role": "user",
                        "content": "Responde solo con: Groq funcionando correctamente en Lumiq."
                    }
                ],
                max_tokens=50,
            )
            respuesta = response.choices[0].message.content
            self.stdout.write(self.style.SUCCESS(f'Respuesta: {respuesta}'))
            self.stdout.write(self.style.SUCCESS('✅ Groq está funcionando correctamente'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))