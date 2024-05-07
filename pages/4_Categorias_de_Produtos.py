import altair as alt
import streamlit as st
import vl_convert as vlc

st.set_page_config(
    page_title="Categorias de Produtos",
    layout='wide'
)

st.markdown("## Categorias de Produtos")

data_geojson = st.session_state["data_geojson"]
df_item = st.session_state["df_item"]
df_maior_soma_por_uf = st.session_state["df_maior_soma_por_uf"]

tab1, tab2 = st.tabs(['Mapa Produto mais Vendido por UF', 'Sumarização UF/Produto'])

with tab1:
    # Cria o mapa
    mapa_secao_altair = alt.Chart(
        data = df_maior_soma_por_uf,
        title = 'Categoria de produto com maior valor de vendas por UF'
    ).mark_geoshape(
        stroke='black',
        strokeWidth=0.2
    ).transform_lookup(
        lookup='sigla_uf',
        from_=alt.LookupData(data_geojson, 'properties.SIGLA', ['type','geometry']),
    ).encode(
        alt.Color(shorthand = 'CATEGORIA',
                type='nominal',
                scale=alt.Scale(scheme='spectral'),
                title = "Categorias de produtos",
                legend=alt.Legend(symbolSize=200, symbolStrokeColor='white')),
        tooltip=[alt.Tooltip(field='sigla_uf', title='Estado'),
                alt.Tooltip(field='CATEGORIA', title='Seção'),
                alt.Tooltip(field='VALOR', title='Valor Total', format='($,.2f')]
    ).project(
        'equirectangular'
    ).properties(
        width=900,
        height=700,
        usermeta={
            "embedOptions": {
                "formatLocale": vlc.get_format_locale('pt-BR'),
                "timeFormatLocale": vlc.get_time_format_locale('pt-BR')
            }
        }
    )

    # Exibindo o mapa
    st.altair_chart(mapa_secao_altair)

with tab2:

    # tab1, tab2 = st.tabs(['Qtde Notas por UF e Produto', 'Valor Notas por UF e Produto'])
    col1, col2 = st.columns(2)

    # Cria dataframe com a quantidade de notas emitidas por UF e tipo de produto
    df_uf_emit_produto = df_item.groupby(['sigla_uf', 'SEÇÃO']) \
        .agg({'VALOR TOTAL': 'sum', 'SEÇÃO': 'count'}) \
        .rename(columns={'VALOR TOTAL': 'valor_total', 'SEÇÃO': 'qtde'}) \
        .reset_index()

    # Cria dataframe com a quantidade de notas por UF de destino e tipo de produto
    df_uf_dest_produto = df_item.groupby(['UF DESTINATÁRIO', 'SEÇÃO']) \
        .agg({'VALOR TOTAL': 'sum', 'SEÇÃO': 'count'}) \
        .rename(columns={'VALOR TOTAL': 'valor_total', 'SEÇÃO': 'qtde'}) \
        .reset_index()

    with col1:
        # Criar o gráfico de barras empilhadas com Altair
        stacked_bar_chart = alt.Chart(df_uf_emit_produto).mark_bar().encode(
            x='sigla_uf:N',
            y=alt.Y('qtde:Q',stack="normalize"),
            color='SEÇÃO:N',
            tooltip=['sigla_uf', 'SEÇÃO', 'qtde', 'valor_total']
        ).properties(
            title="Quantidade de Notas Emitidas por UF e Tipo de Produto",
            width=600,
            height=400
        )

        # Exibindo o mapa
        st.altair_chart(stacked_bar_chart)
        
        # Criar o gráfico de barras empilhadas com Altair
        stacked_bar_chart = alt.Chart(df_uf_dest_produto).mark_bar().encode(
            x='UF DESTINATÁRIO:N',
            y=alt.Y('qtde:Q',stack="normalize"),
            color='SEÇÃO:N',
            tooltip=['UF DESTINATÁRIO', 'SEÇÃO', 'qtde', 'valor_total']
        ).properties(
            title="Quantidade de Notas por UF de Destino e Tipo de Produto",
            width=600,
            height=400
        )

        # Exibindo o mapa
        st.altair_chart(stacked_bar_chart)

    with col2:
        # Criar o gráfico de barras empilhadas com Altair
        stacked_bar_chart = alt.Chart(df_uf_emit_produto).mark_bar().encode(
            x='sigla_uf:N',
            y=alt.Y('valor_total:Q',stack="normalize"),
            color='SEÇÃO:N',
            tooltip=['sigla_uf', 'SEÇÃO', 'valor_total', 'qtde']
        ).properties(
            title="Valor Total de Notas Emitidas por UF e Tipo de Produto",
            width=600,
            height=400
        )

        # Exibindo o mapa
        st.altair_chart(stacked_bar_chart)

        # Criar o gráfico de barras empilhadas com Altair
        stacked_bar_chart = alt.Chart(df_uf_dest_produto).mark_bar().encode(
            x='UF DESTINATÁRIO:N',
            y=alt.Y('valor_total:Q',stack="normalize"),
            color='SEÇÃO:N',
            tooltip=['UF DESTINATÁRIO', 'SEÇÃO', 'valor_total', 'qtde']
        ).properties(
            title="Valor Total de Notas por UF de Destino e Tipo de Produto",
            width=600,
            height=400
        )

        # Exibindo o mapa
        st.altair_chart(stacked_bar_chart)
