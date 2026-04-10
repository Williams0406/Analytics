import io
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path

from decouple import config
import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections
from django.db import transaction
from django.db.utils import OperationalError
from django.utils import timezone

from .analysis_summary import build_dataset_analysis
from .datetime_utils import DATETIME_SAMPLE_SIZE, parse_datetime_series
from .models import DatasetColumn, DatasetImport, DatasetRelationship, DatasetTable

SUPPORTED_EXTENSIONS = {'.csv', '.tsv', '.xlsx', '.xls'}
DISPLAY_SAMPLE_SIZE = 5
RELATIONSHIP_SAMPLE_SIZE = int(config('DATASET_RELATIONSHIP_SAMPLE_SIZE', default='25'))
MAX_FILE_SIZE_BYTES = int(float(config('DATASET_IMPORT_MAX_FILE_SIZE_MB', default='100')) * 1024 * 1024)
DATASET_IMPORT_TIMEOUT_SECONDS = float(config('DATASET_IMPORT_TIMEOUT_SECONDS', default='180'))
DATASET_IMPORT_DB_RETRIES = int(config('DATASET_IMPORT_DB_RETRIES', default='5'))
DATASET_IMPORT_DB_RETRY_DELAY_SECONDS = float(config('DATASET_IMPORT_DB_RETRY_DELAY_SECONDS', default='0.1'))
logger = logging.getLogger(__name__)


def _file_size_limit_mb() -> int:
    return max(1, int(round(MAX_FILE_SIZE_BYTES / (1024 * 1024))))


def _validate_file_size(file_name: str, size_bytes: int) -> None:
    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f'El archivo "{file_name}" excede el limite de {_file_size_limit_mb()}MB.'
        )


def normalize_identifier(value: str) -> str:
    normalized = re.sub(r'[^a-zA-Z0-9]+', '_', value.strip().lower())
    normalized = re.sub(r'_+', '_', normalized).strip('_')
    return normalized or 'table'


def singularize(value: str) -> str:
    if value.endswith('ies') and len(value) > 3:
        return value[:-3] + 'y'
    if value.endswith('ses') and len(value) > 3:
        return value[:-2]
    if value.endswith('s') and not value.endswith('ss') and len(value) > 1:
        return value[:-1]
    return value


def build_table_aliases(table_name: str) -> set[str]:
    aliases = {table_name, singularize(table_name)}
    tokens = table_name.split('_')
    if tokens:
        aliases.add(tokens[-1])
        aliases.add(singularize(tokens[-1]))
    return {alias for alias in aliases if alias}


def ensure_unique_table_name(base_name: str, used_names: set[str]) -> str:
    candidate = base_name
    suffix = 2
    while candidate in used_names:
        candidate = f'{base_name}_{suffix}'
        suffix += 1
    used_names.add(candidate)
    return candidate


def make_unique_identifiers(values: list) -> list[str]:
    counters = {}
    normalized_values = []

    for value in values:
        base_name = normalize_identifier(str(value))
        next_index = counters.get(base_name, 0) + 1
        counters[base_name] = next_index
        normalized_values.append(base_name if next_index == 1 else f'{base_name}_{next_index}')

    return normalized_values


def read_tabular_file(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f'El archivo "{uploaded_file.name}" no es compatible. '
            'Usa CSV, TSV o Excel.'
        )

    size = getattr(uploaded_file, 'size', None)
    if size is None:
        content = uploaded_file.read()
        size = len(content)
        _validate_file_size(uploaded_file.name, size)
        buffer = io.BytesIO(content)
    else:
        _validate_file_size(uploaded_file.name, int(size))
        buffer = io.BytesIO(uploaded_file.read())

    if suffix == '.csv':
        try:
            return pd.read_csv(buffer)
        except UnicodeDecodeError:
            buffer.seek(0)
            return pd.read_csv(buffer, encoding='latin1')

    if suffix == '.tsv':
        return pd.read_csv(buffer, sep='\t')

    return pd.read_excel(buffer)


