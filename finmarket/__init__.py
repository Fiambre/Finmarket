"""
Finmarket - Librería para obtener datos financieros de Finmarket Live
"""

from .client import FinmarketClient
from .models import SearchResult, ChartData, ChartPoint

__version__ = "1.0.0"
__all__ = ["FinmarketClient", "SearchResult", "ChartData", "ChartPoint"]
