from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd
from scipy.stats import chi2 as chi2_dist


def safe_ratio(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return round(float(numerator / denominator), 4)


def score_column_name(column_name: str, keywords: list[str]) -> int:
    lowered = column_name.lower()
    return sum(1 for keyword in keywords if keyword in lowered)


def score_column_keywords(column_names: list[str], keywords: list[str]) -> int:
    lowered_columns = [str(column_name).lower() for column_name in column_names]
    return sum(
        1
        for column_name in lowered_columns
        for keyword in keywords
        if keyword in column_name
    )


def is_identifier_like(column_name: str) -> bool:
    lowered = column_name.lower()
    return lowered == 'id' or lowered.startswith('id_') or lowered.endswith('_id')


def normalize_lookup_label(value: str) -> str:
    normalized = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-zA-Z0-9]+', ' ', normalized.lower()).strip()


def format_compact_number(value) -> str:
    if value is None:
        return '0'
    absolute_value = abs(float(value))
    if absolute_value >= 1_000_000:
        return f'{value / 1_000_000:.1f}M'
    if absolute_value >= 1_000:
        return f'{value / 1_000:.1f}K'
    if float(value).is_integer():
        return f'{int(value):,}'
    return f'{float(value):,.1f}'


def format_percent(value: float | None, decimals: int = 1, signed: bool = False) -> str:
    if value is None:
        return '0%'
    sign = '+.' if signed else '.'
    template = f'{{value:{sign}{decimals}f}}%'
    return template.format(value=float(value))


def json_value(value):
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (int, float, str, bool)):
        return value

    try:
        as_float = float(value)
        if as_float.is_integer():
            return int(as_float)
        return round(as_float, 4)
    except (TypeError, ValueError):
        return str(value)


def chi_square_is_significant(observed_counts, alpha: float = 0.05) -> tuple[bool, float]:
    counts = np.asarray([count for count in observed_counts if count >= 0], dtype=float)
    if counts.size < 2 or counts.sum() <= 0:
        return False, 0.0

    expected = counts.sum() / counts.size
    if expected <= 0:
        return False, 0.0

    statistic = float(np.sum(((counts - expected) ** 2) / expected))
    degrees_of_freedom = int(counts.size - 1)
    critical_value = float(chi2_dist.ppf(1.0 - alpha, degrees_of_freedom))

    return statistic > critical_value, round(statistic, 2)
