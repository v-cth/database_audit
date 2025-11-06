"""
Atomic insights - reusable insight components that work across data types
"""

from .top_values import TopValuesInsight
from .quantiles import QuantilesInsight
from .length_stats import LengthStatsInsight

__all__ = [
    'TopValuesInsight',
    'QuantilesInsight',
    'LengthStatsInsight',
]
