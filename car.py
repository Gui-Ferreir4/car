# app.py
import streamlit as st
import pandas as pd
from datetime import timedelta
from io import StringIO

st.set_page_config(page_title="Análise Forscan Lite", layout="wide")
st.title("🔍 Análise Forscan Lite - Consumo e Desempenho")

# Dicionário com descrições das colunas
descricao_colunas = {
    "time(ms)": "Tempo desde o início da gravação (ms)",
    "ENGI_IDLE": "Motor em marcha lenta (1 = Sim, 0 = Não)",
    "IC_SPDMTR(km/h)": "Velocidade registrada no painel",
    "VSS(km/h)": "Velocidade do sensor de roda",
    "RPM(1/min)": "Rotações por minuto do motor",
    "ODOMETER(km)": "Odômetro total (km)",
    "TRIP_ODOM(km)": "Odômetro parcial (km percorridos na viagem)",
    "DSDRPM(1/min)": "RPM desejado pela ECU",
    "BOO_ABS": "Pedal do freio pressionado",
    "AF_RATIO(:1)": "Razão ar/combustível",
    "SHRTFT1(%)": "Correção de combustível em curto prazo",
    "LONGFT1(%)": "Correção de combustível em longo prazo",
    "FUELPW(ms)": "Tempo de injeção de combustível",
    "FUELLVL(%)": "Nível de combustível no tanque",
    "LOAD.OBDII(%)": "Carga do motor (via OBDII)",
    "ECT_GAUGE(Â°C)": "Temperatura do motor no painel",
    "IAT(Â°C)": "Temperatura do ar admitido",
    "O2S11_V(V)": "Tensão do sensor de oxigênio",
    "LMD_EGO1(:1)": "Leitura lambda estimada",
    "OPENLOOP": "Sistema de injeção em malha aberta (sem correção por sonda)",
    "MAP.OBDII(kPa)": "Pressão absoluta do coletor (OBDII)",
    "BARO(kPa)": "Pressão atmosférica",
    "TP.OBDII(%)": "Posição da borboleta do acelerador",
    "SPARKADV(Â°)": "Avanço da ignição",
    "VBAT_1(V)": "Voltagem da bateria",
    "AF_LEARN": "Aprendizado de mistura ar/combustível",
    "ECT(Â°C)": "Temperatura real do motor",
    "ECT.OBDII(Â°C)": "Temperatura via OBDII",
    "FUEL_CONSUM": "Combustível consumido acumulado",
    "FUEL_CORR(:1)": "Correção da mistura combustível",
    "Litres_Alcohol(L)": "Álcool consumido na viagem",
    "MAP(V)": "Pressão do coletor (em volts)",
    "MAP_V(V)": "Pressão do coletor (outro sensor, em volts)",
    "SPKDUR_1(ms)": "Duração da centelha - Cilindro 1",
    "SPKDUR_2(ms)": "Duração da centelha - Cilindro 2",
    "SPKDUR_3(ms)": "Duração da centelha - Cilindro 3",
    "SPKDUR_4(ms)": "Duração da centelha - Cilindro 4",
    "ENG_STATUS": "Status geral do motor",
    "LAMBDA_1": "Leitura da sonda lambda",
    "MIXCNT_STAT": "Status da mistura"
}

# Funções utilitárias
def converter_tempo(ms):
    try:
        segundos = int(ms) // 1000
        return str(timedelta(seconds=segundos))
    except:
        return "Inválido"

def processar_dados(df):
    df.columns = df.columns.str.strip().str.replace("\uFFFD", "", regex=True)

    if "time(ms)" not in df.columns:
        st.error(f"Coluna 'time(ms)' não encontrada. Colunas disponíveis: {df.columns.tolist()}")
        st.stop()
    df["TIME_CONVERTED"] = df["time(ms)"].apply(converter_tempo)

    if "ENGI_IDLE" not in df.columns:
        st.error(f"Coluna 'ENGI_IDLE' não encontrada. Colunas disponíveis: {df.columns.tolist()}")
        st.stop()

    # Mapeia "Sim"/"Não" para 1/0
    map_idle = {"Sim": 1, "Não": 0, "Nao": 0, "nao": 0, "não": 0}
    df["ENGI_IDLE"] = df["ENGI_IDLE"].map(map_idle).fillna(0).astype(int)
    df["ACTIVE"] = df["ENGI_IDLE"].apply(lambda x: 0 if x == 1 else 1)

    # Substitui "-" e strings vazias por NaN para todas as colunas numéricas conhecidas
    colunas_numericas = [col for col in df.columns if col in descricao_colunas]
    for col in colunas_numericas:
        df[col] = df[col].replace(["-", ""], pd.NA)
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

def calcular_distancia(df):
    if "TRIP_ODOM(km)" in df.columns:
        return round(df["TRIP_ODOM(km)"].max() - df["TRIP_ODOM(km)"].min(), 2)
    return None

def calcular_consumo(df):
    if "FUEL_CONSUM" in df.columns:
        return round(df["FUEL_CONSUM"].max() - df["FUEL_CONSUM"].min(), 2)
    elif "Litres_Alcohol(L)" in df.columns:
        return round(df["Litres_Alcohol(L)"].max() - df["Litres_Alcohol(L)"].min(), 2)
    return None

def calcular_kml(distancia, consumo):
    if distancia and consumo and consumo > 0:
        return round(distancia / consumo, 2)
    return None

