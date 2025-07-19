import pandas as pd
from datetime import timedelta
import streamlit as st

def converter_tempo(ms):
    try:
        segundos = int(ms) // 1000
        return str(timedelta(seconds=segundos))
    except:
        return "Inválido"

def processar_dados(df):
    df.columns = df.columns.str.strip().str.replace("\uFFFD", "", regex=True)

    if "time(ms)" not in df.columns or "ENGI_IDLE" not in df.columns:
        st.error("Colunas obrigatórias não encontradas.")
        st.stop()

    # Converte tempo
    df["TIME_CONVERTED"] = df["time(ms)"].apply(converter_tempo)

    # Normaliza valores de marcha lenta
    df["ENGI_IDLE"] = df["ENGI_IDLE"].replace({
        "Sim": 1, "Não": 0, "Nao": 0, "nao": 0, "não": 0
    }).fillna(0).astype(int)

    # Marca registros ativos
    df["ACTIVE"] = df["ENGI_IDLE"].apply(lambda x: 0 if x == 1 else 1)

    # Limpa colunas numéricas com traços e converte
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].replace("-", pd.NA)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Remove linhas com todos os valores ausentes (exceto time)
    df.dropna(axis=0, how='all', subset=[col for col in df.columns if col not in ["TIME_CONVERTED", "time(ms)"]], inplace=True)

    return df

