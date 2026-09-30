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

# Importando as novas funções consolidadas
from src.data_loader import carregar_dados_acidentes, carregar_dados_veiculos, carregar_geojson

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
    'fundo_app': '#F1F5F9',
    'fundo_sidebar': '#0F172A',
    'card_fundo': '#FFFFFF',
    'azul_escuro': '#0A192F',
    'azul_medio': '#1E3A8A',
    'laranja_destaque': '#D97706',
    'amarelo_alerta': '#F59E0B',
    'texto_escuro': '#0F172A',
    'cinza_texto': '#64748B',
    'cinza_borda': '#CBD5E1',
    'branco': '#FFFFFF',
    'vermelho': '#DC2626',
    'laranja':'#FFA500'
}

MESES_MAP = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}

ORDEM_DIAS = [
    "Domingo", "Segunda-Feira", "Terça-Feira", "Quarta-Feira", 
    "Quinta-Feira", "Sexta-Feira", "Sábado",
]

# Estilização CSS personalizada
st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {CORES_DASHBOARD['fundo_app']} !important; color: {CORES_DASHBOARD['texto_escuro']} !important; }}
    [data-testid="stSidebar"] {{ background-color: {CORES_DASHBOARD['fundo_sidebar']} !important; }}
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {{ color: {CORES_DASHBOARD['branco']} !important; }}
    h1, h2, h3 {{ color: {CORES_DASHBOARD['azul_escuro']} !important; font-weight: 800 !important; letter-spacing: -0.5px; }}
    .stMarkdown p, label, .stCaption {{ color: {CORES_DASHBOARD['texto_escuro']} !important; }}
    div[data-testid="metric-container"], div[data-testid="stMetric"] {{ background-color: {CORES_DASHBOARD['card_fundo']} !important; border: 1px solid {CORES_DASHBOARD['cinza_borda']} !important; border-radius: 10px !important; padding: 16px !important; box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.06) !important; }}
    div[data-testid="metric-container"] [data-testid="stMetricLabel"], div[data-testid="metric-container"] [data-testid="stMetricLabel"] *, div[data-testid="stMetricLabel"] p, div[data-testid="stMetricLabel"] label {{ color: {CORES_DASHBOARD['cinza_texto']} !important; font-size: 0.88rem !important; font-weight: 700 !important; text-transform: uppercase !important; }}
    div[data-testid="metric-container"] [data-testid="stMetricValue"], div[data-testid="metric-container"] [data-testid="stMetricValue"] *, div[data-testid="stMetricValue"] div, div[data-testid="stMetricValue"] span {{ color: {CORES_DASHBOARD['azul_escuro']} !important; font-size: 2.2rem !important; font-weight: 800 !important; }}
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {{ gap: 8px; background-color: {CORES_DASHBOARD['card_fundo']}; padding: 8px 12px; border-radius: 10px; border: 1px solid {CORES_DASHBOARD['cinza_borda']}; box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.04); }}
    div[data-testid="stTabs"] button[data-baseweb="tab"] {{ font-size: 1rem !important; font-weight: 700 !important; color: {CORES_DASHBOARD['cinza_texto']} !important; border-radius: 6px !important; padding: 8px 18px !important; border: none !important; }}
    div[data-testid="stTabs"] button[aria-selected="true"] {{ background-color: {CORES_DASHBOARD['azul_escuro']} !important; color: {CORES_DASHBOARD['branco']} !important; }}
    hr {{ border-color: {CORES_DASHBOARD['cinza_borda']} !important; }}
    .st-emotion-cache-csawen{{ color:{CORES_DASHBOARD['texto_escuro']}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

def formatar_numero(valor: float) -> str:
    return f"{int(valor):,}".replace(",", ".")

def aplicar_tema_grafico(fig):
    fig.update_layout(
        template='plotly_white',
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(color=CORES_DASHBOARD['texto_escuro'], family="sans-serif", size=12),
        legend=dict(font=dict(color=CORES_DASHBOARD['texto_escuro'], size=12), title=dict(font=dict(color=CORES_DASHBOARD['texto_escuro']))),
        xaxis=dict(showgrid=True, gridcolor="#E2E8F0", zeroline=False, color=CORES_DASHBOARD['texto_escuro'], title=dict(font=dict(color=CORES_DASHBOARD['texto_escuro'])), tickfont=dict(color=CORES_DASHBOARD['texto_escuro'])),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0", zeroline=False, color=CORES_DASHBOARD['texto_escuro'], title=dict(font=dict(color=CORES_DASHBOARD['texto_escuro'])), tickfont=dict(color=CORES_DASHBOARD['texto_escuro'])),
        coloraxis_colorbar=dict(title=dict(font=dict(color=CORES_DASHBOARD['texto_escuro'])), tickfont=dict(color=CORES_DASHBOARD['texto_escuro']))
    )
    return fig

# ==========================================
# 2. Carga e Pré-processamento dos Dados
# ==========================================
df = carregar_dados_acidentes()
df_veiculos = carregar_dados_veiculos()

try:
    geojson_br = carregar_geojson()
except Exception as e:
    geojson_br = None
    st.warning(f"Não foi possível carregar o arquivo GeoJSON para o mapa: {e}")

if 'data_inversa' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['data_inversa']):
    df['data_inversa'] = pd.to_datetime(df['data_inversa'])

if 'mes_num' not in df.columns and 'data_inversa' in df.columns:
    df['mes_num'] = df['data_inversa'].dt.month

if 'dia_semana' in df.columns:
    df['dia_nome'] = df['dia_semana'].astype(str).str.title()
elif 'data_inversa' in df.columns:
    dias_map = {0: "Segunda-Feira", 1: "Terça-Feira", 2: "Quarta-Feira", 3: "Quinta-Feira", 4: "Sexta-Feira", 5: "Sábado", 6: "Domingo"}
    df['dia_nome'] = df['data_inversa'].dt.dayofweek.map(dias_map)

# ==========================================
# 3. Sidebar - Filtros Interativos
# ==========================================
st.sidebar.image("https://whitecube.com.br/wp-content/uploads/2026/04/social-share.png", width=260)
st.sidebar.title("Filtros Analíticos")

anos_disponiveis = sorted(df['ano_base'].dropna().astype(int).unique()) if 'ano_base' in df.columns else []
ufs_disponiveis = sorted(df['uf'].dropna().unique()) if 'uf' in df.columns else []

filtro_ano = st.sidebar.multiselect("Ano Base", options=anos_disponiveis, default=[], placeholder="filtre por ano")
filtro_uf = st.sidebar.multiselect("Unidade da Federação (UF)", options=ufs_disponiveis, default=[], placeholder="Todas as UFs")

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
st.markdown(f"**Esses dados estão disponíveis na URL:** *https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf*")
st.markdown(f"**Anos:** {texto_anos} — **UFs:** {texto_ufs}")

# Ajuste de Estatísticas à prova de linhas duplicadas
if 'id' in df_filtrado.columns:
    total_acidentes = df_filtrado['id'].nunique()
else:
    total_acidentes = len(df_filtrado)

# Para vítimas, se a base for "Por Ocorrência", a soma está correta. 
# Se houver risco de duplicação, seria ideal agrupar por 'id' primeiro. 
# Assumindo o padrão PRF de ocorrência única por linha na base unificada:
total_obitos = df_filtrado.drop_duplicates(subset=['id'])['mortos'].sum() if 'id' in df_filtrado.columns and 'mortos' in df_filtrado.columns else (df_filtrado['mortos'].sum() if 'mortos' in df_filtrado.columns else 0)
total_feridos_graves = df_filtrado.drop_duplicates(subset=['id'])['feridos_graves'].sum() if 'id' in df_filtrado.columns and 'feridos_graves' in df_filtrado.columns else (df_filtrado['feridos_graves'].sum() if 'feridos_graves' in df_filtrado.columns else 0)

if total_acidentes > 0 and 'classificacao_acidente' in df_filtrado.columns:
    if 'id' in df_filtrado.columns:
        acidentes_fatais = df_filtrado[df_filtrado['classificacao_acidente'] == 'Com Vítimas Fatais']['id'].nunique()
    else:
        acidentes_fatais = (df_filtrado['classificacao_acidente'] == 'Com Vítimas Fatais').sum()
    tx_fatalidade = (acidentes_fatais / total_acidentes) * 100
else:
    tx_fatalidade = 0.0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Acidentes de Trânsito", formatar_numero(total_acidentes))
kpi2.metric("Quantidade de Feridos Graves", formatar_numero(total_feridos_graves))
kpi3.metric("Quantidade de Fatalidades", formatar_numero(total_obitos))
kpi4.metric("Taxa de Fatalidades", f"{tx_fatalidade:.1f}%")

st.markdown("---")

# ==========================================
# 5. Navbar de Navegação Superior (Tabs)
# ==========================================
tab_geral, tab_vitimas, tab_veiculos, tab_acidentes = st.tabs([
    "📊 Geral", "👥 Perfil Vítimas", "🚗 Perfil Veículos", "🚨 Perfil Acidentes"
])

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
else:
    with tab_geral:
        st.subheader("Visão Geral e Evolução Temporal")
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("##### Evolução Mensal de Acidentes")
            # Ajuste para contar IDs únicos
            if 'id' in df_filtrado.columns:
                evolucao = df_filtrado.groupby(['mes_num', 'ano_base'])['id'].nunique().reset_index(name='total')
            else:
                evolucao = df_filtrado.groupby(['mes_num', 'ano_base']).size().reset_index(name='total')
                
            evolucao['mes_nome'] = evolucao['mes_num'].map(MESES_MAP)
            evolucao['ano_base'] = evolucao['ano_base'].astype(str)

            fig_line = px.line(
                evolucao, x='mes_nome', y='total', color='ano_base',
                category_orders={'mes_nome': list(MESES_MAP.values())},
                color_discrete_sequence=[CORES_DASHBOARD['vermelho'], CORES_DASHBOARD['laranja'], CORES_DASHBOARD['azul_medio']],
            )
            fig_line.update_layout(xaxis_title="Mês", yaxis_title="Volume de Acidentes")
            st.plotly_chart(aplicar_tema_grafico(fig_line), use_container_width=True)

        with col_g2:
            st.markdown("##### Mapa Coroplético: Óbitos por UF")
            # Usa deduplicação para garantir óbitos reais (sem sobreposição)
            df_unique = df_filtrado.drop_duplicates(subset=['id']) if 'id' in df_filtrado.columns else df_filtrado
            uf_fatais = df_unique.groupby('uf')['mortos'].sum().reset_index()

            if geojson_br:
                fig_uf_mapa = px.choropleth(
                    uf_fatais, geojson=geojson_br, locations='uf', featureidkey='properties.sigla', color='mortos',
                    color_continuous_scale=["#E2E8F0", CORES_DASHBOARD['azul_medio'], CORES_DASHBOARD['vermelho']],
                    labels={'mortos': 'Óbitos', 'uf': 'UF'}
                )
                fig_uf_mapa.update_geos(fitbounds="locations", visible=False)
                st.plotly_chart(aplicar_tema_grafico(fig_uf_mapa), use_container_width=True)
            else:
                fig_uf = px.bar(
                    uf_fatais.sort_values('mortos', ascending=False), x='uf', y='mortos', color='mortos',
                    color_continuous_scale=["#E2E8F0", CORES_DASHBOARD['vermelho']]
                )
                fig_uf.update_layout(xaxis_title="Estado (UF)", yaxis_title="Total de Óbitos", coloraxis_showscale=False)
                st.plotly_chart(aplicar_tema_grafico(fig_uf), use_container_width=True)

        st.markdown("---")
        st.subheader("📍 Mapeamento Geográfico de Ocorrências (Latitude / Longitude)")

        df_coords = df_filtrado.drop_duplicates(subset=['id']).dropna(subset=['latitude', 'longitude']) if 'id' in df_filtrado.columns else df_filtrado.dropna(subset=['latitude', 'longitude'])

        if not df_coords.empty:
            if len(df_coords) > 10000:
                st.caption("Exibindo amostragem de 10.000 pontos para garantir alta performance.")
                df_coords = df_coords.sample(10000, random_state=42)

            fig_scatter_map = px.scatter_map(
                df_coords, lat='latitude', lon='longitude',
                color='classificacao_acidente' if 'classificacao_acidente' in df_coords.columns else None,
                hover_name='municipio' if 'municipio' in df_coords.columns else 'uf',
                hover_data=['br', 'km', 'mortos'] if 'br' in df_coords.columns else ['mortos'],
                zoom=3.5, center={"lat": -14.2350, "lon": -51.9253}, map_style="carto-positron",
                color_discrete_sequence=[CORES_DASHBOARD['azul_escuro'], CORES_DASHBOARD['vermelho'], CORES_DASHBOARD['laranja_destaque']],
            )
            fig_scatter_map.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(aplicar_tema_grafico(fig_scatter_map), use_container_width=True)
        else:
            st.warning("Não há coordenadas geográficas válidas para os filtros selecionados.")

    with tab_vitimas:
        st.subheader("Análise do Perfil das Vítimas e Gravidade")
        col_v1, col_v2 = st.columns(2)
        
        df_unique_acidentes = df_filtrado.drop_duplicates(subset=['id']) if 'id' in df_filtrado.columns else df_filtrado

        with col_v1:
            st.markdown("##### Classificação de Gravidade das Ocorrências")
            if 'classificacao_acidente' in df_unique_acidentes.columns:
                gravidade = df_unique_acidentes['classificacao_acidente'].value_counts().reset_index()
                gravidade.columns = ['Classificação', 'Total']

                fig_donut = px.pie(
                    gravidade, values='Total', names='Classificação', hole=0.55,
                    color_discrete_sequence=[CORES_DASHBOARD['azul_escuro'], CORES_DASHBOARD['laranja_destaque'], CORES_DASHBOARD['amarelo_alerta'], CORES_DASHBOARD['vermelho']]
                )
                fig_donut.update_traces(textposition='inside', textinfo='percent+label', insidetextfont=dict(color='#FFFFFF'), outsidetextfont=dict(color=CORES_DASHBOARD['texto_escuro']))
                st.plotly_chart(aplicar_tema_grafico(fig_donut), use_container_width=True)

        with col_v2:
            st.markdown("##### Total de Feridos Graves vs Óbitos por UF")
            if 'uf' in df_unique_acidentes.columns and 'mortos' in df_unique_acidentes.columns:
                df_vitimas_uf = df_unique_acidentes.groupby('uf')[['mortos', 'feridos_graves']].sum().reset_index().sort_values('mortos', ascending=False).head(10)
                fig_vit_bar = px.bar(
                    df_vitimas_uf, x='uf', y=['mortos', 'feridos_graves'], barmode='group',
                    labels={'value': 'Quantidade', 'variable': 'Métrica', 'uf': 'UF'},
                    color_discrete_map={'mortos': CORES_DASHBOARD['vermelho'], 'feridos_graves': CORES_DASHBOARD['laranja_destaque']}
                )
                st.plotly_chart(aplicar_tema_grafico(fig_vit_bar), use_container_width=True)

    with tab_veiculos:
        st.subheader("Análise dos Tipos de Veículos Envolvidos")
        col_veic1, col_veic2 = st.columns(2)

        with col_veic1:
            st.markdown("##### Distribuição de Acidentes por Tipo de Veículo")
            if 'tipo_veiculo' in df_filtrado.columns:
                top_veiculos = df_filtrado['tipo_veiculo'].dropna().astype(str).str.title().value_counts().head(7).reset_index()
                top_veiculos.columns = ['Tipo de Veículo', 'Total']

                fig_veiculo = px.pie(
                    top_veiculos, values='Total', names='Tipo de Veículo', hole=0.55,
                    color_discrete_sequence=[CORES_DASHBOARD['azul_escuro'], CORES_DASHBOARD['laranja_destaque'], CORES_DASHBOARD['azul_medio'], CORES_DASHBOARD['amarelo_alerta'], '#64748B']
                )
                fig_veiculo.update_traces(textposition='inside', textinfo='percent+label', insidetextfont=dict(color='#FFFFFF'), outsidetextfont=dict(color=CORES_DASHBOARD['texto_escuro']))
                st.plotly_chart(aplicar_tema_grafico(fig_veiculo), use_container_width=True)

        with col_veic2:
            st.markdown("##### Volume Total por Categoria de Veículo")
            if 'tipo_veiculo' in df_filtrado.columns:
                top_veic_bar = df_filtrado['tipo_veiculo'].dropna().astype(str).str.title().value_counts().head(10).reset_index()
                top_veic_bar.columns = ['Veículo', 'Total']

                fig_veic_bar = px.bar(top_veic_bar, x='Total', y='Veículo', orientation='h', text='Total', color_discrete_sequence=[CORES_DASHBOARD['azul_escuro']])
                fig_veic_bar.update_traces(textposition='outside', textfont=dict(color=CORES_DASHBOARD['texto_escuro']))
                fig_veic_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(aplicar_tema_grafico(fig_veic_bar), use_container_width=True)

    with tab_acidentes:
        st.subheader("Análise Operacional das Ocorrências")
        col_a1, col_a2 = st.columns(2)
        
        df_unique_operacional = df_filtrado.drop_duplicates(subset=['id']) if 'id' in df_filtrado.columns else df_filtrado

        with col_a1:
            st.markdown("##### Principais Causas de Acidentes")
            if 'causa_acidente' in df_unique_operacional.columns:
                causas_unicas = sorted(df_unique_operacional['causa_acidente'].dropna().unique())
                causas_selecionadas = st.multiselect("Buscar causa(s) específica(s):", options=causas_unicas, default=[], placeholder="Digite para filtrar causas...", key="filtro_causas_multiselect")

                df_causas = df_unique_operacional.copy()
                if causas_selecionadas:
                    df_causas = df_causas[df_causas['causa_acidente'].isin(causas_selecionadas)]

                causas = df_causas['causa_acidente'].value_counts().reset_index()
                causas.columns = ['Causa', 'Total']
                altura_real_grafico = max(350, len(causas) * 32)

                fig_bar = px.bar(causas, x='Total', y='Causa', orientation='h', text='Total', color_discrete_sequence=[CORES_DASHBOARD['laranja_destaque']])
                fig_bar.update_traces(textposition='outside', textfont=dict(color=CORES_DASHBOARD['texto_escuro'], size=12))
                fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'}, xaxis_title="", yaxis_title="", height=altura_real_grafico)

                with st.container(height=400):
                    st.plotly_chart(aplicar_tema_grafico(fig_bar), use_container_width=True)

        with col_a2:
            st.markdown("##### Top Rodovias (BRs) com Mais Acidentes")
            if 'br' in df_unique_operacional.columns:
                df_brs = df_unique_operacional.dropna(subset=['br']).copy()
                df_brs['br'] = "BR-" + df_brs['br'].astype(str).str.split('.').str[0].str.zfill(3)
                top_brs = df_brs['br'].value_counts().head(10).reset_index()
                top_brs.columns = ['Rodovia', 'Total']

                fig_brs = px.bar(top_brs, x='Total', y='Rodovia', orientation='h', text='Total', color_discrete_sequence=[CORES_DASHBOARD['azul_escuro']])
                fig_brs.update_traces(textposition='outside', textfont=dict(color=CORES_DASHBOARD['texto_escuro']))
                fig_brs.update_layout(yaxis={'categoryorder': 'total ascending'}, xaxis_title="", yaxis_title="")
                st.plotly_chart(aplicar_tema_grafico(fig_brs), use_container_width=True)

        st.markdown("---")
        col_a3, col_a4 = st.columns(2)

        with col_a3:
            st.markdown("##### Acidentes por Hora do Dia")
            if 'hora' in df_unique_operacional.columns:
                acidentes_hora = df_unique_operacional.groupby('hora').size().reindex(range(24), fill_value=0).reset_index(name='total')
                acidentes_hora['hora_label'] = acidentes_hora['hora'].apply(lambda x: f"{int(x):02d}h")

                fig_hora = px.bar(acidentes_hora, x='hora_label', y='total', labels={'hora_label': 'Hora do Dia', 'total': 'Total de Acidentes'}, color_discrete_sequence=[CORES_DASHBOARD['azul_escuro']])
                fig_hora.update_layout(xaxis_title="Hora (00h - 23h)", yaxis_title="Total de Acidentes")
                st.plotly_chart(aplicar_tema_grafico(fig_hora), use_container_width=True)

        with col_a4:
            st.markdown("##### Acidentes por Dia da Semana")
            if 'dia_nome' in df_unique_operacional.columns:
                acidentes_dia = df_unique_operacional.groupby('dia_nome').size().reindex(ORDEM_DIAS, fill_value=0).reset_index(name='total')
                fig_dias = px.bar(acidentes_dia, x='dia_nome', y='total', labels={'dia_nome': 'Dia da Semana', 'total': 'Total de Acidentes'}, color_discrete_sequence=[CORES_DASHBOARD['azul_escuro']])
                fig_dias.update_layout(xaxis_title="", yaxis_title="Total de Acidentes")
                st.plotly_chart(aplicar_tema_grafico(fig_dias), use_container_width=True)
