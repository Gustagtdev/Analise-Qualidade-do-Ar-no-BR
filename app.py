import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Configuração da Página ---
st.set_page_config(layout='wide', page_title='Análise da Qualidade do Ar no Brasil')

st.title('Dashboard de Qualidade do Ar no Brasil 🇧🇷')

st.markdown("""
Este dashboard interativo permite analisar a qualidade do ar no Brasil utilizando indicadores ambientais, séries temporais e análises regionais.

📊 Utilize os filtros laterais para explorar:
- Regiões;
- Estados;
- Cidades;
- Períodos específicos;
- Níveis de qualidade do ar.

Os gráficos ajudam a identificar padrões de poluição, sazonalidade e comportamento dos principais poluentes atmosféricos.
""")

# --- Carregamento e Pré-processamento dos Dados ---
@st.cache_data
def load_and_preprocess_data():
    try:
        dados_ar = pd.read_csv('/dados/simulacao_qualidade_ar_brasil.csv')
    except FileNotFoundError:
        st.error("Arquivo 'simulacao_qualidade_ar_brasil.csv' não encontrado.")
        st.stop()

    dados_ar['data'] = pd.to_datetime(dados_ar['data'])
    dados_ar['dia'] = dados_ar['data'].dt.day

    meses_map = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }

    dados_ar['mes_nome'] = dados_ar['data'].dt.month.map(meses_map)

    dias_semana_map = {
        0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira',
        3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'
    }

    dados_ar['dia_da_semana'] = dados_ar['data'].dt.dayofweek.map(dias_semana_map)

    dados_ar['ano'] = dados_ar['data'].dt.year

    meses_ordem = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril',
        'Maio', 'Junho', 'Julho', 'Agosto',
        'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    dados_ar['mes_nome'] = pd.Categorical(
        dados_ar['mes_nome'],
        categories=meses_ordem,
        ordered=True
    )

    dias_semana_ordem = [
        'Segunda-feira', 'Terça-feira', 'Quarta-feira',
        'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'
    ]

    dados_ar['dia_da_semana'] = pd.Categorical(
        dados_ar['dia_da_semana'],
        categories=dias_semana_ordem,
        ordered=True
    )

    dados_ar['mes'] = dados_ar['data'].dt.month

    return dados_ar

dados_ar = load_and_preprocess_data()

# --- Sidebar ---
st.sidebar.header('Filtros')

anos_disponiveis = sorted(dados_ar['ano'].unique(), reverse=True)

ano_selecionado = st.sidebar.multiselect(
    'Selecione o Ano',
    options=anos_disponiveis,
    default=anos_disponiveis
)

meses_disponiveis = dados_ar['mes_nome'].cat.categories.tolist()

meses_selecionados = st.sidebar.multiselect(
    'Selecione o Mês',
    options=meses_disponiveis,
    default=meses_disponiveis
)

regioes_disponiveis = sorted(dados_ar['regiao'].unique())

regioes_selecionadas = st.sidebar.multiselect(
    'Selecione a Região',
    options=regioes_disponiveis,
    default=regioes_disponiveis
)

ufs_disponiveis = sorted(
    dados_ar[dados_ar['regiao'].isin(regioes_selecionadas)]['uf'].unique()
)

ufs_selecionadas = st.sidebar.multiselect(
    'Selecione o Estado (UF)',
    options=ufs_disponiveis,
    default=ufs_disponiveis
)

cidades_disponiveis = sorted(
    dados_ar[dados_ar['uf'].isin(ufs_selecionadas)]['cidade'].unique()
)

cidades_selecionadas = st.sidebar.multiselect(
    'Selecione a Cidade',
    options=cidades_disponiveis,
    default=cidades_disponiveis
)

niveis_qualidade_ordem = ['Boa', 'Moderada', 'Ruim', 'Péssima']

niveis_qualidade_disponiveis = [
    n for n in niveis_qualidade_ordem
    if n in dados_ar['nivel_qualidade'].unique()
]

niveis_qualidade_selecionados = st.sidebar.multiselect(
    'Selecione o Nível de Qualidade do Ar',
    options=niveis_qualidade_disponiveis,
    default=niveis_qualidade_disponiveis
)

# --- Aplicação dos filtros ---
dados_filtrados = dados_ar[
    dados_ar['ano'].isin(ano_selecionado) &
    dados_ar['mes_nome'].isin(meses_selecionados) &
    dados_ar['regiao'].isin(regioes_selecionadas) &
    dados_ar['uf'].isin(ufs_selecionadas) &
    dados_ar['cidade'].isin(cidades_selecionadas) &
    dados_ar['nivel_qualidade'].isin(niveis_qualidade_selecionados)
]