def gerar_estatisticas(df, coluna, considerar_idle=False):
    # Converte coluna para numérico (pode ser redundante mas garante segurança)
    serie = pd.to_numeric(df[coluna], errors='coerce')

    stats = {
        "Indicador": coluna,
        "Descrição": descricao_colunas.get(coluna, "-")
    }

    geral = serie.dropna()
    stats["Min (Geral)"] = round(geral.min(), 2) if not geral.empty else "-"
    stats["Max (Geral)"] = round(geral.max(), 2) if not geral.empty else "-"
    stats["Média (Geral)"] = round(geral.mean(), 2) if not geral.empty else "-"

    if considerar_idle:
        idle = pd.to_numeric(df[df["ENGI_IDLE"] == 1][coluna], errors='coerce').dropna()
        ativo = pd.to_numeric(df[df["ENGI_IDLE"] == 0][coluna], errors='coerce').dropna()
        stats["Média (Marcha Lenta)"] = round(idle.mean(), 2) if not idle.empty else "-"
        stats["Média (Atividade)"] = round(ativo.mean(), 2) if not ativo.empty else "-"
    else:
        stats["Média (Marcha Lenta)"] = "-"
        stats["Média (Atividade)"] = "-"

    return stats

def avaliar_alertas(df):
    alertas = []

    if "LONGFT1(%)" in df.columns:
        media = df["LONGFT1(%)"].mean()
        if abs(media) > 10:
            alertas.append(f"⚠️ Correção de longo prazo elevada: {media:.2f}%")

    if "AF_RATIO(:1)" in df.columns:
        media = df["AF_RATIO(:1)"].mean()
        if media < 13 or media > 15.5:
            alertas.append(f"⚠️ Razão ar/combustível fora do ideal: {media:.2f}")

    if "FUELPW(ms)" in df.columns:
        media = df["FUELPW(ms)"].mean()
        if media > 5:
            alertas.append(f"⚠️ Tempo médio de injeção alto: {media:.2f} ms")

    if "OPENLOOP" in df.columns:
        openloop_pct = (df["OPENLOOP"] == "ON").mean() * 100
        if openloop_pct > 30:
            alertas.append(f"⚠️ {openloop_pct:.1f}% do tempo em OPENLOOP (modo rico)")

    return alertas

def gerar_relatorio_txt(df, df_stats, distancia, consumo, kml, alertas):
    buffer = StringIO()
    buffer.write("===== RELATÓRIO DE ANÁLISE - FORSCAN LITE =====\n\n")
    buffer.write("Resumo da Viagem:\n")
    buffer.write(f"- Distância percorrida: {distancia or 'N/A'} km\n")
    buffer.write(f"- Combustível consumido: {consumo or 'N/A'} L\n")
    buffer.write(f"- Consumo médio: {kml or 'N/A'} km/L\n\n")

    buffer.write("Alertas Detectados:\n")
    if alertas:
        for alerta in alertas:
            buffer.write(f"- {alerta}\n")
    else:
        buffer.write("- Nenhum alerta crítico identificado\n")
    buffer.write("\n")

    buffer.write("Estatísticas por Coluna:\n")
    for _, row in df_stats.iterrows():
        buffer.write(f"- {row['Indicador']} | {row['Descrição']}\n")
        buffer.write(f"   → Média Geral: {row['Média (Geral)']}\n")
        buffer.write(f"   → Média Marcha Lenta: {row['Média (Marcha Lenta)']}\n")
        buffer.write(f"   → Média Atividade: {row['Média (Atividade)']}\n")
        buffer.write(f"   → Mín: {row['Min (Geral)']}, Máx: {row['Max (Geral)']}\n\n")
    return buffer.getvalue()

# ================================ INTERFACE ================================

uploaded_file = st.file_uploader("📎 Selecione o arquivo CSV exportado do Forscan Lite", type=["csv"])

if uploaded_file:
    try:
        content = uploaded_file.read().decode("utf-8")
        df = pd.read_csv(StringIO(content), sep=";")
        st.success("✅ Arquivo carregado com sucesso!")

        df = processar_dados(df)

        st.subheader("📌 Resumo Geral da Viagem")
        distancia = calcular_distancia(df)
        consumo = calcular_consumo(df)
        kml = calcular_kml(distancia, consumo)

        col1, col2, col3 = st.columns(3)
        col1.metric("Distância (km)", distancia or "N/A")
        col2.metric("Consumo (L)", consumo or "N/A")
        col3.metric("Consumo Médio (km/L)", kml or "N/A")

        st.markdown("---")
        st.subheader("📊 Estatísticas Detalhadas por Coluna")

        tabela_final = []
        for col in df.columns:
            if col in ["ENGI_IDLE", "ACTIVE", "time(ms)", "TIME_CONVERTED"]:
                continue
            considerar_idle = col not in [
                "ODOMETER(km)", "TRIP_ODOM(km)", "FUELLVL(%)", "VBAT_1(V)", "ENG_STATUS",
                "AF_LEARN", "MIXCNT_STAT", "OPENLOOP", "time(ms)", "TIME_CONVERTED"
            ]
            tabela_final.append(gerar_estatisticas(df, col, considerar_idle))

        df_stats = pd.DataFrame(tabela_final)
        st.dataframe(df_stats, use_container_width=True)

        st.markdown("---")
        st.subheader("🚨 Alertas de Desempenho")
        alertas = avaliar_alertas(df)
        if alertas:
            for alerta in alertas:
                st.warning(alerta)
        else:
            st.success("✅ Nenhum alerta crítico identificado.")

        st.markdown("---")
        st.subheader("📄 Relatório Consolidado (.txt)")
        relatorio_txt = gerar_relatorio_txt(df, df_stats, distancia, consumo, kml, alertas)

        st.text_area("📋 Pré-visualização do relatório", relatorio_txt, height=400)
        st.download_button("📥 Baixar Relatório TXT", relatorio_txt, file_name="relatorio_forscan.txt", mime="text/plain")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
