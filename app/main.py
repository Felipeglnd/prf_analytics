import sys
from pathlib import Path
import pandas as pd
import streamlit as st

# ==========================================
# 0. Configuração do Path do Projeto
# ==========================================
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.append(str(RAIZ_PROJETO))

from src.data_loader import (
    carregar_dados,
    carregar_geojson,
    carregar_frota,
    carregar_relatorio_rodovias,
)

# Importação dos submódulos de abas
from views.tab_geral import render_tab_geral
from views.tab_vitimas import render_tab_vitimas
from views.tab_veiculos import render_tab_veiculos
from views.tab_acidentes import render_tab_acidentes

# ==========================================
# 1. Configurações Globais e Paleta Estilo PRF
# ==========================================
st.set_page_config(
    page_title="Dashboard PRF - Acidentes",
    page_icon="🚔",
    layout="wide"
)

# Paleta inspirada nos dashboards executivos da PRF
CORES_DASHBOARD = {
    'fundo_app': '#F1F5F9',          # Cinza/Azul muito claro para o fundo principal
    'fundo_sidebar': '#0F172A',      # Azul marinho bem escuro para a sidebar
    'card_fundo': '#FFFFFF',         # Fundo branco puro para os cards de KPIs
    'azul_escuro': '#0A192F',        # Azul marinho principal dos gráficos
    'azul_medio': '#1E3A8A',         # Azul intermediário
    'laranja_destaque': '#D97706',   # Laranja/âmbar para destaques executivos
    'amarelo_alerta': '#F59E0B',     # Amarelo/Dourado
    'texto_escuro': '#0F172A',       # Texto principal dos títulos e números
    'cinza_texto': '#64748B',        # Rótulos e eixos dos gráficos
    'cinza_borda': '#CBD5E1',        # Borda suave dos cards
    'branco': '#FFFFFF',             # Branco
    'vermelho': '#DC2626',           # Vermelho para alertas/óbitos
    'laranja': '#FFA500'
}

MESES_MAP = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}

ORDEM_DIAS = [
    "Domingo",
    "Segunda-Feira",
    "Terça-Feira",
    "Quarta-Feira",
    "Quinta-Feira",
    "Sexta-Feira",
    "Sábado",
]

