# app.py
import streamlit as st
import pandas as pd
from datetime import timedelta
from io import StringIO

st.set_page_config(page_title="Análise Forscan Lite", layout="wide")
st.title("🔍 Análise Forscan Lite - Consumo e Desempenho")

# Funções utilitárias
def converter_tempo(ms):
    try:
        segundos = int(ms) // 1000
        return str(timedelta(seconds=segundos))
    except:
        return "Inválido"

O ChatGPT disse:
Perfeito. O erro que você está recebendo:

scss
Copiar
Editar
unsupported operand type(s) for -: 'str' and 'str'
significa que o código está tentando subtrair strings, não números. Isso ocorre provavelmente nas funções:

python
Copiar
Editar
def calcular_distancia(df):
    if "TRIP_ODOM(km)" in df.columns:
        return round(df["TRIP_ODOM(km)"].max() - df["TRIP_ODOM(km)"].min(), 2)
ou

python
Copiar
Editar
def calcular_consumo(df):
    if "FUEL_CONSUM" in df.columns:
        return round(df["FUEL_CONSUM"].max() - df["FUEL_CONSUM"].min(), 2)

def processar_dados(df):
    df.columns = df.columns.str.strip().str.replace("\uFFFD", "", regex=True)

    if "time(ms)" not in df.columns:
        st.error(f"Coluna 'time(ms)' não encontrada. Colunas disponíveis: {df.columns.tolist()}")
        st.stop()
    df["TIME_CONVERTED"] = df["time(ms)"].apply(converter_tempo)

    if "ENGI_IDLE" not in df.columns:
        st.error(f"Coluna 'ENGI_IDLE' não encontrada. Colunas disponíveis: {df.columns.tolist()}")
        st.stop()

    # Corrige valores de ENGI_IDLE
    map_idle = {"Sim": 1, "Não": 0, "Nao": 0, "nao": 0, "não": 0}
    df["ENGI_IDLE"] = df["ENGI_IDLE"].map(map_idle).fillna(0).astype(int)
    df["ACTIVE"] = df["ENGI_IDLE"].apply(lambda x: 0 if x == 1 else 1)

    # Conversões numéricas para evitar erro de subtração de strings
    colunas_numericas = [
        "TRIP_ODOM(km)", "FUEL_CONSUM", "Litres_Alcohol(L)", "LONGFT1(%)", 
        "AF_RATIO(:1)", "FUELPW(ms)", "VBAT_1(V)", "FUELLVL(%)"
    ]
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df
Isso garante que as colunas usadas em subtrações e médias sejam tratadas como números (float64) — evitando o erro de subtração de strings.

✅ Depois disso, rode novamente. Se der erro novo, me avise. Caso rode corretamente, posso te ajudar a:
identificar as viagens no log

calcular consumo por trecho

refinar alertas e gerar insights mais inteligentes

Tudo diretamente com base na sua planilha Forscan.







Você disse:
lembre-se que nas linhas iniciais, algumas colunas podem estar preenchidas com -


O ChatGPT disse:
Você está dando feedback sobre uma nova versão do ChatGPT.
Qual resposta você prefere? Elas podem demorar um pouco para carregar.
ChatGPT
Resposta 1
Ótimo lembrete. Quando o CSV tem valores como -, o pandas.to_numeric(..., errors="coerce") os transforma automaticamente em NaN (nulo), o que é o comportamento ideal para seus cálculos — ou seja, nenhuma mudança adicional é necessária no trecho que te enviei.

Mas para evitar qualquer ruído nos dados, podemos melhorar o processar_dados() para garantir:

Substituir o texto - por NaN em todo o DataFrame

Converter os dados numéricos com segurança

✅ Versão atualizada de processar_dados com suporte a -:
python
Copiar
Editar
def processar_dados(df):
    # Corrige nome das colunas
    df.columns = df.columns.str.strip().str.replace("\uFFFD", "", regex=True)

    # Substitui valores "-" por NaN em todo o DataFrame
    df.replace("-", pd.NA, inplace=True)

    # Converte o tempo
    if "time(ms)" not in df.columns:
        st.error(f"Coluna 'time(ms)' não encontrada. Colunas disponíveis: {df.columns.tolist()}")
        st.stop()
    df["TIME_CONVERTED"] = df["time(ms)"].apply(converter_tempo)

    # Converte marcha lenta
    if "ENGI_IDLE" not in df.columns:
        st.error(f"Coluna 'ENGI_IDLE' não encontrada. Colunas disponíveis: {df.columns.tolist()}")
        st.stop()
    map_idle = {"Sim": 1, "Não": 0, "Nao": 0, "nao": 0, "não": 0}
    df["ENGI_IDLE"] = df["ENGI_IDLE"].map(map_idle).fillna(0).astype(int)
    df["ACTIVE"] = df["ENGI_IDLE"].apply(lambda x: 0 if x == 1 else 1)

    # Lista de colunas numéricas que você usa nos cálculos
    colunas_numericas = [
        "TRIP_ODOM(km)", "FUEL_CONSUM", "Litres_Alcohol(L)", "LONGFT1(%)", 
        "AF_RATIO(:1)", "FUELPW(ms)", "VBAT_1(V)", "FUELLVL(%)"
    ]
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

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
    stats = {
        "Indicador": coluna,
        "Descrição": descricao_colunas.get(coluna, "-")
    }

    geral = df[coluna].dropna()
    stats["Min (Geral)"] = round(geral.min(), 2) if not geral.empty else "-"
    stats["Max (Geral)"] = round(geral.max(), 2) if not geral.empty else "-"
    stats["Média (Geral)"] = round(geral.mean(), 2) if not geral.empty else "-"

    if considerar_idle:
        idle = df[df["ENGI_IDLE"] == 1][coluna].dropna()
        ativo = df[df["ENGI_IDLE"] == 0][coluna].dropna()
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
        # leitura inicial do conteúdo
        content = uploaded_file.read().decode("utf-8")
        df = pd.read_csv(StringIO(content), sep=";")
        st.success("✅ Arquivo carregado com sucesso!")

        df = processar_dados(df)

        # Seção de Resumo
        st.subheader("📌 Resumo Geral da Viagem")
        distancia = calcular_distancia(df)
        consumo = calcular_consumo(df)
        kml = calcular_kml(distancia, consumo)

        col1, col2, col3 = st.columns(3)
        col1.metric("Distância (km)", distancia or "N/A")
        col2.metric("Consumo (L)", consumo or "N/A")
        col3.metric("Consumo Médio (km/L)", kml or "N/A")

        # Estatísticas Detalhadas
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

        # Alertas
        st.markdown("---")
        st.subheader("🚨 Alertas de Desempenho")
        alertas = avaliar_alertas(df)
        if alertas:
            for alerta in alertas:
                st.warning(alerta)
        else:
            st.success("✅ Nenhum alerta crítico identificado.")

        # Relatório TXT
        st.markdown("---")
        st.subheader("📄 Relatório Consolidado (.txt)")
        relatorio_txt = gerar_relatorio_txt(df, df_stats, distancia, consumo, kml, alertas)

        st.text_area("📋 Pré-visualização do relatório", relatorio_txt, height=400)
        st.download_button("📥 Baixar Relatório TXT", relatorio_txt, file_name="relatorio_forscan.txt", mime="text/plain")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
