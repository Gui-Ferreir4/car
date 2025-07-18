# app.py - Parte 1
import streamlit as st
import pandas as pd
from datetime import timedelta
from io import StringIO


st.set_page_config(page_title="Análise Forscan Lite", layout="wide")
st.title("🔍 Análise Forscan Lite - Consumo e Desempenho")

# --- Input seleção do combustível ---
combustivel = st.selectbox(
    "Selecione o combustível atual",
    options=["Gasolina", "Etanol"],
    index=0,
    help="Escolha o combustível usado para ajustar análises de consumo."
)

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

# --- Função para converter tempo ms para HH:MM:SS ---
def converter_tempo(ms):
    try:
        segundos = int(ms) // 1000
        return str(timedelta(seconds=segundos))
    except:
        return "Inválido"

# --- Processamento inicial do DataFrame ---
def processar_dados(df):
    # Limpa espaços e caracteres estranhos das colunas
    df.columns = df.columns.str.strip().str.replace("\uFFFD", "", regex=True)

    # Verifica colunas obrigatórias
    if "time(ms)" not in df.columns:
        st.error(f"Coluna 'time(ms)' não encontrada. Colunas disponíveis: {df.columns.tolist()}")
        st.stop()
    if "ENGI_IDLE" not in df.columns:
        st.error(f"Coluna 'ENGI_IDLE' não encontrada. Colunas disponíveis: {df.columns.tolist()}")
        st.stop()

    # Converte tempo
    df["TIME_CONVERTED"] = df["time(ms)"].apply(converter_tempo)

    # Mapeia "Sim"/"Não" para 1/0 em ENGI_IDLE
    map_idle = {"Sim": 1, "Não": 0, "Nao": 0, "nao": 0, "não": 0}
    df["ENGI_IDLE"] = df["ENGI_IDLE"].map(map_idle).fillna(0).astype(int)

    # Coluna ACTIVE: 0 marcha lenta ligada, 1 desligada
    df["ACTIVE"] = df["ENGI_IDLE"].apply(lambda x: 0 if x == 1 else 1)

    # Conversão colunas numéricas que podem vir com '-'
    for col in df.columns:
        if df[col].dtype == object:
            # Tentar converter substituindo '-' por NaN
            df[col] = pd.to_numeric(df[col].replace("-", pd.NA), errors="coerce")

    return df

# app.py - Parte 2

# Constante do volume do tanque em litros
VOLUME_TANQUE = 55.0

def calcular_consumo_combustivel(df):
    """
    Calcula o consumo em litros baseado nas médias de FUELLVL(%) no início e fim da viagem.
    Considera somente períodos de marcha lenta (ENGI_IDLE == 1).
    """
    if "FUELLVL(%)" not in df.columns:
        return None

    # Seleciona registros em marcha lenta
    df_idle = df[df["ENGI_IDLE"] == 1]

    # Checa se há dados suficientes
    if df_idle.empty:
        return None

    # Calcula média nos primeiros 5% do tempo da viagem (início)
    tempo_total = df_idle["time(ms)"].max() - df_idle["time(ms)"].min()
    limite_inicial = df_idle["time(ms)"].min() + 0.05 * tempo_total
    media_inicio = df_idle[df_idle["time(ms)"] <= limite_inicial]["FUELLVL(%)"].mean()

    # Calcula média nos últimos 5% do tempo da viagem (fim)
    limite_final = df_idle["time(ms)"].max() - 0.05 * tempo_total
    media_fim = df_idle[df_idle["time(ms)"] >= limite_final]["FUELLVL(%)"].mean()

    if pd.isna(media_inicio) or pd.isna(media_fim):
        return None

    # Consumo em % do tanque
    percentual_consumido = media_inicio - media_fim
    if percentual_consumido < 0:
        percentual_consumido = 0  # proteção contra valores negativos

    # Converte percentual para litros (tanque cheio = 100%)
    litros_consumidos = percentual_consumido / 100.0 * VOLUME_TANQUE

    return round(litros_consumidos, 2)

# Estatísticas detalhadas refinadas por campo

def calcular_distancia(df):
    if "TRIP_ODOM(km)" in df.columns:
        return round(df["TRIP_ODOM(km)"].max() - df["TRIP_ODOM(km)"].min(), 2)
    return None

