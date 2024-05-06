import pandas as pd
import altair as alt
import streamlit as st
import vl_convert as vlc

st.set_page_config(
    page_title="Categorias de Produtos",
    layout='wide'
)

st.markdown("## Categorias de Produtos")

data_geojson = st.session_state["data_geojson"]

# Função para obter a seção com base no capítulo
def obter_secao(capitulo):
    # Dicionário que mapeia os capítulos às suas respectivas seções
    secoes_por_capitulo = {
        range(1, 6): 'ANIMAIS VIVOS E PRODUTOS DO REINO ANIMAL',
        range(6, 15): 'PRODUTOS DO REINO VEGETAL',
        range(15, 16): 'GORDURAS E ÓLEOS ANIMAIS OU VEGETAIS; PRODUTOS DA SUA DISSOCIAÇÃO; GORDURAS ALIMENTÍCIAS ELABORADAS; CERAS DE ORIGEM ANIMAL OU VEGETAL',
        range(16, 25): 'PRODUTOS DAS INDÚSTRIAS ALIMENTARES; BEBIDAS, LÍQUIDOS ALCOÓLICOS E VINAGRES; TABACO E SEUS SUCEDÂNEOS MANUFATURADOS',
        range(25, 28): 'PRODUTOS MINERAIS',
        range(28, 39): 'PRODUTOS DAS INDÚSTRIAS QUÍMICAS OU DAS INDÚSTRIAS CONEXAS',
        range(39, 41): 'PLÁSTICO E SUAS OBRAS; BORRACHA E SUAS OBRAS',
        range(41, 44): 'PELES, COUROS, PELES COM PELO E OBRAS DESTAS MATÉRIAS; ARTIGOS DE CORREEIRO OU DE SELEIRO; ARTIGOS DE VIAGEM, BOLSAS E ARTIGOS SEMELHANTES; OBRAS DE TRIPA',
        range(44, 47): 'MADEIRA, CARVÃO VEGETAL E OBRAS DE MADEIRA; CORTIÇA E SUAS OBRAS; OBRAS DE ESPARTARIA OU DE CESTARIA',
        range(47, 50): 'PASTAS DE MADEIRA OU DE OUTRAS MATÉRIAS FIBROSAS CELULÓSICAS; PAPEL OU CARTÃO PARA RECICLAR (DESPERDÍCIOS E APARAS); PAPEL OU CARTÃO E SUAS OBRAS',
        range(50, 64): 'MATÉRIAS TÊXTEIS E SUAS OBRAS',
        range(64, 68): 'CALÇADO, CHAPÉUS E ARTIGOS DE USO SEMELHANTE, GUARDA-CHUVAS, GUARDA-SÓIS, BENGALAS, CHICOTES, E SUAS PARTES; PENAS PREPARADAS E SUAS OBRAS; FLORES ARTIFICIAIS; OBRAS DE CABELO',
        range(68, 71): 'OBRAS DE PEDRA, GESSO, CIMENTO, AMIANTO, MICA OU DE MATÉRIAS SEMELHANTES; PRODUTOS CERÂMICOS; VIDRO E SUAS OBRAS',
        range(71, 72): 'PÉROLAS NATURAIS OU CULTIVADAS, PEDRAS PRECIOSAS OU SEMIPRECIOSAS E SEMELHANTES, METAIS PRECIOSOS, METAIS FOLHEADOS OU CHAPEADOS DE METAIS PRECIOSOS (PLAQUÊ), E SUAS OBRAS; BIJUTERIAS; MOEDAS',
        range(72, 84): 'METAIS COMUNS E SUAS OBRAS',
        range(84, 86): 'MÁQUINAS E APARELHOS, MATERIAL ELÉTRICO, E SUAS PARTES; APARELHOS DE GRAVAÇÃO OU DE REPRODUÇÃO DE SOM, APARELHOS DE GRAVAÇÃO OU DE REPRODUÇÃO DE IMAGENS E DE SOM EM TELEVISÃO, E SUAS PARTES E ACESSÓRIOS',
        range(86, 90): 'MATERIAL DE TRANSPORTE',
        range(90, 93): 'INSTRUMENTOS E APARELHOS DE ÓPTICA, DE FOTOGRAFIA, DE CINEMATOGRAFIA, DE MEDIDA, DE CONTROLE OU DE PRECISÃO; INSTRUMENTOS E APARELHOS MÉDICO-CIRÚRGICOS; ARTIGOS DE RELOJOARIA; INSTRUMENTOS MUSICAIS; SUAS PARTES E ACESSÓRIOS',
        range(93, 94): 'ARMAS E MUNIÇÕES; SUAS PARTES E ACESSÓRIOS',
        range(94, 97): 'MERCADORIAS E PRODUTOS DIVERSOS',
        range(97, 98): 'OBJETOS DE ARTE, DE COLEÇÃO E ANTIGUIDADES',
    }

    capitulo = int(capitulo)
    for faixa, secao in secoes_por_capitulo.items():
        if capitulo in faixa:
            return secao
    return 'Seção Desconhecida'  # Se o capítulo não estiver mapeado, atribua 'Seção Desconhecida'

