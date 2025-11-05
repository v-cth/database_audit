"""
Export audit results to Polars DataFrame
"""

import logging
from typing import List, Dict, Any

try:
    import polars as pl
    HAS_POLARS = True
except ImportError:
    HAS_POLARS = False
    pl = None  # type: ignore

from .types import AuditResultsDict
from .exceptions import ExporterError
from .utils import validate_audit_results, MAX_EXAMPLES_COUNT

logger = logging.getLogger(__name__)


def export_to_dataframe(results: AuditResultsDict) -> 'pl.DataFrame':
    """
    Export audit results to a Polars DataFrame for easy analysis

    This function converts audit results into a tabular format with one row per issue.
    Each row contains metadata about the table, column, and specific issue details.

    Args:
        results: Audit results dictionary with required structure

    Returns:
        Polars DataFrame with one row per issue found

    Raises:
        ExporterError: If Polars is not installed or processing fails
        InvalidResultsError: If results dictionary has invalid structure

    Examples:
        >>> results = {
        ...     'table_name': 'users',
        ...     'total_rows': 1000,
        ...     'analyzed_rows': 1000,
        ...     'sampled': False,
        ...     'columns': {}
        ... }
        >>> df = export_to_dataframe(results)  # doctest: +SKIP
    """
    # Check if Polars is available
    if not HAS_POLARS:
        logger.error("Polars is not installed")
        raise ExporterError(
            "Polars is required for DataFrame export. "
            "Install it with: pip install polars"
        )

    # Validate input
    try:
        validated_results = validate_audit_results(results)
    except Exception as e:
        logger.error(f"Results validation failed: {e}")
        raise

    # Build rows from issues
    rows: List[Dict[str, Any]] = []

    try:
        for col_name, col_data in validated_results['columns'].items():
            for issue in col_data['issues']:
                # Safely extract examples
                examples = issue.get('examples', [])
                if isinstance(examples, list):
                    examples_subset = examples[:MAX_EXAMPLES_COUNT]
                    examples_str = str(examples_subset)
                else:
                    examples_str = str(examples)

                row = {
                    'table_name': validated_results['table_name'],
                    'total_rows': validated_results['total_rows'],
                    'analyzed_rows': validated_results['analyzed_rows'],
                    'sampled': validated_results['sampled'],
                    'column_name': col_name,
                    'column_dtype': col_data['dtype'],
                    'null_count': col_data['null_count'],
                    'null_pct': col_data['null_pct'],
                    'distinct_count': col_data.get('distinct_count', None),
                    'issue_type': issue['type'],
                    'issue_count': issue.get('count', 0),
                    'issue_pct': issue.get('pct', 0.0),
                    'suggestion': issue.get('suggestion', ''),
                    'examples': examples_str,
                    'audit_timestamp': validated_results.get('timestamp', '')
                }
                rows.append(row)

    except (KeyError, TypeError, AttributeError) as e:
        logger.error(f"Error processing results: {e}")
        raise ExporterError(f"Failed to process audit results: {e}") from e

    # Create DataFrame
    try:
        if not rows:
            # Return empty dataframe with correct schema if no issues
            logger.info("No issues found, returning empty DataFrame")
            return pl.DataFrame({
                'table_name': pl.Series([], dtype=pl.Utf8),
                'total_rows': pl.Series([], dtype=pl.Int64),
                'analyzed_rows': pl.Series([], dtype=pl.Int64),
                'sampled': pl.Series([], dtype=pl.Boolean),
                'column_name': pl.Series([], dtype=pl.Utf8),
                'column_dtype': pl.Series([], dtype=pl.Utf8),
                'null_count': pl.Series([], dtype=pl.Int64),
                'null_pct': pl.Series([], dtype=pl.Float64),
                'distinct_count': pl.Series([], dtype=pl.Int64),
                'issue_type': pl.Series([], dtype=pl.Utf8),
                'issue_count': pl.Series([], dtype=pl.Int64),
                'issue_pct': pl.Series([], dtype=pl.Float64),
                'suggestion': pl.Series([], dtype=pl.Utf8),
                'examples': pl.Series([], dtype=pl.Utf8),
                'audit_timestamp': pl.Series([], dtype=pl.Utf8)
            })

        df = pl.DataFrame(rows)
        logger.info(f"Created DataFrame with {len(df)} issue rows")
        return df

    except Exception as e:
        logger.error(f"Failed to create Polars DataFrame: {e}")
        raise ExporterError(f"Failed to create DataFrame: {e}") from e
