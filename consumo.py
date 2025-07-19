VOLUME_TANQUE = 55.0

def calcular_consumo_combustivel(df):
    if "FUELLVL(%)" not in df.columns:
        return None

    df_idle = df[df["ENGI_IDLE"] == 1]
    if df_idle.empty:
        return None

    tempo_total = df_idle["time(ms)"].max() - df_idle["time(ms)"].min()
    inicio = df_idle[df_idle["time(ms)"] <= df_idle["time(ms)"].min() + 0.05 * tempo_total]
    fim = df_idle[df_idle["time(ms)"] >= df_idle["time(ms)"].max() - 0.05 * tempo_total]

    consumo_pct = inicio["FUELLVL(%)"].mean() - fim["FUELLVL(%)"].mean()
    if consumo_pct < 0:
        consumo_pct = 0

    return round(consumo_pct / 100.0 * VOLUME_TANQUE, 2)

def calcular_distancia(df):
    if "TRIP_ODOM(km)" in df.columns:
        return round(df["TRIP_ODOM(km)"].max() - df["TRIP_ODOM(km)"].min(), 2)
    return None

def calcular_kml(distancia, consumo):
    if distancia and consumo and consumo > 0:
        return round(distancia / consumo, 2)
    return None