def calcular_kml(distancia, consumo):
    if distancia and consumo and consumo > 0:
        return round(distancia / consumo, 2)
    return None
    
def gerar_relatorio_txt(df, df_stats, distancia, consumo, kml, alertas):
    from io import StringIO
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
    buffer.write("\nEstatísticas por Coluna:\n")
    for _, row in df_stats.iterrows():
        buffer.write(f"- {row['Indicador']} | {row['Descrição']}\n")
        buffer.write(f"   → Média Geral: {row['Média (Geral)']}\n")
        buffer.write(f"   → Média Marcha Lenta: {row['Média (Marcha Lenta)']}\n")
        buffer.write(f"   → Média Atividade: {row['Média (Atividade)']}\n")
        buffer.write(f"   → Mín: {row['Min (Geral)']}, Máx: {row['Max (Geral)']}\n\n")
    return buffer.getvalue()

def gerar_estatisticas_refinadas(df, coluna, tipo_combustivel="gasolina", considerar_idle=False):
    stats = {
        "Indicador": coluna,
        "Descrição": descricao_colunas.get(coluna, "-"),
        "Valor Ideal Marcha Lenta": "-",
        "Valor Ideal Atividade": "-",
        "Min (Geral)": "-",
        "Max (Geral)": "-",
        "Média (Geral)": "-",
        "Média (Marcha Lenta)": "-",
        "Média (Atividade)": "-"
    }
    
    # Função para obter valores ideais segundo a tabela (exemplo simplificado)
    def valores_ideais(col, tipo):
        # Valores baseados na tabela que montamos, simplificado para exemplo:
        vals = {
            "ENGI_IDLE": {"gasolina": (1, 0), "etanol": (1, 0)},
            "RPM(1/min)": {"gasolina": (700, 800), "etanol": (700, 850)},
            "AF_RATIO(:1)": {"gasolina": (14.7, 14.7), "etanol": (9.0, 9.0)},
            "LONGFT1(%)": {"gasolina": (-10, 10), "etanol": (-10, 10)},
            # ... inclua mais conforme tabela real
        }
        if col in vals:
            return vals[col][tipo]
        return ("-", "-")
    
    # Preparar a coluna para cálculo (remover -, converter para numérico se possível)
    serie = df[coluna].replace("-", pd.NA).dropna()
    
    # Tentar converter para numérico para cálculo
    try:
        serie_num = pd.to_numeric(serie, errors='coerce').dropna()
    except Exception:
        serie_num = pd.Series(dtype=float)
    
    if serie_num.empty:
        # Se não tem dados numéricos, só contar valores ou fazer análise qualitativa
        stats["Min (Geral)"] = "-"
        stats["Max (Geral)"] = "-"
        stats["Média (Geral)"] = "-"
        stats["Média (Marcha Lenta)"] = "-"
        stats["Média (Atividade)"] = "-"
        return stats
    
    # Valores ideais para essa coluna e tipo de combustível
    ideal_min, ideal_max = valores_ideais(coluna, tipo_combustivel)
    stats["Valor Ideal Marcha Lenta"] = ideal_min
    stats["Valor Ideal Atividade"] = ideal_max
    
    # Cálculos gerais
    stats["Min (Geral)"] = round(serie_num.min(), 2)
    stats["Max (Geral)"] = round(serie_num.max(), 2)
    stats["Média (Geral)"] = round(serie_num.mean(), 2)
    
    if considerar_idle and "ENGI_IDLE" in df.columns:
        idle_vals = df[df["ENGI_IDLE"] == 1][coluna].replace("-", pd.NA).dropna()
        ativo_vals = df[df["ENGI_IDLE"] == 0][coluna].replace("-", pd.NA).dropna()
        
        try:
            idle_num = pd.to_numeric(idle_vals, errors='coerce').dropna()
            ativo_num = pd.to_numeric(ativo_vals, errors='coerce').dropna()
        except Exception:
            idle_num = pd.Series(dtype=float)
            ativo_num = pd.Series(dtype=float)
        
        stats["Média (Marcha Lenta)"] = round(idle_num.mean(), 2) if not idle_num.empty else "-"
        stats["Média (Atividade)"] = round(ativo_num.mean(), 2) if not ativo_num.empty else "-"
    else:
        stats["Média (Marcha Lenta)"] = "-"
        stats["Média (Atividade)"] = "-"
    
    # Aqui você pode expandir para campos específicos, ex:
    if coluna == "AF_RATIO(:1)":
        ideal_ratio = 14.7 if tipo_combustivel == "gasolina" else 9.0
        desvio = abs(stats["Média (Geral)"] - ideal_ratio)
        stats["Desvio do Ideal"] = round(desvio, 2)
    
    # Exemplo de tratamento para booleanos ou flags
    if coluna == "ENGI_IDLE":
        counts = df["ENGI_IDLE"].value_counts(normalize=True, dropna=False)
        stats["Percentual Sim"] = round(counts.get(1, 0)*100, 2)
        stats["Percentual Não"] = round(counts.get(0, 0)*100, 2)
    
    # Continue adaptando cada campo conforme a tabela
    
    return stats

