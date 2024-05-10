import os
import gdown
import zipfile
import json
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st


## Bases de dados

# Download e descompactação das bases
URL_NFE = "https://drive.google.com/uc?id=1eTAaOQkO6RT37XHOnR7bP6hBlwu-JLBB"
FILENAME_NFE = "202401_NFe.zip"
if not os.path.exists(FILENAME_NFE):
    gdown.download(URL_NFE, FILENAME_NFE, quiet=False)
    with zipfile.ZipFile(FILENAME_NFE, 'r') as zip_ref:
        zip_ref.extractall()
# os.remove(FILENAME_NFE)

URL_ESTADOS = "https://drive.google.com/uc?id=1ieqNEa1Fbb4I87OghPXS-Scn2a_Zva8t"
FILENAME_ESTADOS = "br_states.zip"
if not os.path.exists(FILENAME_ESTADOS):
    gdown.download(URL_ESTADOS, FILENAME_ESTADOS, quiet=False)
    with zipfile.ZipFile(FILENAME_ESTADOS, 'r') as zip_ref:
        zip_ref.extractall()
# os.remove(FILENAME_ESTADOS)

URL_COORDS = "https://drive.google.com/uc?id=1c9THXE6MX0VgA3kcwTFvKt4JJpIEddy_"
FILENAME_COORDS = "lat-long-capitais.zip"
if not os.path.exists(FILENAME_COORDS):
    gdown.download(URL_COORDS, FILENAME_COORDS, quiet=False)
    with zipfile.ZipFile(FILENAME_COORDS, 'r') as zip_ref:
        zip_ref.extractall()
# os.remove(FILENAME_COORDS)


## Agora iniciamos a aplicação

st.set_page_config(
    page_title="Dashboard NF-e",
    layout='wide'
)

st.write("# Estatísticas sobre NF-e")
st.write('''
         **O *dataset* utilizado corresponde a um subconjunto de NF-e emitidas ao longo do mês de janeiro de 2024, 
         referentes a compras realizadas exclusivamente por órgãos públicos e disponibilizadas no 
         [Portal da Transparência](https://portaldatransparencia.gov.br/download-de-dados/notas-fiscais).**
         ''')

st.sidebar.success("Escolha uma das visualizações acima.")

url_geojson = './br_states.json'

@st.cache_data
def carregar_arquivo_nfe():
    df_nfe = pd.read_csv('202401_NFe_NotaFiscal.csv', encoding='ISO-8859-1', sep=';', dtype=str)
    df_nfe['VALOR NOTA FISCAL'] = df_nfe['VALOR NOTA FISCAL'].apply(lambda x: float(x.split()[0].replace(',', '.')))
    df_nfe = df_nfe.astype({'VALOR NOTA FISCAL': 'float'})
    return df_nfe

@st.cache_data
def carregar_info_capitais():
    df_capitais = pd.read_csv('lat-long-capitais.csv', encoding='utf-8', sep=';')
    return df_capitais

@st.cache_data
def agregar_dados_nfe(df_nfe):
    labels_emit, counts_emit = np.unique(df_nfe['UF EMITENTE'], return_counts=True)
    data_emit = {'sigla_uf': labels_emit, 'qtd_total_nfe_emit': counts_emit}

    df_totais_uf_emit = pd.DataFrame(data_emit)
    df_totais_uf_emit['perc_emit_nfe'] = (df_totais_uf_emit['qtd_total_nfe_emit'] / df_totais_uf_emit['qtd_total_nfe_emit'].sum()) * 100
    df_totais_uf_emit = df_totais_uf_emit.round({'perc_emit_nfe': 2})

    df_valor_uf_emit = df_nfe.groupby(['UF EMITENTE'], as_index=False)[['VALOR NOTA FISCAL']].sum()
    df_valor_uf_emit.rename({'UF EMITENTE': 'sigla_uf', 'VALOR NOTA FISCAL': 'valor_total_emit'}, axis = 1, inplace = True)

    labels_dest, counts_dest = np.unique(df_nfe['UF DESTINATÁRIO'], return_counts=True)
    data_dest = {'sigla_uf': labels_dest, 'qtd_total_nfe_dest': counts_dest}
    df_totais_uf_dest = pd.DataFrame(data_dest)

    df_valor_uf_dest = df_nfe.groupby(['UF DESTINATÁRIO'], as_index=False)[['VALOR NOTA FISCAL']].sum()
    df_valor_uf_dest.rename({'UF DESTINATÁRIO': 'sigla_uf', 'VALOR NOTA FISCAL': 'valor_total_uf_dest'}, axis = 1, inplace = True)

    df_consolidado = df_totais_uf_emit.merge(df_valor_uf_emit, on = 'sigla_uf', how = 'left')
    df_consolidado = df_consolidado.merge(df_totais_uf_dest, on = 'sigla_uf', how = 'left')
    df_consolidado = df_consolidado.merge(df_valor_uf_dest, on = 'sigla_uf', how = 'left')

    return df_consolidado, labels_emit