@st.cache_data
def carregar_arquivo_itens_nfe():
    # Carregando os dados dos itens NF-e
    df_item = pd.read_csv('202401_NFe_NotaFiscalItem.csv', encoding='ISO-8859-1', sep=';', dtype=str)

    df_item['VALOR TOTAL'] = df_item['VALOR TOTAL'].apply(lambda x: float(x.split()[0].replace(',', '.')))
    df_item = df_item.astype({'VALOR TOTAL': 'float'})

    # Eliminar as instâncias em que o código NCM informado está claramente errado (valores inexistentes, vazios, etc)
    df_item = df_item.loc[df_item['CÓDIGO NCM/SH'] != '-1']
    df_item = df_item.loc[df_item['CÓDIGO NCM/SH'] != '99999999']
    df_item = df_item.loc[df_item['CÓDIGO NCM/SH'].str.len() >= 7]

    # Criar atributo para o capítulo da NCM
    df_item['CÓDIGO NCM/SH'] = df_item['CÓDIGO NCM/SH'].apply(lambda x: x.zfill(8))
    df_item['CAPÍTULO NCM'] = df_item['CÓDIGO NCM/SH'].str.slice(0, 2)

    # Adicionar o novo atributo 'Seção' ao DataFrame
    df_item['SEÇÃO'] = df_item['CAPÍTULO NCM'].apply(obter_secao)

    # Renomeando campos
    df_item.rename(columns={'UF EMITENTE': 'sigla_uf'}, inplace=True)

    return df_item

if "df_item" not in st.session_state:
    df_item = carregar_arquivo_itens_nfe()
    st.session_state["df_item"] = df_item
else:
    df_item = st.session_state["df_item"]

@st.cache_data
def agregar_valores_mapa_ncm(df_item):
    # Agrupando por UF e capítulo NCM
    df_soma_por_uf_ncm = df_item.groupby(['sigla_uf', 'CAPÍTULO NCM'])['VALOR TOTAL'].sum()

    # Selecionado o capítulo de NCM com mais vendas por UF
    df_maior_soma_por_uf = df_soma_por_uf_ncm.groupby(level='sigla_uf').idxmax()

    # Agrupando por UF e seção
    df_soma_por_uf_secao = pd.DataFrame(df_item.groupby(['sigla_uf', 'SEÇÃO'], as_index=False, group_keys=False)['VALOR TOTAL'].sum())

    # Selecionado a seção com mais vendas por UF
    df_maior_soma_por_uf = pd.DataFrame(df_soma_por_uf_secao.groupby(['sigla_uf'], as_index=False).idxmax(numeric_only=True))
    df_maior_soma_por_uf['CATEGORIA'] = df_maior_soma_por_uf['VALOR TOTAL'].apply(lambda x: df_soma_por_uf_secao.iloc[x]['SEÇÃO'])
    df_maior_soma_por_uf['VALOR'] = df_maior_soma_por_uf['VALOR TOTAL'].apply(lambda x: df_soma_por_uf_secao.iloc[x]['VALOR TOTAL'])

    return df_maior_soma_por_uf

df_maior_soma_por_uf = agregar_valores_mapa_ncm(df_item)

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
