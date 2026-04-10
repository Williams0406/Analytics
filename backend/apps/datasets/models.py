from django.conf import settings
from django.db import models


class DatasetImport(models.Model):
    STATUS_CHOICES = [
        ('processing', 'Procesando'),
        ('ready', 'Listo'),
        ('failed', 'Fallido'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dataset_imports',
    )
    name = models.CharField(max_length=150)
    source_type = models.CharField(max_length=30, default='file_bundle')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    file_count = models.PositiveIntegerField(default=0)
    tables_count = models.PositiveIntegerField(default=0)
    relationships_count = models.PositiveIntegerField(default=0)
    files_meta = models.JSONField(default=list, blank=True)
    analysis_summary = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Importacion de Dataset'
        verbose_name_plural = 'Importaciones de Dataset'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} | {self.name} | {self.status}'


class DatasetTable(models.Model):
    dataset_import = models.ForeignKey(
        DatasetImport,
        on_delete=models.CASCADE,
        related_name='tables',
    )
    name = models.CharField(max_length=150)
    source_file = models.CharField(max_length=255, blank=True)
    row_count = models.PositiveIntegerField(default=0)
    column_count = models.PositiveIntegerField(default=0)
    primary_key_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tabla Inferida'
        verbose_name_plural = 'Tablas Inferidas'
        ordering = ['name']
        unique_together = ['dataset_import', 'name']

    def __str__(self):
        return f'{self.dataset_import.name} | {self.name}'


class DatasetColumn(models.Model):
    DATA_TYPES = [
        ('integer', 'Integer'),
        ('decimal', 'Decimal'),
        ('boolean', 'Boolean'),
        ('datetime', 'Datetime'),
        ('string', 'String'),
        ('text', 'Text'),
        ('unknown', 'Unknown'),
    ]

    table = models.ForeignKey(
        DatasetTable,
        on_delete=models.CASCADE,
        related_name='columns',
    )
    name = models.CharField(max_length=100)
    inferred_type = models.CharField(max_length=20, choices=DATA_TYPES, default='unknown')
    is_nullable = models.BooleanField(default=True)
    is_primary_key = models.BooleanField(default=False)
    uniqueness_ratio = models.FloatField(default=0)
    null_count = models.PositiveIntegerField(default=0)
    non_null_count = models.PositiveIntegerField(default=0)
    sample_values = models.JSONField(default=list, blank=True)
    ordinal_position = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Columna Inferida'
        verbose_name_plural = 'Columnas Inferidas'
        ordering = ['ordinal_position', 'name']
        unique_together = ['table', 'name']

    def __str__(self):
        return f'{self.table.name}.{self.name}'


class DatasetRelationship(models.Model):
    dataset_import = models.ForeignKey(
        DatasetImport,
        on_delete=models.CASCADE,
        related_name='relationships',
    )
    source_table = models.ForeignKey(
        DatasetTable,
        on_delete=models.CASCADE,
        related_name='outgoing_relationships',
    )
    source_column = models.ForeignKey(
        DatasetColumn,
        on_delete=models.CASCADE,
        related_name='outgoing_column_relationships',
    )
    target_table = models.ForeignKey(
        DatasetTable,
        on_delete=models.CASCADE,
        related_name='incoming_relationships',
    )
    target_column = models.ForeignKey(
        DatasetColumn,
        on_delete=models.CASCADE,
        related_name='incoming_column_relationships',
    )
    confidence = models.FloatField(default=0.5)
    inference_method = models.CharField(max_length=50, default='column_name')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Relacion Inferida'
        verbose_name_plural = 'Relaciones Inferidas'
        ordering = ['source_table__name', 'source_column__name']
        unique_together = [
            'dataset_import',
            'source_table',
            'source_column',
            'target_table',
            'target_column',
        ]

    def __str__(self):
        return (
            f'{self.source_table.name}.{self.source_column.name} -> '
            f'{self.target_table.name}.{self.target_column.name}'
        )
