import altair as alt
import streamlit as st
import vl_convert as vlc

st.set_page_config(
    page_title="HeatMap Interativo UF Origem x UF Destino",
    layout='wide'
)

st.markdown("## HeatMap Interativo UF Origem x UF Destino")

df_nfe = st.session_state["df_nfe"]
labels = st.session_state["labels"]

matriz_valores = st.session_state["matriz_valores"]
source = st.session_state["matriz_grafico_heatmap"]

pts = alt.selection_point(encodings=['y'])

rect = alt.Chart(
    source
).mark_rect(
).encode(
    alt.X('uf_dest:N').title('UF Destino'),
    alt.Y('uf_orig:N').title('UF Origem'),
    alt.Color('valor:Q').scale(scheme='lightmulti', reverse=False, 
                               type='sqrt', nice=True,
                               domainMid=100000000).title('Valor Total NFe'),
    tooltip=[alt.Tooltip(field='uf_dest', title='UF Destino'),
            alt.Tooltip(field='uf_orig', title='UF Origem'),
            alt.Tooltip(field='valor', title='Valor Total NF-e',
                        format='($,.2f')]
).add_params(pts
).properties(
    width=800,
    height=600
)

circ = rect.mark_point().encode(
    alt.ColorValue('green'),
    alt.Size('valor:Q').title('Valor')
).transform_filter(
    pts
)

bar = alt.Chart(source).mark_bar().encode(
    alt.X('uf_dest:N').title('UF Destino'),
    alt.Y('valor:Q').title('Valor Total das NF-e'),
    alt.ColorValue('steelblue'),
    tooltip=[alt.Tooltip(field='valor', title='Valor Total NF-e',
                        format='($,.2f')]
).transform_filter(
    pts
).properties(
    width=800,
    height=300
)

st.altair_chart(
    alt.vconcat(
        rect + circ,
        bar,
        usermeta={
            "embedOptions": {
                "formatLocale": vlc.get_format_locale('pt-BR'),
                "timeFormatLocale": vlc.get_time_format_locale('pt-BR')
            }
        }
    ).resolve_legend(
        color="independent",
        size="independent"
    ).configure(
        autosize='fit-x'
    )
)
