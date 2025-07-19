import pandas as pd
from descricao_colunas import descricao_colunas

def valores_ideais_expandido(tipo_combustivel):
    gasolina = tipo_combustivel.lower() == 'gasolina'
    return {
        'RPM': (750, 900) if gasolina else (850, 1000),
        'MAF(g/s)': (2.0, 4.0) if gasolina else (2.5, 4.5),
        'MAP(kPa)': (25, 40),
        'ECT(°C)': (88, 104),
        'IAT(°C)': (10, 50),
        'IGNADV(°)': (5, 20),
        'LTFT(%)': (-10, 10),
        'STFT(%)': (-10, 10),
        'SPEED(km/h)': (0, 0),
        'LOAD(%)': (15, 35),
        'THROTTLE(%)': (10, 20),
        'O2S_V_B1S1(V)': (0.1, 0.9),
        'O2S_V_B1S2(V)': (0.4, 0.6),
        'FUELLVL(%)': (0, 100),
        'FUELSYS1': ('Closed Loop',),
        'OPENLOOP': ('OFF',),
        'ENGI_IDLE': ('Sim',),
        'consumo_litros': (0, 20),
    }

def gerar_estatisticas_refinadas_expandido(df, tipo_combustivel):
    limites = valores_ideais_expandido(tipo_combustivel)
    tabela_final = []
    ignorar = ["ENGI_IDLE", "ACTIVE", "time(ms)", "TIME_CONVERTED"]

    for col in df.columns:
        if col in ignorar:
            continue

        stats = {
            "Indicador": col,
            "Descrição": descricao_colunas.get(col, "-"),
            "Valor Ideal": limites.get(col, "-"),
            "Min": "-", "Máx": "-", "Média": "-",
            "Média Marcha Lenta": "-", "Média Atividade": "-"
        }

        serie = pd.to_numeric(df[col], errors='coerce').dropna()
        if serie.empty:
            tabela_final.append(stats)
            continue

        stats["Min"] = round(serie.min(), 2)
        stats["Máx"] = round(serie.max(), 2)
        stats["Média"] = round(serie.mean(), 2)

        if "ENGI_IDLE" in df.columns:
            stats["Média Marcha Lenta"] = round(df[df["ENGI_IDLE"] == 1][col].mean(), 2)
            stats["Média Atividade"] = round(df[df["ENGI_IDLE"] == 0][col].mean(), 2)

        tabela_final.append(stats)

    return tabela_final
