from __future__ import annotations

import warnings

import pandas as pd

COMMON_DATETIME_FORMATS = [
    '%Y-%m-%d',
    '%Y-%m-%d %H:%M',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%dT%H:%M',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%dT%H:%M:%S.%f',
    '%Y/%m/%d',
    '%Y/%m/%d %H:%M',
    '%Y/%m/%d %H:%M:%S',
    '%d/%m/%Y',
    '%d/%m/%Y %H:%M',
    '%d/%m/%Y %H:%M:%S',
    '%m/%d/%Y',
    '%m/%d/%Y %H:%M',
    '%m/%d/%Y %H:%M:%S',
    '%d-%m-%Y',
    '%d-%m-%Y %H:%M',
    '%d-%m-%Y %H:%M:%S',
    '%m-%d-%Y',
    '%m-%d-%Y %H:%M',
    '%m-%d-%Y %H:%M:%S',
]
DATETIME_SAMPLE_SIZE = 250
DATETIME_WARNING_MESSAGE = 'Could not infer format, so each element will be parsed individually'


def _clean_datetime_input(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors='coerce')

    cleaned = series.astype('string').str.strip()
    return cleaned.mask(cleaned == '', pd.NA)


def _sample_series(series: pd.Series, sample_size: int = DATETIME_SAMPLE_SIZE) -> pd.Series:
    non_null = series.dropna()
    if len(non_null) <= sample_size:
        return non_null
    return non_null.sample(sample_size, random_state=7)


def infer_datetime_format(series: pd.Series, sample_size: int = DATETIME_SAMPLE_SIZE) -> str:
    sample = _sample_series(_clean_datetime_input(series), sample_size=sample_size)
    if sample.empty:
        return ''

    for candidate_format in COMMON_DATETIME_FORMATS:
        parsed = pd.to_datetime(sample, format=candidate_format, errors='coerce')
        success_ratio = float(parsed.notna().mean()) if len(sample) else 0
        if success_ratio >= 0.9:
            return candidate_format

    return ''


def parse_datetime_series(series: pd.Series, sample_size: int = DATETIME_SAMPLE_SIZE) -> pd.Series:
    cleaned = _clean_datetime_input(series)
    if cleaned.dropna().empty:
        return pd.to_datetime(cleaned, errors='coerce')

    candidate_format = infer_datetime_format(cleaned, sample_size=sample_size)
    if candidate_format:
        return pd.to_datetime(cleaned, format=candidate_format, errors='coerce')

    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore',
            message=f'.*{DATETIME_WARNING_MESSAGE}.*',
            category=UserWarning,
        )
        try:
            return pd.to_datetime(cleaned, format='mixed', errors='coerce')
        except TypeError:
            return pd.to_datetime(cleaned, errors='coerce')
