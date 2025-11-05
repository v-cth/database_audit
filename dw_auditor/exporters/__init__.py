"""
Export functionality for audit results

This module provides multiple export formats for database audit results with
enterprise-grade security, error handling, and best practices:

- JSON: Machine-readable format for integration
- DataFrame: Polars DataFrame for data analysis
- HTML: Professional, secure reports
- Run Summary: Aggregate reporting across tables

All exporters include:
- Input validation
- Comprehensive error handling
- Security hardening (XSS protection, path validation)
- Proper logging
- Type safety

See README.md for full documentation.
"""

from .dataframe_export import export_to_dataframe
from .json_export import export_to_json
from .html import export_to_html
from .run_summary_export import (
    export_run_summary_to_dataframe,
    export_run_summary_to_json,
    export_run_summary_to_html
)

# Export exceptions for error handling
from .exceptions import (
    ExporterError,
    InvalidResultsError,
    FileExportError,
    PathValidationError
)

# Export types for type hints
from .types import (
    AuditResultsDict,
    ColumnDataDict,
    IssueDict
)

__all__ = [
    # Export functions
    "export_to_dataframe",
    "export_to_json",
    "export_to_html",
    "export_run_summary_to_dataframe",
    "export_run_summary_to_json",
    "export_run_summary_to_html",
    # Exceptions
    "ExporterError",
    "InvalidResultsError",
    "FileExportError",
    "PathValidationError",
    # Types
    "AuditResultsDict",
    "ColumnDataDict",
    "IssueDict",
]

__version__ = "2.0.0"  # Major version bump due to security fixes
