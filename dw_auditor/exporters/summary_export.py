"""
Export column summary to CSV/DataFrame
"""

import logging
from typing import Dict, List, Any

try:
    import polars as pl
    HAS_POLARS = True
except ImportError:
    HAS_POLARS = False
    pl = None  # type: ignore

from .exceptions import ExporterError, InvalidResultsError

logger = logging.getLogger(__name__)


def export_combined_column_summary_to_dataframe(all_results: List[Dict]) -> 'pl.DataFrame':
    """
    Export combined column summary for all tables to a single Polars DataFrame

    Args:
        all_results: List of audit results dictionaries (one per table)

    Returns:
        DataFrame with one row per column across all tables

    Raises:
        ExporterError: If Polars is not installed or processing fails
        InvalidResultsError: If results list is invalid
    """
    # Check if Polars is available
    if not HAS_POLARS:
        logger.error("Polars is not installed")
        raise ExporterError(
            "Polars is required for DataFrame export. "
            "Install it with: pip install polars"
        )

    # Validate input
    if not isinstance(all_results, list):
        raise InvalidResultsError(f"all_results must be a list, got: {type(all_results)}")

    all_rows: List[Dict[str, Any]] = []

    try:
        for results in all_results:
            if not isinstance(results, dict):
                logger.warning(f"Skipping non-dict result: {type(results)}")
                continue

            if 'column_summary' not in results or not results['column_summary']:
                logger.debug(f"Skipping table without column_summary: {results.get('table_name', 'unknown')}")
                continue

            for col_name, col_data in results['column_summary'].items():
                row = {
                    'table_name': results.get('table_name', 'unknown'),
                    'column_name': col_name,
                    'data_type': col_data.get('dtype', 'unknown'),
                    'status': col_data.get('status', 'UNKNOWN'),
                    'null_count': col_data.get('null_count', 0),
                    'null_pct': col_data.get('null_pct', 0.0),
                    'distinct_count': col_data.get('distinct_count', 0),
                    'source_dtype': col_data.get('source_dtype', None)
                }
                all_rows.append(row)

    except (KeyError, TypeError, AttributeError) as e:
        logger.error(f"Error processing column summaries: {e}")
        raise ExporterError(f"Failed to process column summaries: {e}") from e

    try:
        if not all_rows:
            logger.info("No column summaries found, returning empty DataFrame")
            return pl.DataFrame({
                'table_name': pl.Series([], dtype=pl.Utf8),
                'column_name': pl.Series([], dtype=pl.Utf8),
                'data_type': pl.Series([], dtype=pl.Utf8),
                'source_dtype': pl.Series([], dtype=pl.Utf8),
                'status': pl.Series([], dtype=pl.Utf8),
                'null_count': pl.Series([], dtype=pl.Int64),
                'null_pct': pl.Series([], dtype=pl.Float64),
                'distinct_count': pl.Series([], dtype=pl.Int64)
            })

        df = pl.DataFrame(all_rows)
        logger.info(f"Created combined column summary DataFrame with {len(df)} rows")
        return df

    except Exception as e:
        logger.error(f"Failed to create DataFrame: {e}")
        raise ExporterError(f"Failed to create DataFrame: {e}") from e


def export_column_summary_to_dataframe(results: Dict) -> 'pl.DataFrame':
    """
    Export column summary to a Polars DataFrame

    Args:
        results: Audit results dictionary

    Returns:
        DataFrame with one row per column with basic metrics

    Raises:
        ExporterError: If Polars is not installed or processing fails
        InvalidResultsError: If results dictionary is invalid
    """
    # Check if Polars is available
    if not HAS_POLARS:
        logger.error("Polars is not installed")
        raise ExporterError(
            "Polars is required for DataFrame export. "
            "Install it with: pip install polars"
        )

    # Validate input
    if not isinstance(results, dict):
        raise InvalidResultsError(f"results must be a dictionary, got: {type(results)}")

    if 'column_summary' not in results or not results['column_summary']:
        logger.info("No column_summary found, returning empty DataFrame")
        return pl.DataFrame({
            'table_name': pl.Series([], dtype=pl.Utf8),
            'column_name': pl.Series([], dtype=pl.Utf8),
            'data_type': pl.Series([], dtype=pl.Utf8),
            'source_dtype': pl.Series([], dtype=pl.Utf8),
            'status': pl.Series([], dtype=pl.Utf8),
            'null_count': pl.Series([], dtype=pl.Int64),
            'null_pct': pl.Series([], dtype=pl.Float64),
            'distinct_count': pl.Series([], dtype=pl.Int64)
        })

    rows: List[Dict[str, Any]] = []

    try:
        for col_name, col_data in results['column_summary'].items():
            row = {
                'table_name': results.get('table_name', 'unknown'),
                'column_name': col_name,
                'data_type': col_data.get('dtype', 'unknown'),
                'status': col_data.get('status', 'UNKNOWN'),
                'null_count': col_data.get('null_count', 0),
                'null_pct': col_data.get('null_pct', 0.0),
                'distinct_count': col_data.get('distinct_count', 0),
                'source_dtype': col_data.get('source_dtype', None)
            }
            rows.append(row)

    except (KeyError, TypeError, AttributeError) as e:
        logger.error(f"Error processing column summary: {e}")
        raise ExporterError(f"Failed to process column summary: {e}") from e

    try:
        df = pl.DataFrame(rows)
        logger.info(f"Created column summary DataFrame with {len(df)} rows")
        return df

    except Exception as e:
        logger.error(f"Failed to create DataFrame: {e}")
        raise ExporterError(f"Failed to create DataFrame: {e}") from e
