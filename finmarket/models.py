"""
Modelos de datos para Finmarket
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class SearchResult:
    """Resultado de búsqueda de un instrumento financiero"""
    id_notation: int
    name: str
    symbol: Optional[str] = None
    market: Optional[str] = None
    type: Optional[str] = None
    raw_data: Optional[dict] = None


@dataclass
class ChartPoint:
    """Punto de datos en un gráfico"""
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    pctrel: float
    decimals: int = 2


@dataclass
class ChartData:
    """Datos de gráfico para un instrumento"""
    id_notation: int
    time_span: str
    points: List[ChartPoint]

    def to_dataframe(self):
        """Convierte los datos a un DataFrame de pandas"""
        try:
            import pandas as pd
            data = [
                {
                    "date": p.date,
                    "open": p.open,
                    "high": p.high,
                    "low": p.low,
                    "close": p.close,
                    "volume": p.volume,
                    "pctrel": p.pctrel
                }
                for p in self.points
            ]
            return pd.DataFrame(data)
        except ImportError:
            raise ImportError("pandas es requerido para usar to_dataframe(). Instálalo con: pip install pandas")
