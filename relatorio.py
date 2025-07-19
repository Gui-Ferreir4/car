def gerar_relatorio_txt(df_stats, distancia, consumo, kml, alertas):
    from io import StringIO
    buffer = StringIO()

    buffer.write("===== RELATÓRIO DE ANÁLISE - FORSCAN LITE =====\n\n")
    buffer.write(f"- Distância percorrida: {distancia or 'N/A'} km\n")
    buffer.write(f"- Combustível consumido: {consumo or 'N/A'} L\n")
    buffer.write(f"- Consumo médio: {kml or 'N/A'} km/L\n\n")
    buffer.write("Alertas:\n")
    for alerta in alertas or ["Nenhum alerta crítico identificado"]:
        buffer.write(f"- {alerta}\n")

    buffer.write("\nEstatísticas:\n")
    for _, row in df_stats.iterrows():
        buffer.write(f"{row['Indicador']}: {row['Média']} | Min: {row['Min']} | Máx: {row['Máx']}\n")
    return buffer.getvalue()