@st.cache_data
def carregar_info_geojson():
    with open(url_geojson, 'r', encoding = 'utf-8') as f:
        data = json.load(f)
    data_geojson = alt.Data(values=data, format=alt.DataFormat(property='features',type='json'))
    return data_geojson

@st.cache_data
def criar_matriz_valores_nfe(df_nfe, labels):
    matriz_valores = np.zeros((27, 27))

    for sigla_origem in labels:
        indice_origem = np.where(labels == sigla_origem)[0][0]
        df_temp = df_nfe.loc[df_nfe['UF EMITENTE'] == sigla_origem].groupby(['UF DESTINATÁRIO'])[['VALOR NOTA FISCAL']].sum()
        for index, row in df_temp.iterrows():
            indice_destino = np.where(labels == index)[0][0]
            matriz_valores[indice_origem][indice_destino] = row['VALOR NOTA FISCAL']

    return matriz_valores

@st.cache_data
def criar_matriz_dados_grafico(matriz_valores, labels):
    x, y = np.meshgrid(labels, labels)

    # Convert this grid to columnar data expected by Altair
    source = pd.DataFrame({'uf_dest': x.ravel(),
                           'uf_orig': y.ravel(),
                           'valor': matriz_valores.ravel()})

    return source

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

df_nfe = carregar_arquivo_nfe()
df_consolidado, labels = agregar_dados_nfe(df_nfe)

data_geojson = carregar_info_geojson()
df_capitais = carregar_info_capitais()

matriz_valores = criar_matriz_valores_nfe(df_nfe, labels)
matriz_grafico_heatmap = criar_matriz_dados_grafico(matriz_valores, labels)

df_item = carregar_arquivo_itens_nfe()
df_item['QUANTIDADE'] = df_item['QUANTIDADE'].str.replace(',', '.').astype(float)

df_maior_soma_por_uf = agregar_valores_mapa_ncm(df_item)

if "df_nfe" not in st.session_state:
    st.session_state["df_nfe"] = df_nfe
if "df_consolidado" not in st.session_state:
    st.session_state["df_consolidado"] = df_consolidado
if "labels" not in st.session_state:
    st.session_state["labels"] = labels
if "data_geojson" not in st.session_state:
    st.session_state["data_geojson"] = data_geojson
if "df_capitais" not in st.session_state:
    st.session_state["df_capitais"] = df_capitais

if "matriz_valores" not in st.session_state:
    st.session_state["matriz_valores"] = matriz_valores
if "matriz_grafico_heatmap" not in st.session_state:
    st.session_state["matriz_grafico_heatmap"] = matriz_grafico_heatmap

if "df_item" not in st.session_state:
    st.session_state["df_item"] = df_item

if "df_maior_soma_por_uf" not in st.session_state:
    st.session_state["df_maior_soma_por_uf"] = df_maior_soma_por_uf

## Paineis

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil', 'milhões', 'bilhões']:
        if valor < 1_000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1_000
    return f'{prefixo} {valor:.2f} trilhões'

col1, col2, col3 = st.columns(3)

with col1:
    st.metric('Total de NF-e emitidas', formata_numero(df_nfe.shape[0]))
    st.metric('Valor total de vendas', formata_numero(df_nfe['VALOR NOTA FISCAL'].sum(), 'R$'))

with col2:
    st.metric('Total de itens vendidos', formata_numero(df_item['QUANTIDADE'].sum()))
    st.metric('Quantidade de empresas emissoras', formata_numero(len(df_nfe['CPF/CNPJ Emitente'].unique())))

with col3:
    st.metric('Média de itens vendidos por NF-e', formata_numero(df_item['QUANTIDADE'].sum()/df_nfe.shape[0]))
    st.metric('Quantidade de códigos NCM distintos', formata_numero(len(df_item['CÓDIGO NCM/SH'].unique())))

st.markdown('---')

st.markdown(
    """
    #### Algumas perguntas que queremos responder analisando-se este *dashboard*:
    * quais são os Estados mais vendedores?
    * quais são os Estados mais compradores?
    * qual é o fluxo interestadual monetário ?
    * qual é o fluxo interestadual monetário a partir de uma UF?
    * qual é o fluxo interestadual de produtos a partir de uma UF?
    * qual é o tipo de produto mais vendido por UF?
    * qual é o panorama de quantidade de notas emitas por UF e tipo de produto?
    * como se dá a emissão de NF-e ao longo do mês?
    """)
