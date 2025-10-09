"""
Main auditor class that coordinates all auditing functionality
"""

import polars as pl
from typing import Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path

from ..checks.string_checks import (
    check_trailing_spaces,
    check_case_duplicates,
    check_special_chars,
    check_numeric_strings
)
from ..checks.timestamp_checks import check_timestamp_patterns
from ..utils.security import mask_pii_columns, sanitize_connection_string
from ..utils.output import print_results, get_summary_stats
from ..exporters.dataframe_export import export_to_dataframe
from ..exporters.json_export import export_to_json
from ..exporters.html_export import export_to_html


class SecureTableAuditor:
    """Audit data warehouse tables with security controls"""

    def __init__(self, sample_size: int = 100000, sample_threshold: int = 1000000):
        """
        Args:
            sample_size: Number of rows to sample if table exceeds threshold
            sample_threshold: Row count threshold for sampling
        """
        self.sample_size = sample_size
        self.sample_threshold = sample_threshold
        self.audit_log = []

    def audit_from_database(
        self,
        table_name: str,
        connection_string: str,
        schema: Optional[str] = None,
        mask_pii: bool = True,
        sample_in_db: bool = True,
        custom_query: Optional[str] = None,
        custom_pii_keywords: List[str] = None
    ) -> Dict:
        """
        Audit table directly from database (RECOMMENDED)
        No intermediate files - query directly and audit in memory

        Args:
            table_name: Name of table to audit
            connection_string: Database connection string
                Examples:
                - PostgreSQL: "postgresql://user:pass@host:5432/db"
                - MySQL: "mysql://user:pass@host:3306/db"
                - SQLite: "sqlite:///path/to/db.sqlite"
            schema: Schema name (optional, e.g., 'public', 'dbo')
            mask_pii: Automatically mask columns with PII keywords
            sample_in_db: Use database sampling for large tables (faster & more secure)
            custom_query: Custom SQL query instead of SELECT * (advanced)
            custom_pii_keywords: Additional PII keywords beyond defaults

        Returns:
            Dictionary with audit results
        """
        try:
            import connectorx as cx
        except ImportError:
            raise ImportError(
                "connectorx is required for database connections.\n"
                "Install with: pip install connectorx"
            )

        # Log the audit
        self._log_audit(table_name, connection_string)

        print(f"🔐 Secure audit mode: Direct database query (no file export)")

        # Build query
        if custom_query:
            query = custom_query
        else:
            full_table = f"{schema}.{table_name}" if schema else table_name

            # Check if we should sample in DB
            if sample_in_db:
                # Try to get row count first
                try:
                    count_query = f"SELECT COUNT(*) as cnt FROM {full_table}"
                    count_df = pl.read_database_uri(count_query, connection_string)
                    row_count = count_df['cnt'][0]

                    if row_count > self.sample_threshold:
                        print(f"📊 Table has {row_count:,} rows - sampling in database")
                        # Use database-native sampling (works for PostgreSQL, may need adjustment for others)
                        query = f"""
                            SELECT * FROM {full_table}
                            TABLESAMPLE SYSTEM (10)
                            LIMIT {self.sample_size}
                        """
                    else:
                        query = f"SELECT * FROM {full_table}"
                except Exception as e:
                    # If count fails, just query with limit
                    print(f"⚠️  Could not get row count, using LIMIT")
                    query = f"SELECT * FROM {full_table} LIMIT {self.sample_size}"
            else:
                query = f"SELECT * FROM {full_table}"

        print(f"🔍 Executing: {query[:100]}...")

        # Query directly - no intermediate storage
        df = pl.read_database_uri(query, connection_string)

        print(f"✅ Loaded {len(df):,} rows into memory")

        # Mask PII if requested
        if mask_pii:
            df = mask_pii_columns(df, custom_pii_keywords)

        # Run audit
        results = self.audit_table(df, table_name)

        # Clear from memory
        del df

        return results

    def audit_from_file(
        self,
        file_path: Union[str, Path],
        table_name: Optional[str] = None,
        mask_pii: bool = True,
        custom_pii_keywords: List[str] = None
    ) -> Dict:
        """
        Audit from CSV or Parquet file

        Args:
            file_path: Path to CSV or Parquet file
            table_name: Optional name for reporting
            mask_pii: Mask PII columns
            custom_pii_keywords: Additional PII keywords beyond defaults
        """
        file_path = Path(file_path)
        table_name = table_name or file_path.stem

        print(f"📁 Loading file: {file_path}")

        # Read based on extension
        if file_path.suffix.lower() == '.csv':
            df = pl.read_csv(file_path)
        elif file_path.suffix.lower() in ['.parquet', '.pq']:
            df = pl.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        print(f"✅ Loaded {len(df):,} rows")

        # Mask PII if requested
        if mask_pii:
            df = mask_pii_columns(df, custom_pii_keywords)

        return self.audit_table(df, table_name)

    def audit_table(
        self,
        df: pl.DataFrame,
        table_name: str = "table",
        check_config: Optional[Dict] = None
    ) -> Dict:
        """
        Main audit function - runs all checks on a Polars DataFrame

        Args:
            df: Polars DataFrame to audit
            table_name: Name of the table for reporting
            check_config: Optional configuration for which checks to run

        Returns:
            Dictionary with audit results
        """
        print(f"\n{'='*60}")
        print(f"Auditing: {table_name}")
        print(f"Total rows: {len(df):,}")
        print(f"{'='*60}\n")

        # Sample if needed (only if not already sampled in DB)
        original_size = len(df)
        if len(df) > self.sample_threshold:
            df = df.sample(n=min(self.sample_size, len(df)), seed=42)
            print(f"⚠️  Sampling {len(df):,} rows (table has {original_size:,} rows)\n")

        results = {
            'table_name': table_name,
            'total_rows': original_size,
            'sampled': len(df) < original_size,
            'analyzed_rows': len(df),
            'columns': {},
            'timestamp': datetime.now().isoformat()
        }

        # Default check config
        if check_config is None:
            check_config = {
                'trailing_spaces': True,
                'case_duplicates': True,
                'special_chars': True,
                'numeric_strings': True,
                'timestamp_patterns': True
            }

        # Analyze each column
        for col in df.columns:
            col_results = self._audit_column(df, col, check_config)
            if col_results['issues']:
                results['columns'][col] = col_results

        print_results(results)
        return results

    def _audit_column(self, df: pl.DataFrame, col: str, check_config: Dict) -> Dict:
        """Audit a single column for all issues"""
        dtype = df[col].dtype
        null_count = df[col].null_count()
        total_rows = len(df)

        col_result = {
            'dtype': str(dtype),
            'null_count': null_count,
            'null_pct': (null_count / total_rows * 100) if total_rows > 0 else 0,
            'issues': []
        }

        # Skip if all nulls or masked
        if null_count == total_rows:
            return col_result

        # Skip masked columns
        first_non_null = df[col].drop_nulls().head(1)
        if len(first_non_null) > 0 and first_non_null[0] == "***PII_MASKED***":
            return col_result

        # String column checks
        if dtype in [pl.Utf8, pl.String]:
            if check_config.get('trailing_spaces', True):
                col_result['issues'].extend(check_trailing_spaces(df, col))
            if check_config.get('case_duplicates', True):
                col_result['issues'].extend(check_case_duplicates(df, col))
            if check_config.get('special_chars', True):
                col_result['issues'].extend(check_special_chars(df, col))
            if check_config.get('numeric_strings', True):
                col_result['issues'].extend(check_numeric_strings(df, col))

        # Timestamp/Date checks
        elif dtype in [pl.Datetime, pl.Date]:
            if check_config.get('timestamp_patterns', True):
                col_result['issues'].extend(check_timestamp_patterns(df, col))

        return col_result

    def _log_audit(self, table_name: str, connection_string: str):
        """Log audit activity"""
        safe_conn = sanitize_connection_string(connection_string)

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'table': table_name,
            'connection': safe_conn
        }
        self.audit_log.append(log_entry)

    def get_audit_log(self) -> List[Dict]:
        """Get audit history"""
        return self.audit_log

    def export_results_to_dataframe(self, results: Dict) -> pl.DataFrame:
        """
        Export audit results to a Polars DataFrame for easy analysis

        Returns:
            DataFrame with one row per issue found
        """
        return export_to_dataframe(results)

    def export_results_to_json(self, results: Dict, file_path: Optional[str] = None) -> str:
        """
        Export audit results to JSON

        Args:
            results: Audit results dictionary
            file_path: Optional path to save JSON file

        Returns:
            JSON string
        """
        return export_to_json(results, file_path)

    def export_results_to_html(self, results: Dict, file_path: str = "audit_report.html") -> str:
        """
        Export audit results to a beautiful HTML report

        Args:
            results: Audit results dictionary
            file_path: Path to save HTML file

        Returns:
            Path to saved HTML file
        """
        return export_to_html(results, file_path)

    def get_summary_stats(self, results: Dict) -> Dict:
        """
        Get high-level summary statistics from audit results

        Returns:
            Dictionary with summary statistics
        """
        return get_summary_stats(results)