def validate_uploaded_files(files: list) -> None:
    if not files:
        raise ValueError('Debes subir al menos un archivo.')

    for item in files:
        file_name = item['name'] if isinstance(item, dict) else item.name
        if Path(file_name).suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f'El archivo "{file_name}" no es compatible. Usa CSV, TSV o Excel.'
            )
        declared_size = None
        if isinstance(item, dict):
            declared_size = item.get('size')
            if declared_size is None and 'content' in item:
                declared_size = len(item['content'])
        else:
            declared_size = getattr(item, 'size', None)
        if declared_size is not None:
            _validate_file_size(file_name, int(declared_size))


def infer_series_type(series: pd.Series) -> str:
    non_null = series.dropna()
    if non_null.empty:
        return 'unknown'

    if pd.api.types.is_bool_dtype(non_null):
        return 'boolean'
    if pd.api.types.is_integer_dtype(non_null):
        return 'integer'
    if pd.api.types.is_float_dtype(non_null):
        return 'decimal'
    if pd.api.types.is_datetime64_any_dtype(non_null):
        return 'datetime'

    as_text = non_null.astype(str).str.strip()
    if as_text.empty:
        return 'unknown'

    lowered = as_text.str.lower()
    if lowered.isin({'true', 'false', 'yes', 'no', '0', '1'}).all():
        return 'boolean'

    numeric = pd.to_numeric(as_text, errors='coerce')
    numeric_ratio = float(numeric.notna().mean()) if len(as_text) else 0
    if numeric_ratio >= 0.9:
        if (numeric.dropna() % 1 == 0).all():
            return 'integer'
        return 'decimal'

    date_like_ratio = float(as_text.str.contains(r'[-/:T]').mean()) if len(as_text) else 0
    if date_like_ratio >= 0.6:
        sample = as_text if len(as_text) <= DATETIME_SAMPLE_SIZE else as_text.sample(DATETIME_SAMPLE_SIZE, random_state=7)
        parsed_sample = parse_datetime_series(sample)
        sample_ratio = float(parsed_sample.notna().mean()) if len(sample) else 0
        if sample_ratio < 0.85:
            return 'text' if int(as_text.str.len().max()) > 60 else 'string'

        parsed_dates = parse_datetime_series(as_text)
        date_ratio = float(parsed_dates.notna().mean()) if len(as_text) else 0
        if date_ratio >= 0.9:
            return 'datetime'

    return 'text' if int(as_text.str.len().max()) > 60 else 'string'


def build_column_profile(series: pd.Series, position: int) -> dict:
    non_null = series.dropna()
    uniqueness_ratio = 0.0
    if len(non_null):
        uniqueness_ratio = round(float(non_null.nunique() / len(non_null)), 4)

    samples = []
    relationship_samples = []
    if len(non_null):
        unique_values = non_null.astype(str).drop_duplicates()
        samples = [str(value)[:80] for value in unique_values.head(DISPLAY_SAMPLE_SIZE).tolist()]
        relationship_samples = [
            str(value)[:80]
            for value in unique_values.head(max(DISPLAY_SAMPLE_SIZE, RELATIONSHIP_SAMPLE_SIZE)).tolist()
        ]

    return {
        'name': normalize_identifier(str(series.name)),
        'inferred_type': infer_series_type(series),
        'is_nullable': bool(series.isna().any()),
        'uniqueness_ratio': uniqueness_ratio,
        'null_count': int(series.isna().sum()),
        'non_null_count': int(non_null.shape[0]),
        'sample_values': samples,
        'relationship_sample_values': relationship_samples,
        'ordinal_position': position,
    }


def infer_primary_key(table_name: str, columns: list[dict]) -> str:
    column_map = {column['name']: column for column in columns}
    aliases = build_table_aliases(table_name)
    direct_candidates = ['id'] + [f'{alias}_id' for alias in aliases]

    for candidate in direct_candidates:
        column = column_map.get(candidate)
        if column and column['uniqueness_ratio'] >= 0.98 and not column['is_nullable']:
            return candidate

    for column in columns:
        if column['uniqueness_ratio'] >= 0.98 and not column['is_nullable']:
            return column['name']

    for column in columns:
        if column['uniqueness_ratio'] >= 0.98:
            return column['name']

    return ''