if dados_filtrados.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados.")
    st.stop()

# --- KPIs ---
st.subheader('Indicadores Chave de Desempenho (KPIs)')

col1, col2, col3, col4, col5, col6 = st.columns(6)

media_aqi = dados_filtrados['indice_qualidade_ar'].mean()
col1.metric("AQI Médio", f"{media_aqi:.2f}")

cidade_mais_poluida_df = dados_filtrados.groupby('cidade')['indice_qualidade_ar'].mean().reset_index()
cidade_mais_poluida_nome = cidade_mais_poluida_df.loc[
    cidade_mais_poluida_df['indice_qualidade_ar'].idxmax()
]

col2.metric(
    "Cidade Mais Poluída",
    f"{cidade_mais_poluida_nome['cidade']} ({cidade_mais_poluida_nome['indice_qualidade_ar']:.2f})"
)

poluentes_cols = ['pm25', 'pm10', 'no2', 'co', 'o3']

media_poluentes = dados_filtrados[poluentes_cols].mean()

poluente_predominante = media_poluentes.idxmax()

col3.metric(
    "Poluente Predominante",
    f"{poluente_predominante.upper()}"
)

dias_criticos = dados_filtrados[
    dados_filtrados['nivel_qualidade'].isin(['Ruim', 'Péssima'])
].shape[0]

percentual_critico = (dias_criticos / dados_filtrados.shape[0]) * 100

col4.metric(
    "Dias Críticos",
    f"{percentual_critico:.2f}%"
)

regiao_mais_afetada_df = dados_filtrados.groupby('regiao')['indice_qualidade_ar'].mean().reset_index()

regiao_mais_afetada = regiao_mais_afetada_df.loc[
    regiao_mais_afetada_df['indice_qualidade_ar'].idxmax()
]

col5.metric(
    "Região Mais Afetada",
    regiao_mais_afetada['regiao']
)

media_pm25 = dados_filtrados['pm25'].mean()

col6.metric(
    "PM2.5 Médio",
    f"{media_pm25:.2f}"
)

st.markdown("---")

# =========================================================
# VISUALIZAÇÕES
# =========================================================

st.subheader('Visualizações Interativas')

# ---------------------------------------------------------
# 1. Série Temporal
# ---------------------------------------------------------

st.write("### Evolução do Índice de Qualidade do Ar ao Longo do Tempo")

st.markdown("""
Este gráfico mostra como o Índice de Qualidade do Ar (AQI) varia ao longo do tempo.

🔎 O que analisar:
- Períodos de aumento ou redução da poluição;
- Tendências sazonais;
- Picos de poluição;
- Impactos climáticos.
""")

fig_serie_temporal = px.line(
    dados_filtrados.sort_values(by='data'),
    x='data',
    y='indice_qualidade_ar',
    labels={
        'data': 'Data',
        'indice_qualidade_ar': 'AQI'
    },
    line_shape='spline',
    template='plotly_white'
)

fig_serie_temporal.update_layout(
    hovermode='x unified'
)

st.plotly_chart(fig_serie_temporal, use_container_width=True)

# ---------------------------------------------------------
# 2. Comparação Regional
# ---------------------------------------------------------

st.write("### Comparação do Índice de Qualidade do Ar por Região")

st.markdown("""
Este gráfico compara a média do Índice de Qualidade do Ar entre as regiões brasileiras.

🔎 O que analisar:
- Regiões mais poluídas;
- Diferenças regionais;
- Impactos ambientais e urbanos.
""")

aqi_por_regiao = dados_filtrados.groupby(
    'regiao'
)['indice_qualidade_ar'].mean().reset_index()

fig_regiao = px.bar(
    aqi_por_regiao.sort_values(
        by='indice_qualidade_ar',
        ascending=False
    ),
    x='regiao',
    y='indice_qualidade_ar',
    color='regiao',
    template='plotly_white'
)

st.plotly_chart(fig_regiao, use_container_width=True)

# ---------------------------------------------------------
# 3. Ranking das cidades
# ---------------------------------------------------------

st.write("### Top Cidades com Maior Média de Índice de Qualidade do Ar")

st.markdown("""
Este gráfico apresenta as cidades com maior média de poluição atmosférica.

🔎 O que analisar:
- Cidades mais críticas;
- Diferença entre municípios;
- Necessidade de políticas públicas.
""")

