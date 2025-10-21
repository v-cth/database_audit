"""
Timestamp/datetime data quality checks
"""

import polars as pl
from typing import List, Dict
from datetime import datetime, date, timezone


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
    outlier_threshold_pct: float = 0.0
) -> List[Dict]:
    """
    Detect date/timestamp outliers (unusually old or future dates)

    Args:
        df: DataFrame to check
        col: Column name
        min_year: Minimum reasonable year (default: 1950)
        max_year: Maximum reasonable year (default: 2100)
        outlier_threshold_pct: Minimum percentage to report as issue (default: 0.0 = report all)

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


def check_future_dates(
    df: pl.DataFrame,
    col: str,
    threshold_pct: float = 0.0
) -> List[Dict]:
    """
    Detect dates/datetimes that are in the future relative to current time.

    Args:
        df: DataFrame to check
        col: Column name
        threshold_pct: Minimum percentage to report as issue (default: 0.0 = report all)

    Returns:
        List of issues found
    """
    issues = []

    non_null_df = df.filter(pl.col(col).is_not_null())
    non_null_count = len(non_null_df)

    if non_null_count == 0:
        return issues

    # Get current date/datetime based on column type
    col_dtype = df[col].dtype

    if col_dtype == pl.Date:
        # For Date columns, compare against today's date
        current_ref = date.today()
        future_rows = non_null_df.filter(pl.col(col) > current_ref)
    else:
        # For Datetime columns, compare against current datetime
        # Handle timezone-aware vs timezone-naive
        if hasattr(col_dtype, 'time_zone') and col_dtype.time_zone is not None:
            # Timezone-aware: use current UTC time with timezone
            current_ref = datetime.now(timezone.utc)
        else:
            # Timezone-naive: use current local time without timezone
            current_ref = datetime.now()

        future_rows = non_null_df.filter(pl.col(col) > current_ref)

    if len(future_rows) > 0:
        pct_future = len(future_rows) / non_null_count * 100

        # Only report if above threshold
        if pct_future >= threshold_pct:
            examples = future_rows[col].head(5).to_list()

            # Calculate how far into the future
            if col_dtype == pl.Date:
                max_future_date = future_rows[col].max()
                days_in_future = (max_future_date - current_ref).days if max_future_date else 0
            else:
                max_future_date = future_rows[col].max()
                if max_future_date:
                    if hasattr(col_dtype, 'time_zone') and col_dtype.time_zone is not None:
                        # For timezone-aware, both should be timezone-aware
                        time_diff = max_future_date - current_ref
                    else:
                        # For timezone-naive
                        time_diff = max_future_date - current_ref
                    days_in_future = time_diff.days
                else:
                    days_in_future = 0

            issues.append({
                'type': 'FUTURE_DATES',
                'count': len(future_rows),
                'pct': pct_future,
                'max_days_future': days_in_future,
                'current_reference': current_ref,
                'max_future_value': max_future_date,
                'suggestion': f'Found {len(future_rows)} dates in the future - check if these are valid or data entry errors',
                'examples': examples
            })

    return issues
