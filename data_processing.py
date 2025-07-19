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

    df["TIME_CONVERTED"] = df["time(ms)"].apply(converter_tempo)
    df["ENGI_IDLE"] = df["ENGI_IDLE"].replace({
        "Sim": 1, "Não": 0, "Nao": 0, "nao": 0, "não": 0
    }).fillna(0).astype(int)
    df["ACTIVE"] = df["ENGI_IDLE"].apply(lambda x: 0 if x == 1 else 1)

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = pd.to_numeric(df[col].replace("-", pd.NA), errors="coerce")

    return df
