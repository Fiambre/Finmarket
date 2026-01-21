"""
Tests para el cliente de Finmarket
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from finmarket import FinmarketClient
from finmarket.models import SearchResult, ChartData, ChartPoint


class TestFinmarketClientSearch:
    """Tests para el método search"""

    @patch('finmarket.client.requests.Session.get')
    def test_search_ipsa(self, mock_get):
        """Test búsqueda de IPSA"""
        # Mock de la respuesta
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "ID_NOTATION": 3969,
                "NAME": "IPSA",
                "SYMBOL": "IPSA",
                "MARKET": "Chile",
                "TYPE": "Index"
            }
        ]
        mock_get.return_value = mock_response

        client = FinmarketClient()
        results = client.search("ipsa")

        assert len(results) == 1
        assert results[0].id_notation == 3969
        assert results[0].name == "IPSA"
        assert results[0].symbol == "IPSA"

    @patch('finmarket.client.requests.Session.get')
    def test_search_empty_results(self, mock_get):
        """Test búsqueda sin resultados"""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = FinmarketClient()
        results = client.search("nonexistent")

        assert len(results) == 0

    @patch('finmarket.client.requests.Session.get')
    def test_search_with_alternative_keys(self, mock_get):
        """Test búsqueda con claves alternativas en la respuesta"""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "id_notation": 4039,
                "name": "ASSD",
                "symbol": "ASSD",
                "market": "Chile",
                "type": "Stock"
            }
        ]
        mock_get.return_value = mock_response

        client = FinmarketClient()
        results = client.search("assd")

        assert len(results) == 1
        assert results[0].id_notation == 4039


class TestFinmarketClientChartData:
    """Tests para el método get_chart_data"""

    @patch('finmarket.client.requests.Session.get')
    def test_get_chart_data_success(self, mock_get):
        """Test obtención de datos de gráfico exitosa"""
        chart_response = "[{date:new Date(2025, 0, 21, 9, 0, 0),close:0.24,high:0.24,low:0.24,open:0.24,volume:12701745,pctrel:0.00,decimals:2}]"
        
        mock_response = Mock()
        mock_response.text = chart_response
        mock_get.return_value = mock_response

        client = FinmarketClient()
        chart = client.get_chart_data(id_notation=4039, time_span="1Y")

        assert isinstance(chart, ChartData)
        assert chart.id_notation == 4039
        assert chart.time_span == "1Y"
        assert len(chart.points) == 1
        assert chart.points[0].close == 0.24
        assert chart.points[0].volume == 12701745

    @patch('finmarket.client.requests.Session.get')
    def test_get_chart_data_multiple_points(self, mock_get):
        """Test obtención de múltiples puntos de datos"""
        chart_response = """[
            {date:new Date(2025, 0, 21, 9, 0, 0),close:0.24,high:0.24,low:0.24,open:0.24,volume:12701745,pctrel:0.00,decimals:2},
            {date:new Date(2025, 0, 22, 9, 0, 0),close:0.25,high:0.25,low:0.24,open:0.24,volume:28054091,pctrel:4.17,decimals:2}
        ]"""
        
        mock_response = Mock()
        mock_response.text = chart_response
        mock_get.return_value = mock_response

        client = FinmarketClient()
        chart = client.get_chart_data(id_notation=4039, time_span="1M")

        assert len(chart.points) == 2
        assert chart.points[0].close == 0.24
        assert chart.points[1].close == 0.25
        assert chart.points[1].pctrel == 4.17

    @patch('finmarket.client.requests.Session.get')
    def test_get_chart_data_empty(self, mock_get):
        """Test obtención de datos vacíos"""
        mock_response = Mock()
        mock_response.text = "[]"
        mock_get.return_value = mock_response

        client = FinmarketClient()
        chart = client.get_chart_data(id_notation=9999)

        assert len(chart.points) == 0

    @patch('finmarket.client.requests.Session.get')
    def test_get_chart_data_with_volume_parameter(self, mock_get):
        """Test parámetro volume=True"""
        mock_response = Mock()
        mock_response.text = "[]"
        mock_get.return_value = mock_response

        client = FinmarketClient()
        client.get_chart_data(id_notation=4039, volume=True)

        # Verificar que el parámetro se envió correctamente
        call_args = mock_get.call_args
        assert call_args[1]['params']['VOLUME'] == 'true'


class TestChartPointParsing:
    """Tests para el parsing de puntos de datos"""

    @patch('finmarket.client.requests.Session.get')
    def test_parse_chart_response_date_parsing(self, mock_get):
        """Test parsing correcto de fechas"""
        # Nota: JavaScript usa meses 0-indexed, Python usa 1-indexed
        chart_response = "[{date:new Date(2025, 0, 21, 9, 30, 45),close:0.24,high:0.24,low:0.24,open:0.24,volume:12701745,pctrel:0.00,decimals:2}]"
        
        mock_response = Mock()
        mock_response.text = chart_response
        mock_get.return_value = mock_response

        client = FinmarketClient()
        chart = client.get_chart_data(id_notation=4039)

        point = chart.points[0]
        assert point.date == datetime(2025, 1, 21, 9, 30, 45)

    @patch('finmarket.client.requests.Session.get')
    def test_parse_chart_response_missing_fields(self, mock_get):
        """Test parsing con campos faltantes (usa valores por defecto)"""
        chart_response = "[{date:new Date(2025, 0, 21, 9, 0, 0),close:0.24,decimals:2}]"
        
        mock_response = Mock()
        mock_response.text = chart_response
        mock_get.return_value = mock_response

        client = FinmarketClient()
        chart = client.get_chart_data(id_notation=4039)

        point = chart.points[0]
        assert point.close == 0.24
        assert point.open == 0.0  # Default
        assert point.high == 0.0  # Default
        assert point.low == 0.0   # Default
        assert point.volume == 0  # Default
        assert point.pctrel == 0.0  # Default

    @patch('finmarket.client.requests.Session.get')
    def test_parse_chart_response_negative_values(self, mock_get):
        """Test parsing de valores negativos"""
        chart_response = "[{date:new Date(2025, 0, 21, 9, 0, 0),close:0.24,high:0.25,low:0.23,open:0.24,volume:12701745,pctrel:-0.83,decimals:2}]"
        
        mock_response = Mock()
        mock_response.text = chart_response
        mock_get.return_value = mock_response

        client = FinmarketClient()
        chart = client.get_chart_data(id_notation=4039)

        point = chart.points[0]
        assert point.pctrel == -0.83
        assert point.close == 0.24


class TestClientInitialization:
    """Tests para la inicialización del cliente"""

    def test_client_default_timeout(self):
        """Test timeout por defecto"""
        client = FinmarketClient()
        assert client.timeout == 30

    def test_client_custom_timeout(self):
        """Test timeout personalizado"""
        client = FinmarketClient(timeout=60)
        assert client.timeout == 60

    def test_client_headers_setup(self):
        """Test que los headers se configuran correctamente"""
        client = FinmarketClient()
        headers = client.session.headers
        
        assert "user-agent" in headers
        assert "x-requested-with" in headers
        assert headers["x-requested-with"] == "XMLHttpRequest"
        assert "Chrome" in headers["user-agent"]


class TestConvenientMethods:
    """Tests para los métodos convenientes"""

    @patch('finmarket.client.FinmarketClient.get_chart_data')
    def test_get_intraday(self, mock_get_chart):
        """Test método get_intraday"""
        mock_chart = Mock()
        mock_get_chart.return_value = mock_chart

        client = FinmarketClient()
        result = client.get_intraday(4039)

        mock_get_chart.assert_called_once_with(4039, time_span="1D")
        assert result == mock_chart

    @patch('finmarket.client.FinmarketClient.get_chart_data')
    def test_get_weekly(self, mock_get_chart):
        """Test método get_weekly"""
        mock_chart = Mock()
        mock_get_chart.return_value = mock_chart

        client = FinmarketClient()
        result = client.get_weekly(4039)

        mock_get_chart.assert_called_once_with(4039, time_span="5D")
        assert result == mock_chart

    @patch('finmarket.client.FinmarketClient.get_chart_data')
    def test_get_monthly(self, mock_get_chart):
        """Test método get_monthly"""
        mock_chart = Mock()
        mock_get_chart.return_value = mock_chart

        client = FinmarketClient()
        result = client.get_monthly(4039)

        mock_get_chart.assert_called_once_with(4039, time_span="1M")
        assert result == mock_chart

    @patch('finmarket.client.FinmarketClient.get_chart_data')
    def test_get_yearly(self, mock_get_chart):
        """Test método get_yearly"""
        mock_chart = Mock()
        mock_get_chart.return_value = mock_chart

        client = FinmarketClient()
        result = client.get_yearly(4039)

        mock_get_chart.assert_called_once_with(4039, time_span="1Y")
        assert result == mock_chart


class TestChartDataMethods:
    """Tests para métodos de ChartData"""

    def test_chart_data_to_dataframe_with_pandas(self):
        """Test conversión a DataFrame con pandas"""
        point = ChartPoint(
            date=datetime(2025, 1, 21),
            open=0.24,
            high=0.25,
            low=0.23,
            close=0.24,
            volume=12701745,
            pctrel=0.0
        )
        chart = ChartData(id_notation=4039, time_span="1Y", points=[point])

        try:
            import pandas
            result = chart.to_dataframe()
            # Verificar que el DataFrame tiene el contenido correcto
            assert len(result) == 1
            assert result.iloc[0]['close'] == 0.24
            assert result.iloc[0]['volume'] == 12701745
        except ImportError:
            pytest.skip("pandas no está instalado")

    def test_chart_data_to_dataframe_multiple_points(self):
        """Test conversión a DataFrame con múltiples puntos"""
        points = [
            ChartPoint(
                date=datetime(2025, 1, 21),
                open=0.24,
                high=0.25,
                low=0.23,
                close=0.24,
                volume=12701745,
                pctrel=0.0
            ),
            ChartPoint(
                date=datetime(2025, 1, 22),
                open=0.24,
                high=0.26,
                low=0.24,
                close=0.25,
                volume=28054091,
                pctrel=4.17
            )
        ]
        chart = ChartData(id_notation=4039, time_span="1Y", points=points)

        try:
            import pandas
            result = chart.to_dataframe()
            assert len(result) == 2
            assert result.iloc[0]['close'] == 0.24
            assert result.iloc[1]['close'] == 0.25
        except ImportError:
            pytest.skip("pandas no está instalado")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
