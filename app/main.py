import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

# ==========================================
# 0. Configuração do Path do Projeto
# ==========================================
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.append(str(RAIZ_PROJETO))

from src.data_loader import carregar_dados, carregar_geojson

# ==========================================
# 1. Configurações Globais e Paleta PRF
# ==========================================
st.set_page_config(
    page_title="Dashboard PRF - Acidentes",
    page_icon="🚔",
    layout="wide"
)

CORES_PRF = {
    'azul_marinho': '#002855',
    'dourado_destaque': '#D97706',
    'amarelo_ouro': '#E6A100',
    'creme': '#FFF9E6',
    'cinza_neutro': '#7A8D9B',
    'cinza_texto': '#1E293B',
    'vermelho': '#FF0000',
}

MESES_MAP = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}

# Lista com hífens e maiúsculas padronizadas após o .str.title()
ORDEM_DIAS = [
    "Domingo",
    "Segunda-Feira",
    "Terça-Feira",
    "Quarta-Feira",
    "Quinta-Feira",
    "Sexta-Feira",
    "Sábado",
]

# Estilização CSS personalizada
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: #0d1117;
    }}
    h1, h2, h3 {{
        color: {CORES_PRF['amarelo_ouro']};
    }}
    div[data-testid="metric-container"] {{
        background-color: #161b22;
        border: 1px solid {CORES_PRF['amarelo_ouro']};
        padding: 15px;
        border-radius: 8px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def formatar_numero(valor: float) -> str:
    """Formata inteiros com separador de milhar brasileiro."""
    return f"{int(valor):,}".replace(",", ".")


def aplicar_tema_grafico(fig):
    """Aplica o tema base transparente e formatação visual dos gráficos Plotly."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(color="#E6EDF3"),
    )
    return fig


# ==========================================
# 2. Carga e Pré-processamento dos Dados
# ==========================================
df = carregar_dados()

try:
    geojson_br = carregar_geojson()
except Exception as e:
    geojson_br = None
    st.warning(f"Não foi possível carregar o arquivo GeoJSON para o mapa: {e}")

# Garantir tipos de dados pré-processados
if 'data_inversa' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['data_inversa']):
    df['data_inversa'] = pd.to_datetime(df['data_inversa'])

if 'mes_num' not in df.columns and 'data_inversa' in df.columns:
    df['mes_num'] = df['data_inversa'].dt.month

# Pré-processamento da coluna de dia da semana
if 'dia_semana' in df.columns:
    df['dia_nome'] = df['dia_semana'].astype(str).str.title()
elif 'data_inversa' in df.columns:
    dias_map = {
        0: "Segunda-Feira", 1: "Terça-Feira", 2: "Quarta-Feira",
        3: "Quinta-Feira", 4: "Sexta-Feira", 5: "Sábado", 6: "Domingo"
    }
    df['dia_nome'] = df['data_inversa'].dt.dayofweek.map(dias_map)

# ==========================================
# 3. Sidebar - Filtros Interativos
# ==========================================
st.sidebar.image(
    "https://whitecube.com.br/wp-content/uploads/2026/04/social-share.png",
    width=260,
)
st.sidebar.title("Filtros Analíticos")

anos_disponiveis = sorted(df['ano_base'].dropna().astype(int).unique()) if 'ano_base' in df.columns else []
ufs_disponiveis = sorted(df['uf'].dropna().unique()) if 'uf' in df.columns else []

filtro_ano = st.sidebar.multiselect(
    "Ano Base",
    options=anos_disponiveis,
    default=[],
    placeholder="Todos os anos",
)

filtro_uf = st.sidebar.multiselect(
    "Unidade da Federação (UF)",
    options=ufs_disponiveis,
    default=[],
    placeholder="Todas as UFs",
)

# Aplicar filtros condicionais
df_filtrado = df.copy()

if filtro_ano:
    df_filtrado = df_filtrado[df_filtrado['ano_base'].isin(filtro_ano)]

if filtro_uf:
    df_filtrado = df_filtrado[df_filtrado['uf'].isin(filtro_uf)]

# ==========================================
# 4. Layout Principal - KPIs
# ==========================================
st.title("Acidentes em Rodovias Federais (PRF)")

texto_anos = " | ".join(map(str, filtro_ano)) if filtro_ano else "Todos os anos disponíveis"
texto_ufs = " | ".join(filtro_uf) if filtro_uf else "Todas as UFs"
st.markdown(f"**Anos:** {texto_anos} — **UFs:** {texto_ufs} — **Visão:** Ocorrências únicas por acidente.")

# Cálculo das métricas
total_acidentes = len(df_filtrado)
total_obitos = df_filtrado['mortos'].sum() if 'mortos' in df_filtrado.columns and total_acidentes > 0 else 0
total_feridos_graves = df_filtrado['feridos_graves'].sum() if 'feridos_graves' in df_filtrado.columns and total_acidentes > 0 else 0

if total_acidentes > 0 and 'classificacao_acidente' in df_filtrado.columns:
    acidentes_fatais = (df_filtrado['classificacao_acidente'] == 'Com Vítimas Fatais').sum()
    tx_fatalidade = (acidentes_fatais / total_acidentes) * 100
else:
    tx_fatalidade = 0.0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total de Acidentes", formatar_numero(total_acidentes))
kpi2.metric("Total de Óbitos", formatar_numero(total_obitos))
kpi3.metric("Feridos Graves", formatar_numero(total_feridos_graves))
kpi4.metric("Taxa de Acidentes Fatais", f"{tx_fatalidade:.1f}%")

st.markdown("---")

# ==========================================
# 5. Gráficos Analíticos
# ==========================================
if df_filtrado.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
else:
    # Linha 1: Evolução Mensal e Principais Causas
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Evolução Mensal de Acidentes")

        evolucao = (
            df_filtrado.groupby(['mes_num', 'ano_base'])
            .size()
            .reset_index(name='total')
        )
        evolucao['mes_nome'] = evolucao['mes_num'].map(MESES_MAP)
        evolucao['ano_base'] = evolucao['ano_base'].astype(str)

        fig_line = px.line(
            evolucao,
            x='mes_nome',
            y='total',
            color='ano_base',
            category_orders={'mes_nome': list(MESES_MAP.values())},
            color_discrete_sequence=[
                CORES_PRF['cinza_neutro'],
                CORES_PRF['amarelo_ouro'],
                CORES_PRF['vermelho'],
            ],
        )
        fig_line.update_layout(xaxis_title="Mês", yaxis_title="Volume de Acidentes")
        st.plotly_chart(aplicar_tema_grafico(fig_line), width="stretch")

    with col2:
        st.subheader("Principais Causas de Acidentes")

        causas = df_filtrado['causa_acidente'].value_counts().head(5).reset_index()
        causas.columns = ['Causa', 'Total']

        fig_bar = px.bar(
            causas,
            x='Total',
            y='Causa',
            orientation='h',
            color_discrete_sequence=[CORES_PRF['azul_marinho']],
        )

        if len(fig_bar.data) > 0:
            fig_bar.data[0].marker.color = [
                CORES_PRF['dourado_destaque'] if i == 0 else CORES_PRF['azul_marinho']
                for i in range(len(causas))
            ]

        fig_bar.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            xaxis_title="",
            yaxis_title="",
        )
        st.plotly_chart(aplicar_tema_grafico(fig_bar), width="stretch")

    # Linha 2: Gravidade e Óbitos por UF
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Classificação de Gravidade")

        gravidade = df_filtrado['classificacao_acidente'].value_counts().reset_index()
        gravidade.columns = ['Classificação', 'Total']

        fig_donut = px.pie(
            gravidade,
            values='Total',
            names='Classificação',
            hole=0.5,
            color_discrete_sequence=[
                CORES_PRF['azul_marinho'],
                CORES_PRF['amarelo_ouro'],
                CORES_PRF['dourado_destaque'],
            ],
        )
        st.plotly_chart(aplicar_tema_grafico(fig_donut), width="stretch")

    with col4:
        st.subheader("Mapa Coroplético: Óbitos por UF")

        uf_fatais = (
            df_filtrado.groupby('uf')['mortos']
            .sum()
            .reset_index()
        )

        if geojson_br:
            fig_uf_mapa = px.choropleth(
                uf_fatais,
                geojson=geojson_br,
                locations='uf',
                featureidkey='properties.sigla',
                color='mortos',
                color_continuous_scale=[
                    CORES_PRF['creme'],
                    CORES_PRF['amarelo_ouro'],
                    CORES_PRF['vermelho'],
                ],
                labels={'mortos': 'Óbitos', 'uf': 'UF'},
            )
            fig_uf_mapa.update_geos(fitbounds="locations", visible=False)
            st.plotly_chart(aplicar_tema_grafico(fig_uf_mapa), width="stretch")
        else:
            fig_uf = px.bar(
                uf_fatais.sort_values('mortos', ascending=False),
                x='uf',
                y='mortos',
                color='mortos',
                color_continuous_scale=[
                    CORES_PRF['creme'],
                    CORES_PRF['amarelo_ouro'],
                    CORES_PRF['azul_marinho'],
                ],
            )
            fig_uf.update_layout(xaxis_title="Estado (UF)", yaxis_title="Total de Óbitos", coloraxis_showscale=False)
            st.plotly_chart(aplicar_tema_grafico(fig_uf), width="stretch")

    # Linha 3: Dia da Semana e Top Rodovias (BRs)
    col5, col6 = st.columns(2)

    with col5:
        st.subheader("Acidentes por Dia da Semana")

        if 'dia_nome' in df_filtrado.columns:
            acidentes_dia = (
                df_filtrado.groupby('dia_nome')
                .size()
                .reindex(ORDEM_DIAS, fill_value=0)
                .reset_index(name='total')
            )

            fig_dias = px.bar(
                acidentes_dia,
                x='dia_nome',
                y='total',
                labels={'dia_nome': 'Dia da Semana', 'total': 'Total de Acidentes'},
                color='total',
                color_continuous_scale=[
                    CORES_PRF['azul_marinho'],
                    CORES_PRF['amarelo_ouro'],
                    CORES_PRF['vermelho'],
                ],
            )
            fig_dias.update_layout(
                xaxis_title="",
                yaxis_title="Total de Acidentes",
                coloraxis_showscale=False,
            )
            st.plotly_chart(aplicar_tema_grafico(fig_dias), width="stretch")

    with col6:
        st.subheader("Top 5 Rodovias (BRs) com Mais Acidentes")

        if 'br' in df_filtrado.columns:
            df_brs = df_filtrado.dropna(subset=['br']).copy()
            df_brs['br'] = "BR-" + df_brs['br'].astype(str).str.split('.').str[0].str.zfill(3)
            top_brs = df_brs['br'].value_counts().head(5).reset_index()
            top_brs.columns = ['Rodovia', 'Total']

            fig_brs = px.bar(
                top_brs,
                x='Total',
                y='Rodovia',
                orientation='h',
                color_discrete_sequence=[CORES_PRF['azul_marinho']],
            )
            if len(fig_brs.data) > 0:
                fig_brs.data[0].marker.color = [
                    CORES_PRF['dourado_destaque'] if i == 0 else CORES_PRF['azul_marinho']
                    for i in range(len(top_brs))
                ]
            fig_brs.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title="",
                yaxis_title="",
            )
            st.plotly_chart(aplicar_tema_grafico(fig_brs), width="stretch")

    # ==========================================
    # 6. Seção Expandida - Mapeamento Geográfico Detalhado
    # ==========================================
    st.markdown("---")
    st.subheader("📍 Mapeamento Geográfico de Ocorrências (Latitude / Longitude)")

    df_coords = df_filtrado.dropna(subset=['latitude', 'longitude'])

    if not df_coords.empty:
        if len(df_coords) > 10000:
            st.caption("Exibindo amostragem de 10.000 pontos para garantir alta performance.")
            df_coords = df_coords.sample(10000, random_state=42)

        fig_scatter_map = px.scatter_map(
            df_coords,
            lat='latitude',
            lon='longitude',
            color='classificacao_acidente' if 'classificacao_acidente' in df_coords.columns else None,
            hover_name='municipio' if 'municipio' in df_coords.columns else 'uf',
            hover_data=['br', 'km', 'mortos'] if 'br' in df_coords.columns else ['mortos'],
            zoom=3.5,
            center={"lat": -14.2350, "lon": -51.9253},
            map_style="carto-darkmatter",
        )
        fig_scatter_map.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(aplicar_tema_grafico(fig_scatter_map), width="stretch")
    else:
        st.warning("Não há coordenadas geográficas válidas para os filtros selecionados.")