aqi_por_cidade = dados_filtrados.groupby(
    'cidade'
)['indice_qualidade_ar'].mean().reset_index()

fig_cidade = px.bar(
    aqi_por_cidade.sort_values(
        by='indice_qualidade_ar',
        ascending=False
    ).head(20),
    x='cidade',
    y='indice_qualidade_ar',
    color='indice_qualidade_ar',
    color_continuous_scale='Plasma',
    template='plotly_white'
)

st.plotly_chart(fig_cidade, use_container_width=True)

# ---------------------------------------------------------
# 4. Poluentes
# ---------------------------------------------------------

st.write("### Concentração Média dos Principais Poluentes")

st.markdown("""
Os gráficos abaixo mostram as cidades com maior concentração média dos principais poluentes.

🧪 Poluentes analisados:
- PM2.5;
- PM10;
- NO2;
- CO;
- O3.

🔎 Objetivo:
Identificar quais poluentes predominam em cada cidade.
""")

poluentes = ['pm25', 'pm10', 'no2', 'co', 'o3']

for poluente in poluentes:

    st.write(f"#### Top Cidades - {poluente.upper()}")

    fig_poluente = px.bar(
        dados_filtrados.groupby('cidade')[poluente]
        .mean()
        .reset_index()
        .sort_values(by=poluente, ascending=False)
        .head(10),

        x='cidade',
        y=poluente,
        color=poluente,
        color_continuous_scale='Viridis',
        template='plotly_white'
    )

    st.plotly_chart(fig_poluente, use_container_width=True)

# ---------------------------------------------------------
# 5. Heatmap
# ---------------------------------------------------------

st.write("### Sazonalidade Mensal e Anual do Índice de Qualidade do Ar")

st.markdown("""
O mapa de calor mostra como a qualidade do ar varia ao longo dos meses e anos.

🎨 Quanto mais intensa a cor:
- Maior o índice médio de poluição.

🔎 O que analisar:
- Meses mais críticos;
- Tendências anuais;
- Influência climática.
""")

aqi_mensal_anual = dados_filtrados.groupby(
    ['mes_nome', 'ano']
)['indice_qualidade_ar'].mean().reset_index()

fig_mapa_calor = px.density_heatmap(
    aqi_mensal_anual,
    x='mes_nome',
    y='ano',
    z='indice_qualidade_ar',
    color_continuous_scale='Inferno',
    template='plotly_white'
)

st.plotly_chart(fig_mapa_calor, use_container_width=True)

# ---------------------------------------------------------
# 6. Correlação Temperatura x AQI
# ---------------------------------------------------------

st.write("### Correlação entre Temperatura Média e Índice de Qualidade do Ar")

st.markdown("""
Este gráfico avalia a relação entre temperatura média e qualidade do ar.

📌 Cada ponto representa uma cidade.

🔎 O que analisar:
- Relação entre calor e poluição;
- Diferenças regionais;
- Influência do PM2.5.
""")

fig_dispersao = px.scatter(
    dados_filtrados,
    x='temperatura_media',
    y='indice_qualidade_ar',
    color='regiao',
    size='pm25',
    hover_name='cidade',
    trendline='ols',
    template='plotly_white'
)

st.plotly_chart(fig_dispersao, use_container_width=True)

# ---------------------------------------------------------
# 7. Tabela dinâmica
# ---------------------------------------------------------

st.write("### Tabela Dinâmica: AQI Médio por Região e Cidade")

st.markdown("""
A tabela dinâmica permite explorar detalhadamente os índices médios de qualidade do ar.

🎯 Objetivo:
- Comparações detalhadas;
- Exploração regional;
- Apoio à tomada de decisão.
""")

tabela_dinamica_aqi = dados_filtrados.pivot_table(
    values='indice_qualidade_ar',
    index='regiao',
    columns='cidade',
    aggfunc='mean'
).fillna(0)

st.dataframe(
    tabela_dinamica_aqi.style.background_gradient(cmap='Blues')
)

# =========================================================
# CONCLUSÃO
# =========================================================

st.subheader('Interpretação dos Resultados e Conclusão')

st.markdown("""
A análise permite identificar padrões importantes sobre a qualidade do ar no Brasil.

📌 Principais insights:
- Regiões mais afetadas;
- Cidades críticas;
- Poluentes predominantes;
- Tendências sazonais;
- Relação entre clima e poluição.

Essas informações podem apoiar:
- Políticas públicas;
- Planejamento urbano;
- Monitoramento ambiental;
- Estratégias de sustentabilidade.
""")