def prepare_table_profile(uploaded_file, used_names: set[str]) -> dict:
    dataframe = read_tabular_file(uploaded_file)
    if dataframe is None or not len(dataframe.columns):
        raise ValueError(f'El archivo "{uploaded_file.name}" no contiene datos tabulares utilizables.')

    dataframe.columns = make_unique_identifiers(dataframe.columns.tolist())
    table_name = ensure_unique_table_name(
        normalize_identifier(Path(uploaded_file.name).stem),
        used_names,
    )
    columns = [
        build_column_profile(dataframe[column_name], position=index + 1)
        for index, column_name in enumerate(dataframe.columns.tolist())
    ]
    primary_key_name = infer_primary_key(table_name, columns)

    for column in columns:
        column['is_primary_key'] = column['name'] == primary_key_name
        column['sample_lookup'] = set(column.get('relationship_sample_values') or column['sample_values'])

    return {
        'name': table_name,
        'source_file': uploaded_file.name,
        'row_count': int(len(dataframe.index)),
        'column_count': int(len(dataframe.columns)),
        'primary_key_name': primary_key_name,
        'columns': columns,
        'aliases': build_table_aliases(table_name),
        'dataframe': dataframe,
    }


def relationship_score(source_column: dict, target_table_profile: dict, target_pk_name: str) -> float:
    source_column_name = source_column['name']
    base_name = source_column_name[:-3] if source_column_name.endswith('_id') else source_column_name
    aliases = target_table_profile['aliases']
    target_pk_base = target_pk_name[:-3] if target_pk_name.endswith('_id') else target_pk_name

    if base_name == target_table_profile['name']:
        return 0.97
    if base_name in aliases or base_name == target_pk_base:
        return 0.92
    if source_column_name in aliases or source_column_name == target_table_profile['name'] or source_column_name == target_pk_base:
        return 0.86 if source_column.get('uniqueness_ratio', 1.0) < 0.98 else 0.0
    if any(source_column_name.endswith(f'_{alias}') for alias in aliases | {target_pk_base}):
        return 0.84
    if source_column_name == target_pk_name:
        return 0.76
    return 0.0


def infer_relationships(table_profiles: list[dict]) -> list[dict]:
    relationships = []
    seen = set()
    table_map = {profile['name']: profile for profile in table_profiles}

    for source_profile in table_profiles:
        for column in source_profile['columns']:
            column_name = column['name']
            if column['is_primary_key'] or column_name == 'id':
                continue
            if column.get('inferred_type') not in {'integer', 'decimal', 'string'}:
                continue
            if not (column_name.endswith('_id') or column['uniqueness_ratio'] < 0.98):
                continue

            best_match = None
            best_score = 0.0

            for target_name, target_profile in table_map.items():
                if target_name == source_profile['name']:
                    continue

                target_pk_name = target_profile['primary_key_name'] or 'id'
                score = relationship_score(column, target_profile, target_pk_name)
                if score <= 0:
                    continue

                if target_profile['primary_key_name']:
                    target_pk = next(
                        (
                            target_column
                            for target_column in target_profile['columns']
                            if target_column['name'] == target_profile['primary_key_name']
                        ),
                        None,
                    )
                    if target_pk and column['sample_lookup'] and target_pk['sample_lookup']:
                        overlap = len(column['sample_lookup'] & target_pk['sample_lookup'])
                        if overlap:
                            max_overlap = max(
                                1,
                                min(len(column['sample_lookup']), len(target_pk['sample_lookup'])),
                            )
                            score = min(0.99, score + 0.03 + min(0.08, overlap / max_overlap))

                if score > best_score:
                    best_score = score
                    best_match = (target_name, target_pk_name)

            if best_match and best_score >= 0.75:
                key = (source_profile['name'], column_name, best_match[0], best_match[1])
                if key in seen:
                    continue
                seen.add(key)
                relationships.append({
                    'source_table_name': source_profile['name'],
                    'source_column_name': column_name,
                    'target_table_name': best_match[0],
                    'target_column_name': best_match[1],
                    'confidence': round(best_score, 2),
                    'inference_method': 'column_name',
                })

    return relationships