# Estilização CSS personalizada (KPIs, Sidebar e Navbar de Topo)
st.markdown(
    f"""
    <style>
    /* Fundo geral da aplicação */
    .stApp {{
        background-color: {CORES_DASHBOARD['fundo_app']} !important;
        color: {CORES_DASHBOARD['texto_escuro']} !important;
    }}
    
    /* Sidebar em Azul Marinho Escuro */
    [data-testid="stSidebar"] {{
        background-color: {CORES_DASHBOARD['fundo_sidebar']} !important;
    }}

    [data-testid="stSidebar"] *, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {{
        color: {CORES_DASHBOARD['branco']} !important;
    }}
    
    /* Títulos em Azul Escuro Executivo */
    h1, h2, h3 {{
        color: {CORES_DASHBOARD['azul_escuro']} !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }}
    
    /* Textos e rótulos da página principal */
    .stMarkdown p, label, .stCaption {{
        color: {CORES_DASHBOARD['texto_escuro']} !important;
    }}

    /* Estilização do Container do Card de KPI */
    div[data-testid="metric-container"], div[data-testid="stMetric"] {{
        background-color: {CORES_DASHBOARD['card_fundo']} !important;
        border: 1px solid {CORES_DASHBOARD['cinza_borda']} !important;
        border-radius: 10px !important;
        padding: 16px !important;
        box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.06) !important;
    }}

    /* Rótulo do KPI */
    div[data-testid="metric-container"] [data-testid="stMetricLabel"],
    div[data-testid="metric-container"] [data-testid="stMetricLabel"] *,
    div[data-testid="stMetricLabel"] p,
    div[data-testid="stMetricLabel"] label {{
        color: {CORES_DASHBOARD['cinza_texto']} !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
    }}

    /* Valor numérico do KPI */
    div[data-testid="metric-container"] [data-testid="stMetricValue"],
    div[data-testid="metric-container"] [data-testid="stMetricValue"] *,
    div[data-testid="stMetricValue"] div,
    div[data-testid="stMetricValue"] span {{
        color: {CORES_DASHBOARD['azul_escuro']} !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
    }}

    /* Estilização da Navbar (Tabs no Topo) */
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {CORES_DASHBOARD['card_fundo']};
        padding: 8px 12px;
        border-radius: 10px;
        border: 1px solid {CORES_DASHBOARD['cinza_borda']};
        box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.04);
    }}

    div[data-testid="stTabs"] button[data-baseweb="tab"] {{
        font-size: 1rem !important;
        font-weight: 700 !important;
        color: {CORES_DASHBOARD['cinza_texto']} !important;
        border-radius: 6px !important;
        padding: 8px 18px !important;
        border: none !important;
    }}

    div[data-testid="stTabs"] button[aria-selected="true"] {{
        background-color: {CORES_DASHBOARD['azul_escuro']} !important;
        color: {CORES_DASHBOARD['branco']} !important;
    }}

    /* Linhas divisórias */
    hr {{
        border-color: {CORES_DASHBOARD['cinza_borda']} !important;
    }}
    
    .st-emotion-cache-csawen {{
        color: {CORES_DASHBOARD['texto_escuro']};    
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def formatar_numero(valor: float) -> str:
    """Formata inteiros com separador de milhar brasileiro."""
    return f"{int(valor):,}".replace(",", ".")


def aplicar_tema_grafico(fig):
    """Aplica o template claro do Plotly e força texto escuro em todos os elementos visuais."""
    fig.update_layout(
        template='plotly_white',
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(color=CORES_DASHBOARD['texto_escuro'], family="sans-serif", size=12),
        legend=dict(
            font=dict(color=CORES_DASHBOARD['texto_escuro'], size=12),
            title=dict(font=dict(color=CORES_DASHBOARD['texto_escuro']))
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#E2E8F0",
            zeroline=False,
            color=CORES_DASHBOARD['texto_escuro'],
            title=dict(font=dict(color=CORES_DASHBOARD['texto_escuro'])),
            tickfont=dict(color=CORES_DASHBOARD['texto_escuro'])
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#E2E8F0",
            zeroline=False,
            color=CORES_DASHBOARD['texto_escuro'],
            title=dict(font=dict(color=CORES_DASHBOARD['texto_escuro'])),
            tickfont=dict(color=CORES_DASHBOARD['texto_escuro'])
        ),
        coloraxis_colorbar=dict(
            title=dict(font=dict(color=CORES_DASHBOARD['texto_escuro'])),
            tickfont=dict(color=CORES_DASHBOARD['texto_escuro'])
        )
    )
    return fig


# ==========================================
# 2. Carga e Pré-processamento dos Dados
# ==========================================
df = carregar_dados()
df_frota = carregar_frota()
df_rodovias = carregar_relatorio_rodovias()

try:
    geojson_br = carregar_geojson()
except Exception as e:
    geojson_br = None
    st.warning(f"Não foi possível carregar o arquivo GeoJSON para o mapa: {e}")

# Mapeamento da coluna de estado físico da vítima para vitima_estado
if 'estado' in df.columns:
    df['vitima_estado'] = df['estado']
elif 'estado_fisico' in df.columns:
    df['vitima_estado'] = df['estado_fisico']

# Tratamento de datas e horas
if 'data_inversa' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['data_inversa']):
    df['data_inversa'] = pd.to_datetime(df['data_inversa'], errors='coerce')

if 'mes_num' not in df.columns and 'data_inversa' in df.columns:
    df['mes_num'] = df['data_inversa'].dt.month

if 'dia_semana' in df.columns:
    df['dia_nome'] = df['dia_semana'].astype(str).str.title()
elif 'data_inversa' in df.columns:
    dias_map = {
        0: "Segunda-Feira", 1: "Terça-Feira", 2: "Quarta-Feira",
        3: "Quinta-Feira", 4: "Sexta-Feira", 5: "Sábado", 6: "Domingo"
    }
    df['dia_nome'] = df['data_inversa'].dt.dayofweek.map(dias_map)

# Conversão numérica segura para contagens
if 'mortos' in df.columns:
    df['mortos'] = pd.to_numeric(df['mortos'], errors='coerce').fillna(0)
else:
    df['mortos'] = 0

if 'feridos_graves' in df.columns:
    df['feridos_graves'] = pd.to_numeric(df['feridos_graves'], errors='coerce').fillna(0)
else:
    df['feridos_graves'] = 0

# Tratamento da hora
if 'hora' in df.columns:
    df['hora_num'] = pd.to_datetime(df['hora'].astype(str), format='%H:%M:%S', errors='coerce').dt.hour
    if df['hora_num'].isnull().all():
        df['hora_num'] = pd.to_numeric(df['hora'], errors='coerce').fillna(-1).astype(int)
else:
    df['hora_num'] = -1

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

# Obtenção dinâmica dos valores de vitima_estado
if 'vitima_estado' in df.columns:
    vitima_estados_disponiveis = sorted(df['vitima_estado'].dropna().astype(str).unique())
else:
    vitima_estados_disponiveis = []

filtro_ano = st.sidebar.multiselect(
    "Ano Base",
    options=anos_disponiveis,
    default=[],
    placeholder="Filtre por ano",
)

filtro_uf = st.sidebar.multiselect(
    "Unidade da Federação (UF)",
    options=ufs_disponiveis,
    default=[],
    placeholder="Todas as UFs",
)

filtro_vitima_estado = st.sidebar.multiselect(
    "Estado da Vítima",
    options=vitima_estados_disponiveis,
    default=[],
    placeholder="Todos os estados da vítima",
)

df_filtrado = df.copy()

if filtro_ano:
    df_filtrado = df_filtrado[df_filtrado['ano_base'].isin(filtro_ano)]

if filtro_uf:
    df_filtrado = df_filtrado[df_filtrado['uf'].isin(filtro_uf)]

if filtro_vitima_estado:
    if 'vitima_estado' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['vitima_estado'].isin(filtro_vitima_estado)]
    else:
        # Fallback para colunas agregadas de contagem caso a tabela seja sumarizada por acidente
        mascara = False
        for est in filtro_vitima_estado:
            est_str = str(est).lower()
            for col_nome in ['ilesos', 'feridos_leves', 'feridos_graves', 'mortos']:
                if col_nome in est_str or est_str in col_nome:
                    if col_nome in df_filtrado.columns:
                        mascara = mascara | (df_filtrado[col_nome] > 0)
        if isinstance(mascara, pd.Series):
            df_filtrado = df_filtrado[mascara]

# ==========================================
# 4. Cabeçalho e KPIs Principais
# ==========================================
st.title("Acidentes em Rodovias Federais (PRF)")

# Menu sanfona para ocultar/exibir as fontes dos dados
with st.expander("📌 Ver Fontes das Informações", expanded=False):
    st.markdown("**Dados abertos PRF:** *https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf*")
    st.markdown("**Frota de veículos 2023:** *https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/frota-de-veiculos-2023*")
    st.markdown("**Frota de veículos 2024:** *https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/frota-de-veiculos-2024*")
    st.markdown("**Frota de veículos 2025:** *https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/frota-de-veiculos-2025*")
    st.markdown("**Plano Nacional de Viação e Sistema Nacional de Viação:** *https://www.gov.br/dnit/pt-br/assuntos/atlas-e-mapas/pnv-e-snv*")

# Contagem única de acidentes
if 'id' in df_filtrado.columns:
    total_acidentes = df_filtrado['id'].nunique()
else:
    total_acidentes = len(df_filtrado)

# Totais absolutos
total_obitos = int(df_filtrado['mortos'].sum()) if total_acidentes > 0 else 0
total_feridos_graves = int(df_filtrado['feridos_graves'].sum()) if total_acidentes > 0 else 0

# Cálculo da taxa de acidentes fatais
if total_acidentes > 0:
    if 'mortos' in df_filtrado.columns and df_filtrado['mortos'].sum() > 0:
        acidentes_fatais = (df_filtrado['mortos'] > 0).sum()
    elif 'classificacao_acidente' in df_filtrado.columns:
        acidentes_fatais = df_filtrado['classificacao_acidente'].astype(str).str.contains('fatal', case=False, na=False).sum()
    else:
        acidentes_fatais = 0
        
    tx_fatalidade = (acidentes_fatais / total_acidentes) * 100
else:
    tx_fatalidade = 0.0

# Renderização dos KPIs no Streamlit
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Acidentes de Trânsito", formatar_numero(total_acidentes))
kpi2.metric("Quantidade de Feridos Graves", formatar_numero(total_feridos_graves))
kpi3.metric("Quantidade de Fatalidades", formatar_numero(total_obitos))
kpi4.metric("Taxa de Acidentes Fatais", f"{tx_fatalidade:.1f}%")

st.markdown("---")

# ==========================================
# 5. Renderização das Abas (Modularizadas)
# ==========================================
tab_geral, tab_vitimas, tab_veiculos, tab_acidentes = st.tabs([
    "📊 Geral", 
    "👥 Perfil Vítimas", 
    "🚗 Perfil Veículos", 
    "🚨 Perfil Acidentes"
])

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
else:
    with tab_geral:
        render_tab_geral(
            df_filtrado, df_frota, geojson_br, CORES_DASHBOARD, MESES_MAP, filtro_ano, aplicar_tema_grafico
        )

    with tab_vitimas:
        render_tab_vitimas(
            df_filtrado, CORES_DASHBOARD, aplicar_tema_grafico
        )

    with tab_veiculos:
        render_tab_veiculos(
            df_filtrado, CORES_DASHBOARD, aplicar_tema_grafico
        )

    with tab_acidentes:
        render_tab_acidentes(
            df_filtrado, df_rodovias, CORES_DASHBOARD, ORDEM_DIAS, filtro_ano, aplicar_tema_grafico
        )
