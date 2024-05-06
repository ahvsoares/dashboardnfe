import altair as alt
import streamlit as st

st.set_page_config(
    page_title="Sumarizações de NF-e por UF Origem e UF Destino",
    layout='wide'
)

st.markdown("## Sumarizações de NF-e por UF Origem e UF Destino")

df_nfe = st.session_state["df_nfe"]
df_consolidado = st.session_state["df_consolidado"]
data_geojson = st.session_state["data_geojson"]

tab1, tab2 = st.tabs(["Histograma", "Mapas"])

with tab1:

    rotulos_radio = ['Quantidade de NF-e emitidas por UF do Emissor',
                     'Total (R$) das NF-e emitidas por UF do Emissor',
                     'Quantidade de NF-e emitidas para a UF de Destino',
                     'Total (R$) das NF-e emitidas para a UF de Destino']

    campos_grafico = ['qtd_total_nfe_emit', 'valor_total_emit', 'qtd_total_nfe_dest', 'valor_total_uf_dest']

    legenda_eixo_x = ['UF Origem', 'UF Origem', 'UF Destino', 'UF Destino']
    legenda_eixo_y = ['Qtde NF-e', 'Valor Total NF-e', 'Qtde NF-e', 'Valor Total NF-e']

    formato_tooltip = ['(,.0f', '($,.2f', '(,.0f', '($,.2f']

    with st.sidebar:
        add_radio = st.radio(
            label='Escolha o Agrupamento desejado',
            options= range(len(rotulos_radio)),
            format_func=rotulos_radio.__getitem__,
            index=0
        )

    y_column = campos_grafico[add_radio]

    hist_qtd_total_nfe = alt.Chart(
        data = df_consolidado,
        title = rotulos_radio[add_radio]
    ).mark_bar().encode(
        alt.X('sigla_uf:N').title(legenda_eixo_x[add_radio]),
        alt.Y(y_column, type='quantitative').title(legenda_eixo_y[add_radio]),
        alt.ColorValue('steelblue'),
        tooltip=alt.Tooltip(field=y_column, format=formato_tooltip[add_radio])
    ).properties(
        width=800,
        height=400
    )

    st.altair_chart(hist_qtd_total_nfe)

with tab2:

    highlight = alt.selection_point(nearest=False, fields=['sigla_uf'], empty=False)

    # criando o mapa
    mapa_geo_teste = alt.Chart(
        df_consolidado,
        title = rotulos_radio[add_radio]
    ).mark_geoshape(
        stroke='black',
        strokeWidth=0.3
    ).encode(
        color=alt.condition(highlight,
                            alt.ColorValue('lightblue'),
                            alt.Color(shorthand=y_column,
                                        type='quantitative',
                                        scale=alt.Scale(scheme='reds'),
                                        title=legenda_eixo_y[add_radio])
        ),
        tooltip=[alt.Tooltip(field='sigla_uf', title='Estado'),
                 alt.Tooltip(field=y_column, title=legenda_eixo_y[add_radio],
                             format=formato_tooltip[add_radio])]
    ).interactive(
    ).transform_lookup(
        lookup='sigla_uf',
        from_=alt.LookupData(data_geojson, 'properties.SIGLA', ['type','geometry']),
    ).add_params(highlight
    ).project(
        'equirectangular'
    ).properties(
        width=600,
        height=600
    )

    st.altair_chart(mapa_geo_teste)
