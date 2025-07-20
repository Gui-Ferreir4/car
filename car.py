import streamlit as st
import pandas as pd
from funcoes_processamento import processar_dados
from funcoes_estatisticas import gerar_estatisticas_refinadas_expandido
from funcoes_alertas import avaliar_alertas
from funcoes_metricas import calcular_distancia, calcular_consumo_combustivel, calcular_kml
from funcoes_relatorio import gerar_relatorio_txt

st.set_page_config(page_title="Analisador Forscan Lite", layout="wide")
st.title("🚗 Analisador de Desempenho - Forscan Lite")

# Upload do arquivo
uploaded_file = st.file_uploader("📂 Faça upload do arquivo CSV Forscan", type=["csv"])

if uploaded_file is not None:
    try:
        # Leitura e processamento do CSV
        df = pd.read_csv(uploaded_file, encoding='utf-8', sep=';')
        df = processar_dados(df)

        # Pergunta o combustível usado
        #tipo_combustivel = st.radio("Qual o combustível usado na viagem?", ["Gasolina", "Etanol"])

        # Gera as estatísticas refinadas
        tabela_final = gerar_estatisticas_refinadas_expandido(df, tipo_combustivel.lower())
        df_stats = pd.DataFrame(tabela_final)

        # Exibe as estatísticas
        st.subheader("📊 Estatísticas Detalhadas por Coluna")
        st.dataframe(df_stats, use_container_width=True)

        # Resumo e métricas principais
        st.subheader("📌 Resumo Geral da Viagem")
        distancia = calcular_distancia(df)
        consumo = calcular_consumo_combustivel(df)
        kml = calcular_kml(distancia, consumo)

        col1, col2, col3 = st.columns(3)
        col1.metric("Distância (km)", f"{distancia:.2f}" if distancia else "N/A")
        col2.metric("Consumo (L)", f"{consumo:.2f}" if consumo else "N/A")
        col3.metric("Consumo Médio (km/L)", f"{kml:.2f}" if kml else "N/A")

        # Alertas de desempenho
        st.markdown("---")
        st.subheader("🚨 Alertas de Desempenho")
        alertas = avaliar_alertas(df, tipo_combustivel.lower())
        if alertas:
            for alerta in alertas:
                st.warning(alerta)
        else:
            st.success("✅ Nenhum alerta crítico identificado.")

        # Geração do relatório em TXT
        st.markdown("---")
        st.subheader("📄 Relatório Consolidado (.txt)")
        relatorio_txt = gerar_relatorio_txt(df, df_stats, distancia, consumo, kml, alertas)

        st.text_area("📋 Pré-visualização do relatório", relatorio_txt, height=400)
        st.download_button("📥 Baixar Relatório TXT", relatorio_txt, file_name="relatorio_forscan.txt", mime="text/plain")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
