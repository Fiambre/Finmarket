"""
Ejemplo de uso de la librería Finmarket
"""

from finmarket import FinmarketClient


def main():
    # Crear cliente
    client = FinmarketClient()

    # 1. Buscar un instrumento
    print("=" * 50)
    print("Buscando 'ipsa'...")
    print("=" * 50)

    results = client.search("ipsa")
    for result in results:
        print(f"  Nombre: {result.name}")
        print(f"  ID Notation: {result.id_notation}")
        print(f"  Símbolo: {result.symbol}")
        print(f"  Mercado: {result.market}")
        print("-" * 30)

    # 2. Obtener datos históricos (1 año)
    print("\n" + "=" * 50)
    print("Obteniendo datos históricos (1 año) para ID 4039...")
    print("=" * 50)

    chart = client.get_chart_data(id_notation=4039, time_span="1Y")
    print(f"  Total de puntos: {len(chart.points)}")

    if chart.points:
        print(f"\n  Últimos 5 registros:")
        for point in chart.points[-5:]:
            print(f"    {point.date}: Open={point.open}, High={point.high}, Low={point.low}, Close={point.close}")

    # 3. Obtener datos intradía
    print("\n" + "=" * 50)
    print("Obteniendo datos intradía para ID 4039...")
    print("=" * 50)

    intraday = client.get_intraday(id_notation=4039)
    print(f"  Total de puntos: {len(intraday.points)}")

    if intraday.points:
        print(f"\n  Primeros 3 registros:")
        for point in intraday.points[:3]:
            print(f"    {point.date}: Close={point.close}, Volume={point.volume}, %Rel={point.pctrel}")

    # 4. Convertir a DataFrame (requiere pandas)
    print("\n" + "=" * 50)
    print("Convirtiendo a DataFrame...")
    print("=" * 50)

    try:
        df = chart.to_dataframe()
        print(df.head())
        print(f"\n  Estadísticas:")
        print(df[['close']].describe())
    except ImportError as e:
        print(f"  {e}")


if __name__ == "__main__":
    main()
