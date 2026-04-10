from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Endpoint público para verificar que la API de Lumiq está activa.
    Usado por Railway en health checks y por el frontend al iniciar.
    """
    return Response({
        'status': 'ok',
        'platform': 'Lumiq API',
        'version': '1.0.0',
        'timestamp': timezone.now().isoformat(),
        'environment': 'development',
    })


@api_view(['GET'])
def protected_ping(request):
    """
    Endpoint protegido — requiere JWT válido.
    Verifica que la autenticación funciona correctamente.
    """
    return Response({
        'message': f'Hola {request.user.username}, tu token es válido ✅',
        'user_id': request.user.id,
        'email': request.user.email,
    })