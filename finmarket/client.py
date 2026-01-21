"""
Cliente principal para la API de Finmarket
"""

import re
import requests
from datetime import datetime, date
from typing import List, Optional, Literal

from .models import SearchResult, ChartData, ChartPoint


TimeSpan = Literal["1D", "5D", "1M", "3M", "6M", "1Y", "3Y", "5Y", "10Y", "MAX"]


class FinmarketClient:
    """
    Cliente para obtener datos financieros de Finmarket Live.

    Ejemplo de uso:
        client = FinmarketClient()

        # Buscar un instrumento
        results = client.search("ipsa")

        # Obtener datos del gráfico
        chart = client.get_chart_data(id_notation=4039, time_span="1Y")
    """

    BASE_URL = "https://bancobci.finmarketslive.cl/www"

    def __init__(self, timeout: int = 30):
        """
        Inicializa el cliente de Finmarket.

        Args:
            timeout: Tiempo máximo de espera para las peticiones (segundos)
        """
        self.timeout = timeout
        self.session = requests.Session()
        self._setup_session()

    def _setup_session(self):
        """Configura los headers por defecto de la sesión"""
        self.session.headers.update({
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "en-US,en;q=0.9,es;q=0.8",
            "referer": f"{self.BASE_URL}/index.html",
            "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        })

    def search(self, query: str, market: str = "chile") -> List[SearchResult]:
        """
        Busca instrumentos financieros por nombre o símbolo.

        Args:
            query: Término de búsqueda (ej: "ipsa", "banco", "copec")
            market: Mercado a buscar (default: "chile")

        Returns:
            Lista de resultados de búsqueda

        Ejemplo:
            results = client.search("ipsa")
            for r in results:
                print(f"{r.name} - ID: {r.id_notation}")
        """
        url = f"{self.BASE_URL}/global/buscador.html"
        params = {
            "SEARCH_VALUE": query,
            "MERCADO": market
        }

        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        results = []

        if isinstance(data, list):
            for item in data:
                result = SearchResult(
                    id_notation=int(item.get("ID_NOTATION") or item.get("id_notation") or item.get("id") or 0),
                    name=item.get("NAME") or item.get("name") or "",
                    symbol=item.get("SYMBOL") or item.get("symbol"),
                    market=item.get("MARKET") or item.get("market"),
                    type=item.get("TYPE") or item.get("type"),
                    raw_data=item
                )
                results.append(result)

        return results

    def get_chart_data(
        self,
        id_notation: int,
        time_span: TimeSpan = "1Y",
        quality: str = "RLT",
        volume: bool = False
    ) -> ChartData:
        """
        Obtiene datos históricos de precios para un instrumento.

        Args:
            id_notation: ID del instrumento (obtenido de search())
            time_span: Período de tiempo ("1D", "5D", "1M", "3M", "6M", "1Y", "3Y", "5Y", "10Y", "MAX")
            quality: Calidad de los datos (default: "RLT")
            volume: Incluir datos de volumen (default: False)

        Returns:
            ChartData con los puntos de datos históricos

        Ejemplo:
            chart = client.get_chart_data(4039, time_span="1Y")
            for point in chart.points:
                print(f"{point.date}: {point.close}")
        """
        url = f"{self.BASE_URL}/chart/datachart.html"
        params = {
            "ID_NOTATION": id_notation,
            "QUALITY": quality,
            "VOLUME": str(volume).lower()
        }

        # Si es MAX, usar parámetros de fecha en lugar de TIME_SPAN
        if time_span == "MAX":
            params["DATEINI"] = "1900-01-01"
            params["DATEFIN"] = date.today().strftime("%Y-%m-%d")
        else:
            params["TIME_SPAN"] = time_span

        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()

        points = self._parse_chart_response(response.text)

        return ChartData(
            id_notation=id_notation,
            time_span=time_span,
            points=points
        )

    def _parse_chart_response(self, text: str) -> List[ChartPoint]:
        """
        Parsea la respuesta del endpoint datachart que viene en formato JavaScript.

        El formato es: [{date:new Date(2026, 0, 16, 12, 14, 56), close:0.16, ...}, ...]
        """
        points = []

        # Patrón mejorado para extraer cada objeto del array JavaScript
        # Busca desde { hasta el siguiente }, considerando que puede haber new Date(...) dentro
        object_pattern = r'\{date:new Date\(([^)]+)\)([^}]*)\}'
        objects = re.findall(object_pattern, text)

        for date_part, rest_part in objects:
            point_data = {}

            # Parsear la fecha: year, month, day, hour, minute, second
            date_values = [int(x.strip()) for x in date_part.split(',')]
            if len(date_values) >= 3:
                year, month, day = date_values[0], date_values[1], date_values[2]
                hour = date_values[3] if len(date_values) > 3 else 0
                minute = date_values[4] if len(date_values) > 4 else 0
                second = date_values[5] if len(date_values) > 5 else 0
                # JavaScript los meses son 0-indexed, Python no
                point_data['date'] = datetime(year, month + 1, day, hour, minute, second)
            else:
                continue

            # Extraer valores numéricos del resto del objeto
            full_obj = f"{{date:new Date({date_part}){rest_part}}}"
            for field in ['close', 'high', 'low', 'open', 'volume', 'pctrel', 'decimals']:
                match = re.search(rf'{field}:([-\d.]+)', full_obj)
                if match:
                    value = match.group(1)
                    if field in ['volume', 'decimals']:
                        point_data[field] = int(float(value))
                    else:
                        point_data[field] = float(value)

            if 'date' in point_data and 'close' in point_data:
                points.append(ChartPoint(
                    date=point_data['date'],
                    open=point_data.get('open', 0.0),
                    high=point_data.get('high', 0.0),
                    low=point_data.get('low', 0.0),
                    close=point_data['close'],
                    volume=point_data.get('volume', 0),
                    pctrel=point_data.get('pctrel', 0.0),
                    decimals=point_data.get('decimals', 2)
                ))

        return points

    def get_intraday(self, id_notation: int) -> ChartData:
        """
        Obtiene datos intradía (1 día) para un instrumento.

        Args:
            id_notation: ID del instrumento

        Returns:
            ChartData con los puntos de datos del día
        """
        return self.get_chart_data(id_notation, time_span="1D")

    def get_weekly(self, id_notation: int) -> ChartData:
        """
        Obtiene datos de la última semana para un instrumento.

        Args:
            id_notation: ID del instrumento

        Returns:
            ChartData con los puntos de datos de la semana
        """
        return self.get_chart_data(id_notation, time_span="5D")

    def get_monthly(self, id_notation: int) -> ChartData:
        """
        Obtiene datos del último mes para un instrumento.

        Args:
            id_notation: ID del instrumento

        Returns:
            ChartData con los puntos de datos del mes
        """
        return self.get_chart_data(id_notation, time_span="1M")

    def get_yearly(self, id_notation: int) -> ChartData:
        """
        Obtiene datos del último año para un instrumento.

        Args:
            id_notation: ID del instrumento

        Returns:
            ChartData con los puntos de datos del año
        """
        return self.get_chart_data(id_notation, time_span="1Y")
