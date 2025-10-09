"""
Data Warehouse Table Auditor - Secure Polars Edition
High-performance data quality checks with security best practices
"""

from .core.auditor import SecureTableAuditor
from .core.config import AuditConfig

__version__ = "1.0.0"
__all__ = ["SecureTableAuditor", "AuditConfig"]
