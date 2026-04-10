from __future__ import annotations

from .models import DatasetImport
from .utils import safe_ratio


def extract_schema_profile(dataset_import: DatasetImport) -> dict:
    tables_data = []
    column_names = []

    for table in dataset_import.tables.prefetch_related('columns').all():
        columns = list(table.columns.all())
        column_names.extend(column.name for column in columns)
        total_non_null = sum(column.non_null_count for column in columns)
        total_cells = (table.row_count or 0) * (table.column_count or 0)

        tables_data.append({
            'name': table.name,
            'row_count': table.row_count,
            'column_count': table.column_count,
            'primary_key_name': table.primary_key_name,
            'completeness_ratio': safe_ratio(total_non_null, total_cells),
            'numeric_columns_count': sum(
                1 for column in columns if column.inferred_type in {'integer', 'decimal'}
            ),
            'categorical_columns_count': sum(
                1 for column in columns if column.inferred_type in {'string', 'text', 'boolean'}
            ),
            'datetime_columns_count': sum(
                1 for column in columns if column.inferred_type == 'datetime'
            ),
            'top_numeric_metrics': [],
            'top_dimensions': [],
            'sample_rows': [],
        })

    relationships_data = [
        {
            'source_table_name': relation.source_table.name,
            'source_column_name': relation.source_column.name,
            'target_table_name': relation.target_table.name,
            'target_column_name': relation.target_column.name,
            'confidence': relation.confidence,
        }
        for relation in dataset_import.relationships.select_related(
            'source_table',
            'source_column',
            'target_table',
            'target_column',
        )
    ]

    return {
        'name': dataset_import.name,
        'tables_count': dataset_import.tables_count,
        'relationships_count': dataset_import.relationships_count,
        'column_names': column_names,
        'tables': tables_data,
        'relationships': relationships_data,
    }
