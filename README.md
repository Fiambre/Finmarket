# Finmarket

Librería Python para obtener datos financieros del mercado chileno desde Finmarket Live.

## Características

- Búsqueda de instrumentos financieros (acciones, índices, etc.)
- Datos históricos de precios (OHLCV)
- Múltiples períodos de tiempo (intradía hasta 10 años)
- Conversión a DataFrame de pandas
- Sin dependencias pesadas (solo `requests`)

## Instalación

```bash
pip install finmarket
```

Con soporte para pandas:

```bash
pip install finmarket[pandas]
```

### Instalación desde código fuente

```bash
git clone https://github.com/finmarket/finmarket-python.git
cd finmarket-python
pip install -e .
```

## Uso rápido

```python
from finmarket import FinmarketClient

# Crear cliente
client = FinmarketClient()

# Buscar instrumentos
results = client.search("ipsa")
print(results[0].name)        # IPSA
print(results[0].id_notation) # 3969

# Obtener datos históricos
chart = client.get_chart_data(id_notation=3969, time_span="1Y")
print(f"Total de registros: {len(chart.points)}")
```

## API Reference

### FinmarketClient

```python
client = FinmarketClient(timeout=30)
```

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `timeout` | int | 30 | Tiempo máximo de espera en segundos |

---

### search(query, market="chile")

Busca instrumentos financieros por nombre o símbolo.

```python
results = client.search("banco")
```

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `query` | str | - | Término de búsqueda |
| `market` | str | "chile" | Mercado a buscar |

**Retorna:** `List[SearchResult]`

#### SearchResult

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `id_notation` | int | ID único del instrumento |
| `name` | str | Nombre del instrumento |
| `symbol` | str \| None | Símbolo/ticker |
| `market` | str \| None | Mercado |
| `type` | str \| None | Tipo (Acciones, Indices, etc.) |
| `raw_data` | dict \| None | Datos crudos de la API |

**Ejemplo:**

```python
results = client.search("copec")

for r in results:
    print(f"{r.symbol}: {r.name} (ID: {r.id_notation})")
```

---

### get_chart_data(id_notation, time_span="1Y", quality="RLT", volume=False)

Obtiene datos históricos de precios.

```python
chart = client.get_chart_data(id_notation=3969, time_span="1Y")
```

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `id_notation` | int | - | ID del instrumento |
| `time_span` | str | "1Y" | Período de tiempo |
| `quality` | str | "RLT" | Calidad de datos |
| `volume` | bool | False | Incluir volumen |

**Períodos disponibles (`time_span`):**

| Valor | Descripción |
|-------|-------------|
| `1D` | 1 día (intradía) |
| `5D` | 5 días |
| `1M` | 1 mes |
| `3M` | 3 meses |
| `6M` | 6 meses |
| `1Y` | 1 año |
| `3Y` | 3 años |
| `5Y` | 5 años |
| `10Y` | 10 años |
| `MAX` | Máximo disponible |

**Retorna:** `ChartData`

#### ChartData

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `id_notation` | int | ID del instrumento |
| `time_span` | str | Período solicitado |
| `points` | List[ChartPoint] | Lista de puntos de datos |

**Métodos:**

- `to_dataframe()` → Convierte a DataFrame de pandas (requiere pandas instalado)

#### ChartPoint

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `date` | datetime | Fecha y hora |
| `open` | float | Precio de apertura |
| `high` | float | Precio máximo |
| `low` | float | Precio mínimo |
| `close` | float | Precio de cierre |
| `volume` | int | Volumen |
| `pctrel` | float | Variación porcentual |
| `decimals` | int | Decimales de precisión |

**Ejemplo:**

```python
chart = client.get_chart_data(3969, time_span="1M")

# Iterar sobre los puntos
for point in chart.points[-5:]:
    print(f"{point.date.strftime('%Y-%m-%d')}: {point.close}")

# Convertir a DataFrame
df = chart.to_dataframe()
print(df.tail())
```

---

### Métodos de conveniencia

```python
# Equivalente a get_chart_data(id, time_span="1D")
client.get_intraday(id_notation)

# Equivalente a get_chart_data(id, time_span="5D")
client.get_weekly(id_notation)

# Equivalente a get_chart_data(id, time_span="1M")
client.get_monthly(id_notation)

# Equivalente a get_chart_data(id, time_span="1Y")
client.get_yearly(id_notation)
```

## Ejemplos

### Obtener el precio actual del IPSA

```python
from finmarket import FinmarketClient

client = FinmarketClient()

# Buscar IPSA
results = client.search("ipsa")
ipsa = next(r for r in results if r.symbol == "IPSA")

# Obtener último precio
chart = client.get_intraday(ipsa.id_notation)
if chart.points:
    ultimo = chart.points[-1]
    print(f"IPSA: {ultimo.close} ({ultimo.pctrel:+.2f}%)")
```

### Análisis con pandas

```python
from finmarket import FinmarketClient

client = FinmarketClient()

# Obtener datos de 1 año
chart = client.get_chart_data(id_notation=3969, time_span="1Y")
df = chart.to_dataframe()

# Estadísticas básicas
print(df['close'].describe())

# Rendimiento total
rendimiento = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
print(f"Rendimiento anual: {rendimiento:.2f}%")

# Volatilidad
volatilidad = df['close'].pct_change().std() * (252 ** 0.5) * 100
print(f"Volatilidad anualizada: {volatilidad:.2f}%")
```

### Comparar múltiples instrumentos

```python
from finmarket import FinmarketClient

client = FinmarketClient()

# Lista de símbolos a buscar
simbolos = ["IPSA", "COPEC", "BANCO DE CHILE"]

for simbolo in simbolos:
    results = client.search(simbolo)
    if results:
        r = results[0]
        chart = client.get_yearly(r.id_notation)
        if chart.points:
            inicio = chart.points[0].close
            fin = chart.points[-1].close
            cambio = (fin / inicio - 1) * 100
            print(f"{r.symbol}: {cambio:+.2f}%")
```

### Exportar a CSV

```python
from finmarket import FinmarketClient

client = FinmarketClient()
chart = client.get_chart_data(id_notation=3969, time_span="1Y")

df = chart.to_dataframe()
df.to_csv("ipsa_historico.csv", index=False)
```

## Manejo de errores

```python
from finmarket import FinmarketClient
import requests

client = FinmarketClient()

try:
    results = client.search("ipsa")
except requests.exceptions.Timeout:
    print("La solicitud tardó demasiado")
except requests.exceptions.HTTPError as e:
    print(f"Error HTTP: {e}")
except requests.exceptions.RequestException as e:
    print(f"Error de conexión: {e}")
```

## Limitaciones

- Los datos provienen de Finmarket Live y están sujetos a disponibilidad del servicio
- No incluye datos en tiempo real, solo datos diferidos/históricos
- Solo mercado chileno disponible actualmente

## Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles.
