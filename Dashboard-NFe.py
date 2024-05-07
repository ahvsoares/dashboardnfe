import os
import gdown
import zipfile
import json
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st

# Download e descompactação das bases
URL_NFE = "https://drive.google.com/uc?id=1eTAaOQkO6RT37XHOnR7bP6hBlwu-JLBB"
FILENAME_NFE = "202401_NFe.zip"
gdown.download(URL_NFE, FILENAME_NFE, quiet=False)
with zipfile.ZipFile(FILENAME_NFE, 'r') as zip_ref:
    zip_ref.extractall()
os.remove(FILENAME_NFE)

URL_ESTADOS = "https://drive.google.com/uc?id=1ieqNEa1Fbb4I87OghPXS-Scn2a_Zva8t"
FILENAME_ESTADOS = "br_states.zip"
gdown.download(URL_ESTADOS, FILENAME_ESTADOS, quiet=False)
with zipfile.ZipFile(FILENAME_ESTADOS, 'r') as zip_ref:
    zip_ref.extractall()
os.remove(FILENAME_ESTADOS)

URL_COORDS = "https://drive.google.com/uc?id=1c9THXE6MX0VgA3kcwTFvKt4JJpIEddy_"
FILENAME_COORDS = "lat-long-capitais.zip"
gdown.download(URL_COORDS, FILENAME_COORDS, quiet=False)
with zipfile.ZipFile(FILENAME_COORDS, 'r') as zip_ref:
    zip_ref.extractall()
os.remove(FILENAME_COORDS)

# Agora iniciamos a aplicação

st.set_page_config(
    page_title="Dashboard NF-e",
    layout='wide'
)

st.write("# Painel da NF-e")

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

df_nfe = carregar_arquivo_nfe()
df_consolidado, labels = agregar_dados_nfe(df_nfe)

data_geojson = carregar_info_geojson()
df_capitais = carregar_info_capitais()

matriz_valores = criar_matriz_valores_nfe(df_nfe, labels)
matriz_grafico_heatmap = criar_matriz_dados_grafico(matriz_valores, labels)


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



def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil', 'milhões']:
        if valor < 1_000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1_000
    return f'{prefixo} {valor:.2f} milhões'

col1, col2 = st.columns(2)

with col1:
    st.metric('Total de NF-e emitidas no período', formata_numero(df_nfe.shape[0]))

with col2:
    st.metric('Valor total de vendas no período', formata_numero(df_nfe['VALOR NOTA FISCAL'].sum(), 'R$'))
