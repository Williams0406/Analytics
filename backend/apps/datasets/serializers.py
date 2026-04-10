from rest_framework import serializers

from .models import DatasetColumn, DatasetImport, DatasetRelationship, DatasetTable


class DatasetColumnSerializer(serializers.ModelSerializer):
    inferred_type_display = serializers.CharField(
        source='get_inferred_type_display',
        read_only=True,
    )

    class Meta:
        model = DatasetColumn
        fields = [
            'id',
            'name',
            'inferred_type',
            'inferred_type_display',
            'is_nullable',
            'is_primary_key',
            'uniqueness_ratio',
            'null_count',
            'non_null_count',
            'sample_values',
            'ordinal_position',
        ]


class DatasetTableSerializer(serializers.ModelSerializer):
    columns = DatasetColumnSerializer(many=True, read_only=True)

    class Meta:
        model = DatasetTable
        fields = [
            'id',
            'name',
            'source_file',
            'row_count',
            'column_count',
            'primary_key_name',
            'columns',
        ]


class DatasetRelationshipSerializer(serializers.ModelSerializer):
    source_table_name = serializers.CharField(source='source_table.name', read_only=True)
    source_column_name = serializers.CharField(source='source_column.name', read_only=True)
    target_table_name = serializers.CharField(source='target_table.name', read_only=True)
    target_column_name = serializers.CharField(source='target_column.name', read_only=True)

    class Meta:
        model = DatasetRelationship
        fields = [
            'id',
            'source_table',
            'source_table_name',
            'source_column',
            'source_column_name',
            'target_table',
            'target_table_name',
            'target_column',
            'target_column_name',
            'confidence',
            'inference_method',
        ]


class DatasetImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetImport
        fields = [
            'id',
            'name',
            'source_type',
            'status',
            'file_count',
            'tables_count',
            'relationships_count',
            'files_meta',
            'error_message',
            'created_at',
            'updated_at',
        ]


class DatasetImportDetailSerializer(DatasetImportSerializer):
    tables = DatasetTableSerializer(many=True, read_only=True)
    relationships = DatasetRelationshipSerializer(many=True, read_only=True)
    analysis_summary = serializers.JSONField(read_only=True)

    class Meta(DatasetImportSerializer.Meta):
        fields = DatasetImportSerializer.Meta.fields + ['analysis_summary', 'tables', 'relationships']
