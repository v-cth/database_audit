"""
Timestamp/datetime data quality checks
"""

import polars as pl
from typing import List, Dict


def check_timestamp_patterns(
    df: pl.DataFrame,
    col: str,
    constant_hour_threshold: float = 0.9,
    midnight_threshold: float = 0.95
) -> List[Dict]:
    """Detect timestamp patterns (same hour, effectively dates)"""
    issues = []

    non_null_df = df.filter(pl.col(col).is_not_null())
    non_null_count = len(non_null_df)

    if non_null_count == 0:
        return issues

    # For Date columns, skip time checks
    if df[col].dtype == pl.Date:
        return issues

    # Extract time components for Datetime
    time_analysis = non_null_df.select([
        pl.col(col).dt.hour().alias('hour'),
        pl.col(col).dt.minute().alias('minute'),
        pl.col(col).dt.second().alias('second'),
    ])

    # Check unique hours
    unique_hours = time_analysis['hour'].n_unique()

    if unique_hours <= 3:
        hour_counts = time_analysis.group_by('hour').agg(pl.len().alias('count')).sort('count', descending=True)
        most_common = hour_counts.row(0, named=True)
        pct_same_hour = most_common['count'] / non_null_count

        if pct_same_hour > constant_hour_threshold:
            examples = non_null_df[col].head(3).to_list()
            issues.append({
                'type': 'CONSTANT_HOUR',
                'hour': most_common['hour'],
                'pct': pct_same_hour * 100,
                'suggestion': 'Timestamp appears to be date-only, consider using DATE type',
                'examples': examples
            })

    # Check if all times are midnight
    midnight_count = time_analysis.filter(
        (pl.col('hour') == 0) &
        (pl.col('minute') == 0) &
        (pl.col('second') == 0)
    ).height

    midnight_pct = midnight_count / non_null_count

    if midnight_pct > midnight_threshold:
        examples = non_null_df[col].head(3).to_list()
        issues.append({
            'type': 'ALWAYS_MIDNIGHT',
            'pct': midnight_pct * 100,
            'suggestion': 'All timestamps at midnight - use DATE type instead',
            'examples': examples
        })

    return issues
