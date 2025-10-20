"""
Mixin for exporting audit results in various formats.
"""

from typing import Dict, Optional
import polars as pl

from ..exporters.dataframe_export import export_to_dataframe
from ..exporters.html_export import export_to_html
from ..exporters.json_export import export_to_json
from ..exporters.summary_export import export_column_summary_to_dataframe
from ..utils.output import get_summary_stats


class AuditorExporterMixin:
    """Mixin class providing methods to export audit results."""

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

    def export_column_summary_to_dataframe(self, results: Dict) -> pl.DataFrame:
        """
        Export column summary to a Polars DataFrame

        Args:
            results: Audit results dictionary

        Returns:
            DataFrame with one row per column with basic metrics (null count, null %, distinct count)
        """
        return export_column_summary_to_dataframe(results)
