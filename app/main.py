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

from src.data_loader import (
    carregar_dados,
    carregar_geojson,
    carregar_frota,
    carregar_relatorio_rodovias,
)

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

filtro_ano = st.sidebar.multiselect(
    "Ano Base",
    options=anos_disponiveis,
    default=[],
    placeholder="filtre por ano",
)

filtro_uf = st.sidebar.multiselect(
    "Unidade da Federação (UF)",
    options=ufs_disponiveis,
    default=[],
    placeholder="Todas as UFs",
)

df_filtrado = df.copy()

if filtro_ano:
    df_filtrado = df_filtrado[df_filtrado['ano_base'].isin(filtro_ano)]

if filtro_uf:
    df_filtrado = df_filtrado[df_filtrado['uf'].isin(filtro_uf)]

# ==========================================
# 4. Cabeçalho e KPIs Principais
# ==========================================
st.title("Acidentes em Rodovias Federais (PRF)")

texto_anos = " | ".join(map(str, filtro_ano)) if filtro_ano else " 2023, 2024, 2025"
texto_ufs = " | ".join(filtro_uf) if filtro_uf else "Todas as UFs"
st.markdown(f"**Dados abertos PRF:** *https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf*")
st.markdown(f"**Frota de veículos 2023:** *https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/frota-de-veiculos-2023*")
st.markdown(f"**Frota de veículos 2024:** *https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/frota-de-veiculos-2024*")
st.markdown(f"**Frota de veículos 2025:** *https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/frota-de-veiculos-2025*")
st.markdown(f"**Plano Nacional de Viação e Sistema Nacional de Viação:** *https://www.gov.br/dnit/pt-br/assuntos/atlas-e-mapas/pnv-e-snv*")


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
# 5. Navbar de Navegação Superior (Tabs)
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
    # ----------------------------------------------------
    # ABA 1: GERAL
    # ----------------------------------------------------
    with tab_geral:
        st.subheader("Visão Geral e Evolução Temporal")
        
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("##### Evolução Mensal de Acidentes")
            if 'mes_num' in df_filtrado.columns and 'ano_base' in df_filtrado.columns:
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
                        CORES_DASHBOARD['vermelho'],
                        CORES_DASHBOARD['laranja'],
                        CORES_DASHBOARD['azul_medio'],
                    ],
                )
                fig_line.update_layout(xaxis_title="Mês", yaxis_title="Volume de Acidentes")
                st.plotly_chart(aplicar_tema_grafico(fig_line), use_container_width=True)

        with col_g2:
            st.markdown("##### Mapa Coroplético: Óbitos por UF")
            if 'uf' in df_filtrado.columns:
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
                            "#E2E8F0",
                            CORES_DASHBOARD['azul_medio'],
                            CORES_DASHBOARD['vermelho'],
                        ],
                        labels={'mortos': 'Óbitos', 'uf': 'UF'},
                    )
                    fig_uf_mapa.update_geos(fitbounds="locations", visible=False)
                    st.plotly_chart(aplicar_tema_grafico(fig_uf_mapa), use_container_width=True)
                else:
                    fig_uf = px.bar(
                        uf_fatais.sort_values('mortos', ascending=False),
                        x='uf',
                        y='mortos',
                        color='mortos',
                        color_continuous_scale=[
                            "#E2E8F0",
                            CORES_DASHBOARD['vermelho'],
                        ],
                    )
                    fig_uf.update_layout(xaxis_title="Estado (UF)", yaxis_title="Total de Óbitos", coloraxis_showscale=False)
                    st.plotly_chart(aplicar_tema_grafico(fig_uf), use_container_width=True)

        # =====================================================================
        # NOVA SEÇÃO: Frota vs Acidentes & Condições Meteorológicas
        # =====================================================================
        st.markdown("---")
        
        col_g3, col_g4 = st.columns(2)

        with col_g3:
            st.markdown("##### Taxa de Acidentes vs Frota (por UF)")
            st.caption("Acidentes (ID único) a cada 10 mil veículos registrados no estado")
            
            if 'uf' in df_filtrado.columns and not df_frota.empty:
                # 1. Total de Acidentes ÚNICOS por UF
                if 'id' in df_filtrado.columns:
                    acidentes_uf = df_filtrado.groupby('uf')['id'].nunique().reset_index()
                    acidentes_uf.columns = ['uf', 'total_acidentes']
                else:
                    # Fallback caso a coluna ID não exista
                    acidentes_uf = df_filtrado['uf'].value_counts().reset_index()
                    acidentes_uf.columns = ['uf', 'total_acidentes']
                
                # 2. Filtrar e agregar a Frota por UF
                df_frota_filtrada = df_frota.copy()
                if filtro_ano and 'ano' in df_frota_filtrada.columns:
                    df_frota_filtrada = df_frota_filtrada[df_frota_filtrada['ano'].isin(filtro_ano)]
                
                if 'qtd_veiculos' in df_frota_filtrada.columns:
                    # Garantir que qtd_veiculos é numérico
                    df_frota_filtrada['qtd_veiculos'] = pd.to_numeric(df_frota_filtrada['qtd_veiculos'], errors='coerce').fillna(0)
                    frota_uf = df_frota_filtrada.groupby('uf')['qtd_veiculos'].sum().reset_index()
                    
                    # 3. Mesclar as duas bases e calcular a razão
                    df_taxa_frota = pd.merge(acidentes_uf, frota_uf, on='uf', how='inner')
                    df_taxa_frota = df_taxa_frota[df_taxa_frota['qtd_veiculos'] > 0].copy()
                    
                    # Cálculo: (Acidentes / Frota) * 10.000 para facilitar a leitura no gráfico
                    df_taxa_frota['taxa_10k'] = (df_taxa_frota['total_acidentes'] / df_taxa_frota['qtd_veiculos']) * 10000
                    
                    if not df_taxa_frota.empty:
                        # Ordenar para o gráfico de barras
                        df_taxa_frota = df_taxa_frota.sort_values('taxa_10k', ascending=True)
                        altura_grafico = max(300, len(df_taxa_frota) * 26)
                        max_taxa = df_taxa_frota['taxa_10k'].max()
                        
                        fig_taxa_f = px.bar(
                            df_taxa_frota,
                            x='taxa_10k',
                            y='uf',
                            orientation='h',
                            text='taxa_10k',
                            labels={
                                'taxa_10k': 'Acidentes por 10 mil veículos',
                                'uf': 'UF'
                            },
                            color_discrete_sequence=[CORES_DASHBOARD['azul_escuro']]
                        )
                        
                        fig_taxa_f = aplicar_tema_grafico(fig_taxa_f)
                        
                        fig_taxa_f.update_traces(
                            texttemplate='%{text:.2f}', 
                            textposition='outside', 
                            cliponaxis=False,
                            textfont=dict(color=CORES_DASHBOARD['texto_escuro'], size=10)
                        )
                        
                        fig_taxa_f.update_layout(
                            yaxis={
                                'categoryorder': 'total ascending',
                                'tickfont': dict(size=11),
                                'automargin': True
                            },
                            xaxis=dict(
                                range=[0, max_taxa * 1.15],
                                showgrid=True,
                                zeroline=False
                            ),
                            xaxis_title="",
                            yaxis_title="",
                            margin=dict(l=0, r=40, t=10, b=10),
                            height=altura_grafico
                        )
                        
                        with st.container(height=380):
                            st.plotly_chart(fig_taxa_f, use_container_width=True)
                    else:
                        st.info("Não foi possível correlacionar os dados de frota e acidentes para os filtros selecionados.")
                else:
                    st.warning("A coluna 'qtd_veiculos' não foi encontrada na base de frota.")

        with col_g4:
            st.markdown("##### Acidentes por Condição Meteorológica")
            if 'condicao_metereologica' in df_filtrado.columns:
                
                condicoes_unicas = sorted(df_filtrado['condicao_metereologica'].dropna().unique())
                
                condicoes_selecionadas = st.multiselect(
                    "Filtrar Condição(ões) Meteorológica(s):",
                    options=condicoes_unicas,
                    default=[],
                    placeholder="Selecione para filtrar...",
                    key="filtro_clima_multiselect"
                )
                
                df_clima = df_filtrado.copy()
                if condicoes_selecionadas:
                    df_clima = df_clima[df_clima['condicao_metereologica'].isin(condicoes_selecionadas)]
                    
                clima_counts = df_clima['condicao_metereologica'].value_counts().reset_index()
                clima_counts.columns = ['Condição', 'Total']
                
                altura_real_clima = max(300, len(clima_counts) * 30)
                max_clima = clima_counts['Total'].max() if not clima_counts.empty else 100
                
                fig_clima = px.bar(
                    clima_counts,
                    x='Total',
                    y='Condição',
                    orientation='h',
                    text='Total',
                    color_discrete_sequence=[CORES_DASHBOARD['azul_medio']]
                )
                
                fig_clima = aplicar_tema_grafico(fig_clima)
                
                fig_clima.update_traces(
                    textposition='outside', 
                    cliponaxis=False,
                    textfont=dict(color=CORES_DASHBOARD['texto_escuro'], size=10)
                )
                
                fig_clima.update_layout(
                    yaxis={
                        'categoryorder': 'total ascending',
                        'tickfont': dict(size=11),
                        'automargin': True
                    },
                    xaxis=dict(
                        range=[0, max_clima * 1.15],
                        showgrid=True,
                        zeroline=False
                    ),
                    xaxis_title="",
                    yaxis_title="",
                    margin=dict(l=0, r=40, t=10, b=10),
                    height=altura_real_clima
                )
                
                with st.container(height=380):
                    st.plotly_chart(fig_clima, use_container_width=True)
            else:
                st.warning("Coluna 'condicao_metereologica' não encontrada nos dados.")
        # =====================================================================

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
                map_style="carto-positron",
                color_discrete_sequence=[
                    CORES_DASHBOARD['azul_escuro'],
                    CORES_DASHBOARD['vermelho'],
                    CORES_DASHBOARD['laranja_destaque'],
                ],
            )
            fig_scatter_map.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(aplicar_tema_grafico(fig_scatter_map), use_container_width=True)
        else:
            st.warning("Não há coordenadas geográficas válidas para os filtros selecionados.")

    # ----------------------------------------------------
    # ABA 2: PERFIL VÍTIMAS
    # ----------------------------------------------------
    with tab_vitimas:
        st.subheader("Análise do Perfil das Vítimas e Gravidade")

        col_v1, col_v2 = st.columns(2)

        with col_v1:
            st.markdown("##### Classificação de Gravidade das Ocorrências")
            if 'classificacao_acidente' in df_filtrado.columns:
                gravidade = df_filtrado['classificacao_acidente'].value_counts().reset_index()
                gravidade.columns = ['Classificação', 'Total']

                fig_donut = px.pie(
                    gravidade,
                    values='Total',
                    names='Classificação',
                    hole=0.55,
                    color_discrete_sequence=[
                        CORES_DASHBOARD['azul_escuro'],
                        CORES_DASHBOARD['laranja_destaque'],
                        CORES_DASHBOARD['amarelo_alerta'],
                        CORES_DASHBOARD['vermelho'],
                    ],
                )
                fig_donut.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    insidetextfont=dict(color='#FFFFFF'),
                    outsidetextfont=dict(color=CORES_DASHBOARD['texto_escuro'])
                )
                st.plotly_chart(aplicar_tema_grafico(fig_donut), use_container_width=True)

        with col_v2:
            st.markdown("##### Total de Feridos Graves vs Óbitos por UF")
            if 'uf' in df_filtrado.columns and 'mortos' in df_filtrado.columns:
                df_vitimas_uf = df_filtrado.groupby('uf')[['mortos', 'feridos_graves']].sum().reset_index()
                df_vitimas_uf = df_vitimas_uf.sort_values('mortos', ascending=False).head(10)

                fig_vit_bar = px.bar(
                    df_vitimas_uf,
                    x='uf',
                    y=['mortos', 'feridos_graves'],
                    barmode='group',
                    labels={'value': 'Quantidade', 'variable': 'Métrica', 'uf': 'UF'},
                    color_discrete_map={
                        'mortos': CORES_DASHBOARD['vermelho'],
                        'feridos_graves': CORES_DASHBOARD['laranja_destaque']
                    }
                )
                st.plotly_chart(aplicar_tema_grafico(fig_vit_bar), use_container_width=True)

    # ----------------------------------------------------
    # ABA 3: PERFIL VEÍCULOS
    # ----------------------------------------------------
    with tab_veiculos:
        st.subheader("Análise dos Tipos de Veículos Envolvidos")

        col_veic1, col_veic2 = st.columns(2)

        with col_veic1:
            st.markdown("##### Distribuição de Acidentes por Tipo de Veículo")
            if 'tipo_veiculo' in df_filtrado.columns:
                top_veiculos = (
                    df_filtrado['tipo_veiculo']
                    .dropna()
                    .astype(str)
                    .str.title()
                    .value_counts()
                    .head(7)
                    .reset_index()
                )
                top_veiculos.columns = ['Tipo de Veículo', 'Total']

                fig_veiculo = px.pie(
                    top_veiculos,
                    values='Total',
                    names='Tipo de Veículo',
                    hole=0.55,
                    color_discrete_sequence=[
                        CORES_DASHBOARD['azul_escuro'],
                        CORES_DASHBOARD['laranja_destaque'],
                        CORES_DASHBOARD['azul_medio'],
                        CORES_DASHBOARD['amarelo_alerta'],
                        '#64748B',
                        '#94A3B8',
                        '#CBD5E1',
                    ],
                )
                fig_veiculo.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    insidetextfont=dict(color='#FFFFFF'),
                    outsidetextfont=dict(color=CORES_DASHBOARD['texto_escuro'])
                )
                st.plotly_chart(aplicar_tema_grafico(fig_veiculo), use_container_width=True)

        with col_veic2:
            st.markdown("##### Volume Total por Categoria de Veículo")
            if 'tipo_veiculo' in df_filtrado.columns:
                top_veic_bar = (
                    df_filtrado['tipo_veiculo']
                    .dropna()
                    .astype(str)
                    .str.title()
                    .value_counts()
                    .head(10)
                    .reset_index()
                )
                top_veic_bar.columns = ['Veículo', 'Total']

                fig_veic_bar = px.bar(
                    top_veic_bar,
                    x='Total',
                    y='Veículo',
                    orientation='h',
                    text='Total',
                    color_discrete_sequence=[CORES_DASHBOARD['azul_escuro']]
                )
                fig_veic_bar.update_traces(textposition='outside', textfont=dict(color=CORES_DASHBOARD['texto_escuro']))
                fig_veic_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(aplicar_tema_grafico(fig_veic_bar), use_container_width=True)

    # ----------------------------------------------------
    # ABA 4: PERFIL ACIDENTES
    # ----------------------------------------------------
    with tab_acidentes:
        st.subheader("Análise Operacional das Ocorrências")

        col_a1, col_a2 = st.columns(2)

        with col_a1:
            st.markdown("##### Principais Causas de Acidentes")
            if 'causa_acidente' in df_filtrado.columns:
                causas_unicas = sorted(df_filtrado['causa_acidente'].dropna().unique())

                causas_selecionadas = st.multiselect(
                    "Buscar causa(s) específica(s):",
                    options=causas_unicas,
                    default=[],
                    placeholder="Digite para filtrar causas...",
                    key="filtro_causas_multiselect"
                )

                df_causas = df_filtrado.copy()

                if causas_selecionadas:
                    df_causas = df_causas[df_causas['causa_acidente'].isin(causas_selecionadas)]

                causas = df_causas['causa_acidente'].value_counts().reset_index()
                causas.columns = ['Causa', 'Total']

                causas['Causa_Curta'] = causas['Causa'].apply(
                    lambda x: str(x)[:35] + '...' if len(str(x)) > 35 else str(x)
                )

                altura_real_grafico = max(300, len(causas) * 26)
                max_total = causas['Total'].max() if not causas.empty else 100

                fig_bar = px.bar(
                    causas,
                    x='Total',
                    y='Causa',
                    orientation='h',
                    text='Total',
                    color_discrete_sequence=[CORES_DASHBOARD['laranja_destaque']],
                )

                fig_bar = aplicar_tema_grafico(fig_bar)

                fig_bar.update_traces(
                    textposition='outside', 
                    cliponaxis=False,
                    textfont=dict(color=CORES_DASHBOARD['texto_escuro'], size=10)
                )

                fig_bar.update_layout(
                    yaxis={
                        'categoryorder': 'total ascending',
                        'tickfont': dict(size=11),
                        'automargin': True
                    },
                    xaxis=dict(
                        range=[0, max_total * 1.10],
                        showgrid=True,
                        zeroline=False
                    ),
                    xaxis_title="",
                    yaxis_title="",
                    margin=dict(l=0, r=60, t=10, b=10),
                    height=altura_real_grafico
                )

                with st.container(height=380):
                    st.plotly_chart(
                        fig_bar, 
                        use_container_width=True
                    )
                    
        with col_a2:
            st.markdown("##### Rodovias (BRs) com Mais Acidentes")
            if 'br' in df_filtrado.columns:
                df_brs = df_filtrado.dropna(subset=['br']).copy()
                df_brs['br_formatada'] = "BR-" + df_brs['br'].astype(str).str.split('.').str[0].str.zfill(3)

                brs_unicas = sorted(df_brs['br_formatada'].unique())

                brs_selecionadas = st.multiselect(
                    "Buscar rodovia(s) específica(s):",
                    options=brs_unicas,
                    default=[],
                    placeholder="Digite para filtrar rodovias...",
                    key="filtro_brs_multiselect"
                )

                if brs_selecionadas:
                    df_brs = df_brs[df_brs['br_formatada'].isin(brs_selecionadas)]

                top_brs = df_brs['br_formatada'].value_counts().reset_index()
                top_brs.columns = ['Rodovia', 'Total']

                altura_real_grafico_br = max(300, len(top_brs) * 26)
                max_total_br = top_brs['Total'].max() if not top_brs.empty else 100

                fig_brs = px.bar(
                    top_brs,
                    x='Total',
                    y='Rodovia',
                    orientation='h',
                    text='Total',
                    color_discrete_sequence=[CORES_DASHBOARD['azul_escuro']],
                )
                
                fig_brs = aplicar_tema_grafico(fig_brs)
                
                fig_brs.update_traces(
                    textposition='outside', 
                    cliponaxis=False,
                    textfont=dict(color=CORES_DASHBOARD['texto_escuro'], size=10)
                )
                
                fig_brs.update_layout(
                    yaxis={
                        'categoryorder': 'total ascending',
                        'tickfont': dict(size=11),
                        'automargin': True
                    },
                    xaxis=dict(
                        range=[0, max_total_br * 1.15],
                        showgrid=True,
                        zeroline=False
                    ),
                    xaxis_title="",
                    yaxis_title="",
                    margin=dict(l=0, r=60, t=10, b=10),
                    height=altura_real_grafico_br
                )
                
                with st.container(height=380):
                    st.plotly_chart(
                        fig_brs,
                        use_container_width=True
                    )

        st.markdown("---")
        
        # ----------------------------------------------------
        # SEÇÃO DE 2 COLUNAS ACIMA DO MAPA DE CALOR:
        # 1. Acidentes x Dias da Semana (barras verticais)
        # 2. Taxa de Acidentes por Extensão Total da Rodovia (com filtro e barra de rolagem)
        # ----------------------------------------------------
        col_b1, col_b2 = st.columns(2)

        with col_b1:
            st.markdown("##### Acidentes por Dia da Semana")
            if 'dia_nome' in df_filtrado.columns:
                df_dias = (
                    df_filtrado['dia_nome']
                    .value_counts()
                    .reindex(ORDEM_DIAS)
                    .reset_index()
                )
                df_dias.columns = ['Dia da Semana', 'Total']

                fig_dias = px.bar(
                    df_dias,
                    x='Dia da Semana',
                    y='Total',
                    text='Total',
                    color_discrete_sequence=[CORES_DASHBOARD['azul_escuro']],
                )
                fig_dias.update_traces(
                    textposition='outside',
                    cliponaxis=False,
                    textfont=dict(color=CORES_DASHBOARD['texto_escuro'])
                )
                fig_dias.update_layout(
                    xaxis_title="",
                    yaxis_title="Total de Acidentes",
                    height=520
                )
                st.plotly_chart(aplicar_tema_grafico(fig_dias), use_container_width=True)

        with col_b2:
            st.markdown("##### Taxa de Acidentes por Extensão da Rodovia (Acidentes / km)")

            col_rodovia_examp = 'nome_rodovia' if 'nome_rodovia' in df_rodovias.columns else ('br' if 'br' in df_rodovias.columns else None)

            if 'br' in df_filtrado.columns and col_rodovia_examp and 'extensao_total' in df_rodovias.columns:
                df_brs_calc = df_filtrado.dropna(subset=['br']).copy()
                df_brs_calc['rodovia'] = "BR-" + df_brs_calc['br'].astype(str).str.split('.').str[0].str.zfill(3)
                acidentes_br = df_brs_calc['rodovia'].value_counts().reset_index()
                acidentes_br.columns = ['rodovia', 'total_acidentes']

                df_rod_calc = df_rodovias.dropna(subset=[col_rodovia_examp, 'extensao_total']).copy()
                
                df_rod_calc['extensao_total'] = pd.to_numeric(
                    df_rod_calc['extensao_total'].astype(str).str.replace(',', '.'), 
                    errors='coerce'
                )
                
                def formatar_nome_br(val):
                    val_str = str(val).strip().upper()
                    if val_str.startswith('BR-'):
                        return val_str
                    if val_str.startswith('BR'):
                        return f"BR-{val_str[2:].zfill(3)}"
                    try:
                        num = int(float(val_str))
                        return f"BR-{num:03d}"
                    except (ValueError, TypeError):
                        return val_str

                df_rod_calc['rodovia'] = df_rod_calc[col_rodovia_examp].apply(formatar_nome_br)
                
                if filtro_ano and 'ano' in df_rod_calc.columns:
                    df_rod_calc = df_rod_calc[df_rod_calc['ano'].isin(filtro_ano)]
                
                extensao_br = df_rod_calc.groupby('rodovia')['extensao_total'].mean().reset_index()

                df_taxa = pd.merge(acidentes_br, extensao_br, on='rodovia', how='inner')
                df_taxa = df_taxa[df_taxa['extensao_total'] > 0].copy()
                df_taxa['taxa_acidentes_km'] = df_taxa['total_acidentes'] / df_taxa['extensao_total']

                taxa_brs_unicas = sorted(df_taxa['rodovia'].unique())

                taxa_brs_selecionadas = st.multiselect(
                    "Buscar rodovia(s) específica(s):",
                    options=taxa_brs_unicas,
                    default=[],
                    placeholder="Digite para filtrar rodovias...",
                    key="filtro_taxa_brs_multiselect"
                )

                if taxa_brs_selecionadas:
                    df_taxa = df_taxa[df_taxa['rodovia'].isin(taxa_brs_selecionadas)]

                altura_real_taxa = max(300, len(df_taxa) * 26)
                max_taxa = df_taxa['taxa_acidentes_km'].max() if not df_taxa.empty else 1.0

                if not df_taxa.empty:
                    fig_taxa = px.bar(
                        df_taxa,
                        x='taxa_acidentes_km',
                        y='rodovia',
                        orientation='h',
                        text='taxa_acidentes_km',
                        color_discrete_sequence=[CORES_DASHBOARD['amarelo_alerta']],
                        labels={
                            'rodovia': 'Rodovia',
                            'taxa_acidentes_km': 'Acidentes / km'
                        }
                    )
                    
                    fig_taxa = aplicar_tema_grafico(fig_taxa)
                    
                    fig_taxa.update_traces(
                        texttemplate='%{text:.2f}', 
                        textposition='outside', 
                        cliponaxis=False,
                        textfont=dict(color=CORES_DASHBOARD['texto_escuro'], size=10)
                    )
                    
                    fig_taxa.update_layout(
                        yaxis={
                            'categoryorder': 'total ascending',
                            'tickfont': dict(size=11),
                            'automargin': True
                        },
                        xaxis=dict(
                            range=[0, max_taxa * 1.15],
                            showgrid=True,
                            zeroline=False
                        ),
                        xaxis_title="",
                        yaxis_title="",
                        margin=dict(l=0, r=60, t=10, b=10),
                        height=altura_real_taxa
                    )
                    
                    with st.container(height=380):
                        st.plotly_chart(fig_taxa, use_container_width=True)
                else:
                    st.warning("Não foi possível calcular a taxa com os dados atuais.")
            else:
                st.info("Colunas necessárias não foram encontradas para o cálculo da taxa.")

        st.markdown("---")
        st.markdown("##### Mapa de Calor: Concentração de Acidentes (Dia da Semana × Hora)")

        if 'hora_num' in df_filtrado.columns and 'dia_nome' in df_filtrado.columns:
            df_heatmap = (
                df_filtrado[(df_filtrado['hora_num'] >= 0) & (df_filtrado['dia_nome'].notna())]
                .groupby(['dia_nome', 'hora_num'])
                .size()
                .unstack(fill_value=0)
                .reindex(index=ORDEM_DIAS, columns=range(24), fill_value=0)
            )

            fig_heatmap = px.imshow(
                df_heatmap,
                labels=dict(x="Hora do Dia", y="Dia da Semana", color="Acidentes"),
                x=[f"{h:02d}h" for h in range(24)],
                y=ORDEM_DIAS,
                color_continuous_scale=[
                    [0.0, "#16A34A"],
                    [0.5, "#F59E0B"],
                    [1.0, "#DC2626"]
                ],
                aspect="auto"
            )

            fig_heatmap.update_traces(
                xgap=2,
                ygap=2
            )

            fig_heatmap.update_layout(
                xaxis_title="Hora do Dia",
                yaxis_title="",
                height=380
            )

            st.plotly_chart(aplicar_tema_grafico(fig_heatmap), use_container_width=True)
