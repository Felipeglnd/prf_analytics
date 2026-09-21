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

from src.data_loader import carregar_dados

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

# Garantir tipos de dados pré-processados para otimizar requisições repetidas
if 'data_inversa' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['data_inversa']):
    df['data_inversa'] = pd.to_datetime(df['data_inversa'])

if 'mes_num' not in df.columns and 'data_inversa' in df.columns:
    df['mes_num'] = df['data_inversa'].dt.month

# ==========================================
# 3. Sidebar - Filtros Interativos
# ==========================================
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/e/e0/Bras%C3%A3o_da_Pol%C3%ADcia_Rodovi%C3%A1ria_Federal.png",
    width=120,
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
        st.plotly_chart(aplicar_tema_grafico(fig_line), use_container_width=True)

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
        st.plotly_chart(aplicar_tema_grafico(fig_bar), use_container_width=True)

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
        st.plotly_chart(aplicar_tema_grafico(fig_donut), use_container_width=True)

    with col4:
        st.subheader("Acidentes Fatais por UF")

        uf_fatais = (
            df_filtrado.groupby('uf')['mortos']
            .sum()
            .reset_index()
            .sort_values('mortos', ascending=False)
        )

        fig_uf = px.bar(
            uf_fatais,
            x='uf',
            y='mortos',
            color='mortos',
            color_continuous_scale=[
                CORES_PRF['creme'],
                CORES_PRF['amarelo_ouro'],
                CORES_PRF['azul_marinho'],
            ],
        )
        fig_uf.update_layout(
            xaxis_title="Estado (UF)",
            yaxis_title="Total de Óbitos",
            coloraxis_showscale=False,
        )
        st.plotly_chart(aplicar_tema_grafico(fig_uf), use_container_width=True)