def build_import_name(name: str, files: list) -> str:
    cleaned = (name or '').strip()
    if cleaned:
        return cleaned
    if len(files) == 1:
        first_name = files[0]['name'] if isinstance(files[0], dict) else files[0].name
        return f'Importacion {Path(first_name).stem}'
    return f'Importacion de {len(files)} archivos'


def create_dataset_import_record(*, user, files: list, name: str = '') -> DatasetImport:
    file_names = [item['name'] if isinstance(item, dict) else item.name for item in files]
    files_meta = [
        {
            'file_name': file_name,
            'status': 'processing',
        }
        for file_name in file_names
    ]
    return DatasetImport.objects.create(
        user=user,
        name=build_import_name(name, files),
        source_type='file_bundle',
        status='processing',
        file_count=len(files),
        files_meta=files_meta,
    )


def process_dataset_import(
    dataset_import: DatasetImport,
    files: list,
    progress_guard=None,
) -> DatasetImport:
    if not files:
        raise ValueError('Debes subir al menos un archivo.')

    try:
        used_names = set()
        table_profiles = []
        for uploaded_file in files:
            if progress_guard:
                progress_guard()
            table_profiles.append(prepare_table_profile(uploaded_file, used_names))
        if progress_guard:
            progress_guard()
        relationships = infer_relationships(table_profiles)
        if progress_guard:
            progress_guard()
        analysis_summary = build_dataset_analysis(
            dataset_import.name,
            table_profiles,
            relationships,
            progress_guard=progress_guard,
        )
        if progress_guard:
            progress_guard()

        for attempt in range(DATASET_IMPORT_DB_RETRIES):
            try:
                with transaction.atomic():
                    if not DatasetImport.objects.filter(pk=dataset_import.pk).exists():
                        return dataset_import

                    dataset_import = DatasetImport.objects.get(pk=dataset_import.pk)
                    if dataset_import.status != 'processing':
                        return dataset_import
                    table_records = {}
                    column_records = {}
                    files_meta = []

                    for profile in table_profiles:
                        if progress_guard:
                            progress_guard()
                        table = DatasetTable.objects.create(
                            dataset_import=dataset_import,
                            name=profile['name'],
                            source_file=profile['source_file'],
                            row_count=profile['row_count'],
                            column_count=profile['column_count'],
                            primary_key_name=profile['primary_key_name'],
                        )
                        table_records[profile['name']] = table
                        files_meta.append({
                            'file_name': profile['source_file'],
                            'table_name': profile['name'],
                            'rows': profile['row_count'],
                            'columns': profile['column_count'],
                        })

                        for column_profile in profile['columns']:
                            column = DatasetColumn.objects.create(
                                table=table,
                                name=column_profile['name'],
                                inferred_type=column_profile['inferred_type'],
                                is_nullable=column_profile['is_nullable'],
                                is_primary_key=column_profile['is_primary_key'],
                                uniqueness_ratio=column_profile['uniqueness_ratio'],
                                null_count=column_profile['null_count'],
                                non_null_count=column_profile['non_null_count'],
                                sample_values=column_profile['sample_values'],
                                ordinal_position=column_profile['ordinal_position'],
                            )
                            column_records[(profile['name'], column_profile['name'])] = column

                    for relationship in relationships:
                        DatasetRelationship.objects.create(
                            dataset_import=dataset_import,
                            source_table=table_records[relationship['source_table_name']],
                            source_column=column_records[
                                (relationship['source_table_name'], relationship['source_column_name'])
                            ],
                            target_table=table_records[relationship['target_table_name']],
                            target_column=column_records[
                                (relationship['target_table_name'], relationship['target_column_name'])
                            ],
                            confidence=relationship['confidence'],
                            inference_method=relationship['inference_method'],
                        )

                    dataset_import.status = 'ready'
                    dataset_import.tables_count = len(table_profiles)
                    dataset_import.relationships_count = len(relationships)
                    dataset_import.files_meta = files_meta
                    dataset_import.analysis_summary = analysis_summary
                    dataset_import.error_message = ''
                    dataset_import.save(
                        update_fields=[
                            'status',
                            'tables_count',
                            'relationships_count',
                            'files_meta',
                            'analysis_summary',
                            'error_message',
                            'updated_at',
                        ]
                    )

                return dataset_import
            except OperationalError as exc:
                if 'locked' not in str(exc).lower() or attempt == DATASET_IMPORT_DB_RETRIES - 1:
                    raise
                logger.warning(
                    'Dataset import %s encontro un lock de DB; reintentando (%s/%s)',
                    dataset_import.pk,
                    attempt + 1,
                    DATASET_IMPORT_DB_RETRIES,
                )
                time.sleep(DATASET_IMPORT_DB_RETRY_DELAY_SECONDS * (attempt + 1))

    except Exception as exc:
        try:
            dataset_import.status = 'failed'
            dataset_import.error_message = str(exc)
            dataset_import.save(update_fields=['status', 'error_message', 'updated_at'])
        except Exception:
            pass
        raise


