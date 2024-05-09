import altair as alt
import streamlit as st

st.set_page_config(
    page_title="Mapa do Fluxo de Produtos das NF-e",
    layout='wide'
)

st.markdown("## Mapa do Fluxo de Produtos das NF-e")

st.markdown(
    """
    Este gráfico ajuda a responder a seguinte pergunta: qual é o fluxo interestadual de produtos a partir de uma UF?
    """)

df_capitais = st.session_state["df_capitais"]
data_geojson = st.session_state["data_geojson"]
df_consolidado = st.session_state["df_consolidado"]
source = st.session_state["matriz_grafico_heatmap"]

df_consolidado = df_consolidado.merge(df_capitais, on = 'sigla_uf', how = 'left')

source_lines = source.copy()
source_lines = source_lines[source_lines.valor != 0]
source_lines.reset_index(drop=True, inplace=True)

source_lines.rename({'uf_orig': 'sigla_uf'}, axis = 1, inplace = True)


sel_origem = alt.selection_point(on='click', nearest=False, fields=['sigla_uf'], empty=False)

# shared data reference for lookup transforms
destino = alt.LookupData(data=df_capitais, key='sigla_uf', fields=['latitude', 'longitude'])

st.altair_chart(

    alt.layer(
        alt.Chart(
            data = df_consolidado
        ).mark_geoshape(
            fill='#ddd',
            stroke='black',
            strokeWidth=0.2,
            tooltip=''
        ).transform_lookup(
            lookup='sigla_uf',
            from_=alt.LookupData(data_geojson, 'properties.SIGLA', ['type','geometry']),
        ),
        # linhas traçadas entre a UF de Emissão e a UF de Destino da NF-e
        alt.Chart(source_lines).mark_line(
            color='red',
            opacity=0.35,
            strokeWidth=1
        ).transform_filter(
            sel_origem
        ).transform_lookup(
            lookup='sigla_uf',
            from_=destino,
            as_=['latitude', 'longitude']
        ).transform_lookup(
            lookup='uf_dest',
            from_=destino,
            as_=['lat2', 'lon2']
        ).encode(
            latitude='latitude:Q',
            longitude='longitude:Q',
            latitude2='lat2:Q',
            longitude2='lon2:Q',
            size=alt.Size('valor:O', legend=None)
        ),
        alt.Chart(
            df_capitais
        ).mark_circle(
        ).transform_lookup(
            lookup='sigla_uf',
            from_=alt.LookupData(data=df_consolidado, key='sigla_uf',
                                  fields=['qtd_total_nfe_emit', 'latitude', 'longitude'])
        ).add_params(
            sel_origem
        ).encode(
            latitude='latitude:Q',
            longitude='longitude:Q',
            tooltip=[alt.Tooltip(shorthand='sigla_uf:N', title='Estado'),
                      alt.Tooltip(shorthand='qtd_total_nfe_emit:Q', title='Qtde NF-e', format='(,.0f')],
            size=alt.Size('qtd_total_nfe_emit:Q', legend=None).scale(domain=[0, 10000])
        )
    ).project(
        'equirectangular'
    ).properties(
        width=900,
        height=700
    ).configure_view(
        stroke=None
    )

)
