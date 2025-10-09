"""
Timestamp/datetime data quality checks
"""

import polars as pl
from typing import List, Dict
from datetime import datetime


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


def check_date_outliers(
    df: pl.DataFrame,
    col: str,
    min_year: int = 1950,
    max_year: int = 2100,
    outlier_threshold_pct: float = 0.01
) -> List[Dict]:
    """
    Detect date/timestamp outliers (unusually old or future dates)

    Args:
        df: DataFrame to check
        col: Column name
        min_year: Minimum reasonable year (default: 1950)
        max_year: Maximum reasonable year (default: 2100)
        outlier_threshold_pct: Minimum percentage to report as issue (default: 0.01 = 1%)

    Returns:
        List of issues found
    """
    issues = []

    non_null_df = df.filter(pl.col(col).is_not_null())
    non_null_count = len(non_null_df)

    if non_null_count == 0:
        return issues

    # Extract year for both Date and Datetime columns
    year_col = non_null_df.select(pl.col(col).dt.year().alias('year'))

    # Find dates before min_year
    too_old = non_null_df.filter(pl.col(col).dt.year() < min_year)
    if len(too_old) > 0:
        pct_old = len(too_old) / non_null_count * 100

        # Only report if above threshold
        if pct_old >= outlier_threshold_pct:
            examples = too_old[col].head(5).to_list()
            min_year_found = year_col['year'].min()

            issues.append({
                'type': 'DATES_TOO_OLD',
                'count': len(too_old),
                'pct': pct_old,
                'min_year_found': int(min_year_found),
                'threshold_year': min_year,
                'suggestion': f'Found dates before {min_year} - check if these are valid or data errors',
                'examples': examples
            })

    # Find dates after max_year
    too_future = non_null_df.filter(pl.col(col).dt.year() > max_year)
    if len(too_future) > 0:
        pct_future = len(too_future) / non_null_count * 100

        # Only report if above threshold
        if pct_future >= outlier_threshold_pct:
            examples = too_future[col].head(5).to_list()
            max_year_found = year_col['year'].max()

            issues.append({
                'type': 'DATES_TOO_FUTURE',
                'count': len(too_future),
                'pct': pct_future,
                'max_year_found': int(max_year_found),
                'threshold_year': max_year,
                'suggestion': f'Found dates after {max_year} - check if these are valid or placeholder values',
                'examples': examples
            })

    # Check for specific problematic years
    problematic_years = [1900, 1970, 2099, 2999, 9999]
    year_counts = year_col.group_by('year').agg(pl.len().alias('count'))

    for problem_year in problematic_years:
        year_data = year_counts.filter(pl.col('year') == problem_year)
        if len(year_data) > 0:
            count = year_data['count'][0]
            pct = count / non_null_count * 100

            # Only report if above threshold
            if pct >= outlier_threshold_pct:
                examples = non_null_df.filter(
                    pl.col(col).dt.year() == problem_year
                )[col].head(5).to_list()

                issues.append({
                    'type': 'SUSPICIOUS_YEAR',
                    'year': problem_year,
                    'count': int(count),
                    'pct': pct,
                    'suggestion': f'Year {problem_year} appears frequently - often used as placeholder/default value',
                    'examples': examples
                })

    return issues
