from django.contrib import admin

from .models import DatasetColumn, DatasetImport, DatasetRelationship, DatasetTable


class DatasetColumnInline(admin.TabularInline):
    model = DatasetColumn
    extra = 0


@admin.register(DatasetTable)
class DatasetTableAdmin(admin.ModelAdmin):
    list_display = ('name', 'dataset_import', 'row_count', 'column_count', 'primary_key_name')
    search_fields = ('name', 'dataset_import__name', 'dataset_import__user__email')
    inlines = [DatasetColumnInline]


@admin.register(DatasetImport)
class DatasetImportAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'user',
        'status',
        'file_count',
        'tables_count',
        'relationships_count',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'user__email')


@admin.register(DatasetRelationship)
class DatasetRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        'dataset_import',
        'source_table',
        'source_column',
        'target_table',
        'target_column',
        'confidence',
    )
    list_filter = ('inference_method',)
    search_fields = ('dataset_import__name', 'source_table__name', 'target_table__name')
