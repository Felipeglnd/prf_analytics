import pandas as pd
import plotly.express as px
import streamlit as st


def render_tab_geral(
    df_filtrado, df_frota, geojson_br, CORES_DASHBOARD, MESES_MAP, filtro_ano, aplicar_tema_grafico
):
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
        st.markdown("##### Total de Acidentes por Estado (UF)")
        if 'uf' in df_filtrado.columns:
            if 'id' in df_filtrado.columns:
                uf_acidentes = (
                    df_filtrado.groupby('uf')['id']
                    .nunique()
                    .reset_index(name='total_acidentes')
                )
            else:
                uf_acidentes = (
                    df_filtrado['uf']
                    .value_counts()
                    .reset_index()
                )
                uf_acidentes.columns = ['uf', 'total_acidentes']

            uf_acidentes = uf_acidentes.sort_values('total_acidentes', ascending=False)

            fig_uf_bar = px.bar(
                uf_acidentes,
                x='uf',
                y='total_acidentes',
                text='total_acidentes',
                color_discrete_sequence=[CORES_DASHBOARD['azul_escuro']],
                labels={'uf': 'Estado (UF)', 'total_acidentes': 'Total de Acidentes'},
            )
            fig_uf_bar.update_traces(
                textposition='outside',
                cliponaxis=False,
                textfont=dict(color=CORES_DASHBOARD['texto_escuro'], size=10),
            )
            fig_uf_bar.update_layout(
                xaxis_title="Estado (UF)",
                yaxis_title="Total de Acidentes",
                xaxis={'categoryorder': 'total descending'},
            )
            st.plotly_chart(aplicar_tema_grafico(fig_uf_bar), use_container_width=True)

    st.markdown("---")

    col_g3, col_g4 = st.columns(2)

    with col_g3:
        st.markdown("##### Taxa de Acidentes vs Frota (por UF)")
        st.caption("Acidentes (ID único) a cada 10 mil veículos registrados no estado")

        if 'uf' in df_filtrado.columns and not df_frota.empty:
            if 'id' in df_filtrado.columns:
                acidentes_uf = df_filtrado.groupby('uf')['id'].nunique().reset_index()
                acidentes_uf.columns = ['uf', 'total_acidentes']
            else:
                acidentes_uf = df_filtrado['uf'].value_counts().reset_index()
                acidentes_uf.columns = ['uf', 'total_acidentes']

            df_frota_filtrada = df_frota.copy()
            if filtro_ano and 'ano' in df_frota_filtrada.columns:
                df_frota_filtrada = df_frota_filtrada[df_frota_filtrada['ano'].isin(filtro_ano)]

            if 'qtd_veiculos' in df_frota_filtrada.columns:
                df_frota_filtrada['qtd_veiculos'] = pd.to_numeric(
                    df_frota_filtrada['qtd_veiculos'], errors='coerce'
                ).fillna(0)
                frota_uf = df_frota_filtrada.groupby('uf')['qtd_veiculos'].sum().reset_index()

                df_taxa_frota = pd.merge(acidentes_uf, frota_uf, on='uf', how='inner')
                df_taxa_frota = df_taxa_frota[df_taxa_frota['qtd_veiculos'] > 0].copy()
                df_taxa_frota['taxa_10k'] = (
                    df_taxa_frota['total_acidentes'] / df_taxa_frota['qtd_veiculos']
                ) * 10000

                if not df_taxa_frota.empty:
                    df_taxa_frota = df_taxa_frota.sort_values('taxa_10k', ascending=True)
                    altura_grafico = max(300, len(df_taxa_frota) * 26)
                    max_taxa = df_taxa_frota['taxa_10k'].max()

                    fig_taxa_f = px.bar(
                        df_taxa_frota,
                        x='taxa_10k',
                        y='uf',
                        orientation='h',
                        text='taxa_10k',
                        labels={'taxa_10k': 'Acidentes por 10 mil veículos', 'uf': 'UF'},
                        color_discrete_sequence=[CORES_DASHBOARD['azul_escuro']],
                    )
                    fig_taxa_f = aplicar_tema_grafico(fig_taxa_f)
                    fig_taxa_f.update_traces(
                        texttemplate='%{text:.2f}',
                        textposition='outside',
                        cliponaxis=False,
                        textfont=dict(color=CORES_DASHBOARD['texto_escuro'], size=10),
                    )
                    fig_taxa_f.update_layout(
                        yaxis={'categoryorder': 'total ascending', 'tickfont': dict(size=11), 'automargin': True},
                        xaxis=dict(range=[0, max_taxa * 1.15], showgrid=True, zeroline=False),
                        xaxis_title="",
                        yaxis_title="",
                        margin=dict(l=0, r=40, t=10, b=10),
                        height=altura_grafico,
                    )
                    with st.container(height=380):
                        st.plotly_chart(fig_taxa_f, use_container_width=True)

    with col_g4:
        st.markdown("##### Acidentes por Condição Meteorológica")
        if 'condicao_metereologica' in df_filtrado.columns:
            condicoes_unicas = sorted(df_filtrado['condicao_metereologica'].dropna().unique())
            condicoes_selecionadas = st.multiselect(
                "Filtrar Condição(ões) Meteorológica(s):",
                options=condicoes_unicas,
                default=[],
                placeholder="Selecione para filtrar...",
                key="filtro_clima_multiselect",
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
                color_discrete_sequence=[CORES_DASHBOARD['azul_medio']],
            )
            fig_clima = aplicar_tema_grafico(fig_clima)
            fig_clima.update_traces(
                textposition='outside',
                cliponaxis=False,
                textfont=dict(color=CORES_DASHBOARD['texto_escuro'], size=10),
            )
            fig_clima.update_layout(
                yaxis={'categoryorder': 'total ascending', 'tickfont': dict(size=11), 'automargin': True},
                xaxis=dict(range=[0, max_clima * 1.15], showgrid=True, zeroline=False),
                xaxis_title="",
                yaxis_title="",
                margin=dict(l=0, r=40, t=10, b=10),
                height=altura_real_clima,
            )
            with st.container(height=380):
                st.plotly_chart(fig_clima, use_container_width=True)

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