def import_dataset_bundle(*, user, files: list, name: str = '') -> DatasetImport:
    validate_uploaded_files(files)
    dataset_import = create_dataset_import_record(user=user, files=files, name=name)
    return process_dataset_import(dataset_import, files)


def serialize_uploaded_file(uploaded_file) -> dict:
    size = getattr(uploaded_file, 'size', None)
    if size is not None:
        _validate_file_size(uploaded_file.name, int(size))
    content = uploaded_file.read()
    _validate_file_size(uploaded_file.name, len(content))
    return {
        'name': uploaded_file.name,
        'content_type': getattr(uploaded_file, 'content_type', 'application/octet-stream'),
        'size': len(content),
        'content': content,
    }


def _rehydrate_uploaded_files(file_payloads: list[dict]) -> list[SimpleUploadedFile]:
    return [
        SimpleUploadedFile(
            payload['name'],
            payload['content'],
            content_type=payload.get('content_type') or 'application/octet-stream',
        )
        for payload in file_payloads
    ]


def _mark_import_failed(dataset_import_id: int, message: str) -> None:
    DatasetImport.objects.filter(pk=dataset_import_id).update(
        status='failed',
        error_message=message,
        updated_at=timezone.now(),
    )


def _run_async_dataset_import(dataset_import_id: int, file_payloads: list[dict]) -> None:
    close_old_connections()
    try:
        dataset_import = DatasetImport.objects.get(pk=dataset_import_id)
    except DatasetImport.DoesNotExist:
        return

    cancel_event = threading.Event()

    def progress_guard() -> None:
        if cancel_event.is_set():
            raise TimeoutError(
                f'El procesamiento excedio el limite de {DATASET_IMPORT_TIMEOUT_SECONDS:.0f}s.'
            )

    def _process() -> DatasetImport:
        close_old_connections()
        try:
            return process_dataset_import(dataset_import, files, progress_guard)
        finally:
            close_old_connections()

    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='dataset-import')
    try:
        files = _rehydrate_uploaded_files(file_payloads)
        future = executor.submit(_process)
        future.result(timeout=DATASET_IMPORT_TIMEOUT_SECONDS)
    except FutureTimeoutError:
        cancel_event.set()
        logger.warning(
            'Dataset import %s supero el timeout total de %.1fs',
            dataset_import_id,
            DATASET_IMPORT_TIMEOUT_SECONDS,
        )
        _mark_import_failed(
            dataset_import_id,
            f'El procesamiento excedio el limite de {DATASET_IMPORT_TIMEOUT_SECONDS:.0f}s.',
        )
    except Exception:
        logger.exception('Dataset import %s fallo durante el procesamiento asincrono', dataset_import_id)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
        close_old_connections()


def enqueue_dataset_import(*, user, files: list, name: str = '') -> DatasetImport:
    validate_uploaded_files(files)
    file_payloads = [serialize_uploaded_file(uploaded_file) for uploaded_file in files]
    dataset_import = create_dataset_import_record(user=user, files=file_payloads, name=name)

    def _start_worker():
        worker = threading.Thread(
            target=_run_async_dataset_import,
            args=(dataset_import.id, file_payloads),
            daemon=True,
        )
        worker.start()

    transaction.on_commit(_start_worker)
    return dataset_import
