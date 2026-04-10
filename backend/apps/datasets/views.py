from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DatasetImport
from .schema_inference import enqueue_dataset_import
from .serializers import DatasetImportDetailSerializer, DatasetImportSerializer


class DatasetImportListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return DatasetImport.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DatasetImportDetailSerializer
        return DatasetImportSerializer

    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist('files')
        if not files:
            return Response(
                {'files': ['Debes seleccionar al menos un archivo.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            dataset_import = enqueue_dataset_import(
                user=request.user,
                files=files,
                name=request.data.get('name', ''),
            )
        except ValueError as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            return Response(
                {'error': f'No se pudo procesar el dataset: {str(exc)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = DatasetImportDetailSerializer(dataset_import)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


class DatasetImportDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DatasetImportDetailSerializer

    def get_queryset(self):
        return DatasetImport.objects.filter(user=self.request.user).prefetch_related(
            'tables__columns',
            'relationships__source_table',
            'relationships__source_column',
            'relationships__target_table',
            'relationships__target_column',
        )

    def destroy(self, request, *args, **kwargs):
        dataset_import = self.get_object()
        dataset_name = dataset_import.name
        dataset_import.delete()
        return Response(
            {'message': f'El dataset "{dataset_name}" fue eliminado correctamente.'},
            status=status.HTTP_200_OK,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def latest_dataset_import(request):
    dataset_import = DatasetImport.objects.filter(user=request.user).prefetch_related(
        'tables__columns',
        'relationships__source_table',
        'relationships__source_column',
        'relationships__target_table',
        'relationships__target_column',
    ).first()

    if not dataset_import:
        return Response(
            {'error': 'Aun no has cargado ningun dataset.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = DatasetImportDetailSerializer(dataset_import)
    return Response(serializer.data)