# app.py - Parte 3
# Constantes de eficiência média para cálculo opcional (não usado diretamente aqui, mas pode ser usado em alertas)
EFICIENCIA_KM_LITRO = {
    "Gasolina": 12.0,  # exemplo, km por litro médio esperado
    "Álcool": 8.0
}

def avaliar_alertas(df, combustivel):
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

    # Consumo calculado via FUELLVL
    consumo_litros = calcular_consumo_combustivel(df)
    if consumo_litros is not None:
        alertas.append(f"ℹ️ Consumo estimado: {consumo_litros:.2f} litros (baseado na variação de FUELLVL(%))")
    else:
        alertas.append("ℹ️ Consumo estimado: dados insuficientes para cálculo")

    # Exemplo simples: verificar se consumo está acima da média esperada para o combustível selecionado
    distancia = calcular_distancia(df)
    if distancia and consumo_litros:
        consumo_real = consumo_litros / distancia if distancia > 0 else None
        if consumo_real:
            km_por_litro = 1 / consumo_real
            esperado = EFICIENCIA_KM_LITRO.get(combustivel, None)
            if esperado and km_por_litro < esperado * 0.7:
                alertas.append(f"⚠️ Consumo alto detectado: {km_por_litro:.2f} km/l (média esperada ~{esperado} km/l)")

    return alertas
    
uploaded_file = st.file_uploader("📂 Faça upload do arquivo CSV Forscan", type=["csv"])

# Interface após upload

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, encoding='utf-8', sep=';')
    df = processar_dados(df)  # <- Aqui df é definido e processado
    try:
        # Estatísticas detalhadas
        tabela_final = []
        for col in df.columns:
            if col in ["ENGI_IDLE", "ACTIVE", "time(ms)", "TIME_CONVERTED"]:
                continue
            considerar_idle = col not in [
                "ODOMETER(km)", "TRIP_ODOM(km)", "FUELLVL(%)", "VBAT_1(V)", "ENG_STATUS",
                "AF_LEARN", "MIXCNT_STAT", "OPENLOOP", "time(ms)", "TIME_CONVERTED"
            ]
            tabela_final.append(gerar_estatisticas_refinadas(df, col, combustivel.lower(), considerar_idle))

        df_stats = pd.DataFrame(tabela_final)

        # Resumo e métricas
        st.subheader("📌 Resumo Geral da Viagem")
        distancia = calcular_distancia(df)
        consumo = calcular_consumo_combustivel(df)
        kml = calcular_kml(distancia, consumo)

        col1, col2, col3 = st.columns(3)
        col1.metric("Distância (km)", distancia or "N/A")
        col2.metric("Consumo (L)", consumo or "N/A")
        col3.metric("Consumo Médio (km/L)", kml or "N/A")

        # Estatísticas detalhadas
        st.markdown("---")
        st.subheader("📊 Estatísticas Detalhadas por Coluna")
        st.dataframe(df_stats, use_container_width=True)

        # Alertas
        st.markdown("---")
        st.subheader("🚨 Alertas de Desempenho")
        alertas = avaliar_alertas(df, combustivel)
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
