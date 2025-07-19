EFICIENCIA_KM_LITRO = {"Gasolina": 12.0, "Etanol": 8.0}
from consumo import calcular_consumo_combustivel, calcular_distancia

def avaliar_alertas(df, combustivel):
    alertas = []

    if "LONGFT1(%)" in df.columns and abs(df["LONGFT1(%)"].mean()) > 10:
        alertas.append(f"⚠️ Correção de longo prazo elevada: {df['LONGFT1(%)'].mean():.2f}%")

    if "AF_RATIO(:1)" in df.columns:
        media = df["AF_RATIO(:1)"].mean()
        if media < 13 or media > 15.5:
            alertas.append(f"⚠️ Razão ar/combustível fora do ideal: {media:.2f}")

    if "FUELPW(ms)" in df.columns and df["FUELPW(ms)"].mean() > 5:
        alertas.append(f"⚠️ Tempo médio de injeção alto: {df['FUELPW(ms)'].mean():.2f} ms")

    if "OPENLOOP" in df.columns:
        pct = (df["OPENLOOP"] == "ON").mean() * 100
        if pct > 30:
            alertas.append(f"⚠️ {pct:.1f}% do tempo em OPENLOOP")

    consumo = calcular_consumo_combustivel(df)
    distancia = calcular_distancia(df)

    if consumo:
        alertas.append(f"ℹ️ Consumo estimado: {consumo:.2f} litros")

    if distancia and consumo and consumo > 0:
        kml = distancia / consumo
        esperado = EFICIENCIA_KM_LITRO.get(combustivel)
        if esperado and kml < esperado * 0.7:
            alertas.append(f"⚠️ Consumo alto detectado: {kml:.2f} km/l (esperado ~{esperado} km/l)")

    return alertas
