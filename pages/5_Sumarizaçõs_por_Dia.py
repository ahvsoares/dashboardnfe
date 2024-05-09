import altair as alt
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Sumarizações por Dia",
    layout='wide'
)

st.markdown("## Sumarizações por Dia")

df_nfe = st.session_state["df_nfe"]

tab1, tab2, tab3 = st.tabs(["Histograma NF-e por dia", "Mapa de Calor", "Gráfico de Linhas"])

with tab1:

    st.markdown(
        """
        Este gráfico ajuda a responder a seguinte pergunta: como se dá a emissão de NF-e ao longo do mês?
        """)
    
    FORMATO_DATA = '%d/%m/%Y %H:%M:%S'
    df_nfe['dh_emissao_format'] = pd.to_datetime(df_nfe['DATA EMISSÃO'], format=FORMATO_DATA)
    df_nfe['dia_emissao'] = df_nfe['dh_emissao_format'].apply(lambda x: "%d" % (x.day))
    df_nfe = df_nfe.astype({'dia_emissao': 'int'})

    labels_dh, counts_dh = np.unique(df_nfe['dia_emissao'], return_counts=True)
    data_por_dia = {'dia_emissao': labels_dh, 'qtd_nfe': counts_dh}
    df_emit_por_dia = pd.DataFrame(data_por_dia)

    hist_total_nfe_dia = alt.Chart(
        data = df_emit_por_dia,
        title = 'Quantidade de NF-e emitidas por dia'
    ).mark_bar().encode(
        alt.X('dia_emissao:O').title('Dia Emissão'),
        alt.Y('qtd_nfe:Q').title('Quantidade de NF-e'),
        alt.ColorValue('steelblue'),
        tooltip=alt.Tooltip(field='qtd_nfe')
    ).properties(
        width=800,
        height=400
    )

    # Exibindo o mapa
    st.altair_chart(hist_total_nfe_dia)

with tab2:

    st.markdown(
        """
        Este gráfico ajuda a responder a seguinte pergunta: como se dá a emissão de NF-e ao longo do mês?
        """)
    
    # Cria campo com a hora de emissão
    df_nfe['hora_emissao'] = df_nfe['dh_emissao_format'].dt.hour

    # Cria dataframe com o agrupamento por dia e hora
    df_diahora = df_nfe.groupby(['dia_emissao', 'hora_emissao']).size().reset_index(name='qtde')

    # Criar o heatmap com Altair
    heatmap = alt.Chart(df_diahora).mark_rect().encode(
        x='dia_emissao:O',
        y='hora_emissao:O',
        color=alt.Color('qtde:Q').scale(scheme='lightmulti', reverse=False, 
                            type='linear', nice=True, domainMid=1000),
        tooltip=['dia_emissao', 'hora_emissao', 'qtde']
    ).properties(
        title="Quantidade de Notas Emitidas por Dia e Hora",
        width=800,
        height=500
    )

    # Exibindo o mapa
    st.altair_chart(heatmap)

with tab3:

    st.markdown(
        """
        Este gráfico ajuda a responder a seguinte pergunta: como se dá a emissão de NF-e ao longo do mês?
        """)
    
    # Cria campo com o dia da semana
    df_nfe['dia_semana'] = df_nfe['dh_emissao_format'].dt.dayofweek.map({0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'})

    # Cria dataframe com o agrupamento por dia da semana e hora
    df_diasemana = df_nfe.groupby(['dia_semana', 'hora_emissao']).size().reset_index(name='qtde')

    # Criar o gráfico de linhas com Altair
    line_chart = alt.Chart(df_diasemana).mark_line().encode(
        x='hora_emissao:O',
        y='qtde:Q',
        color='dia_semana:N'
    ).properties(
        title="Quantidade de Notas Emitidas por Dia da Semana e Hora",
        width=800,
        height=400
    )

    # Exibindo o mapa
    st.altair_chart(line_chart)
