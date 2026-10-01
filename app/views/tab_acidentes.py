import pandas as pd
import plotly.express as px
import streamlit as st


def render_tab_acidentes(
    df_filtrado, df_rodovias, CORES_DASHBOARD, ORDEM_DIAS, filtro_ano, aplicar_tema_grafico
):
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
                key="filtro_causas_multiselect",
            )

            df_causas = df_filtrado.copy()
            if causas_selecionadas:
                df_causas = df_causas[df_causas['causa_acidente'].isin(causas_selecionadas)]

            causas = df_causas['causa_acidente'].value_counts().reset_index()
            causas.columns = ['Causa', 'Total']

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
                textfont=dict(color=CORES_DASHBOARD['texto_escuro'], size=10),
            )
            fig_bar.update_layout(
                yaxis={'categoryorder': 'total ascending', 'tickfont': dict(size=11), 'automargin': True},
                xaxis=dict(range=[0, max_total * 1.10], showgrid=True, zeroline=False),
                xaxis_title="",
                yaxis_title="",
                margin=dict(l=0, r=60, t=10, b=10),
                height=altura_real_grafico,
            )
            with st.container(height=380):
                st.plotly_chart(fig_bar, use_container_width=True)

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
                key="filtro_brs_multiselect",
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
                textfont=dict(color=CORES_DASHBOARD['texto_escuro'], size=10),
            )
            fig_brs.update_layout(
                yaxis={'categoryorder': 'total ascending', 'tickfont': dict(size=11), 'automargin': True},
                xaxis=dict(range=[0, max_total_br * 1.15], showgrid=True, zeroline=False),
                xaxis_title="",
                yaxis_title="",
                margin=dict(l=0, r=60, t=10, b=10),
                height=altura_real_grafico_br,
            )
            with st.container(height=380):
                st.plotly_chart(fig_brs, use_container_width=True)

    st.markdown("---")

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
                textfont=dict(color=CORES_DASHBOARD['texto_escuro']),
            )
            fig_dias.update_layout(xaxis_title="", yaxis_title="Total de Acidentes", height=520)
            st.plotly_chart(aplicar_tema_grafico(fig_dias), use_container_width=True)

    with col_b2:
        st.markdown("##### Taxa de Acidentes por Extensão da Rodovia (Acidentes / km)")

        col_rodovia_examp = (
            'nome_rodovia' if 'nome_rodovia' in df_rodovias.columns else ('br' if 'br' in df_rodovias.columns else None)
        )

        if 'br' in df_filtrado.columns and col_rodovia_examp and 'extensao_total' in df_rodovias.columns:
            df_brs_calc = df_filtrado.dropna(subset=['br']).copy()
            df_brs_calc['rodovia'] = "BR-" + df_brs_calc['br'].astype(str).str.split('.').str[0].str.zfill(3)
            acidentes_br = df_brs_calc['rodovia'].value_counts().reset_index()
            acidentes_br.columns = ['rodovia', 'total_acidentes']

            df_rod_calc = df_rodovias.dropna(subset=[col_rodovia_examp, 'extensao_total']).copy()
            df_rod_calc['extensao_total'] = pd.to_numeric(
                df_rod_calc['extensao_total'].astype(str).str.replace(',', '.'), errors='coerce'
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
                key="filtro_taxa_brs_multiselect",
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
                    labels={'rodovia': 'Rodovia', 'taxa_acidentes_km': 'Acidentes / km'},
                )
                fig_taxa = aplicar_tema_grafico(fig_taxa)
                fig_taxa.update_traces(
                    texttemplate='%{text:.2f}',
                    textposition='outside',
                    cliponaxis=False,
                    textfont=dict(color=CORES_DASHBOARD['texto_escuro'], size=10),
                )
                fig_taxa.update_layout(
                    yaxis={'categoryorder': 'total ascending', 'tickfont': dict(size=11), 'automargin': True},
                    xaxis=dict(range=[0, max_taxa * 1.15], showgrid=True, zeroline=False),
                    xaxis_title="",
                    yaxis_title="",
                    margin=dict(l=0, r=60, t=10, b=10),
                    height=altura_real_taxa,
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
            color_continuous_scale=[[0.0, "#16A34A"], [0.5, "#F59E0B"], [1.0, "#DC2626"]],
            aspect="auto",
        )
        fig_heatmap.update_traces(xgap=2, ygap=2)
        fig_heatmap.update_layout(xaxis_title="Hora do Dia", yaxis_title="", height=380)
        st.plotly_chart(aplicar_tema_grafico(fig_heatmap), use_container_width=True)

    # ==========================================
    # Nova Seção: Tabela de Km Críticos por Rodovia
    # ==========================================
    st.markdown("---")
    st.markdown("##### Quilômetros (Km) Críticos com Maior Incidência de Acidentes por Rodovia")

    if 'br' in df_filtrado.columns and 'km' in df_filtrado.columns:
        df_km = df_filtrado.dropna(subset=['br', 'km']).copy()

        if not df_km.empty:
            df_km['rodovia_fmt'] = "BR-" + df_km['br'].astype(str).str.split('.').str[0].str.zfill(3)
            df_km['km_num'] = pd.to_numeric(df_km['km'].astype(str).str.replace(',', '.'), errors='coerce')
            df_km = df_km.dropna(subset=['km_num'])

            if not df_km.empty:
                df_km['km_int'] = df_km['km_num'].round(0).astype(int)

                col_f1, col_f2, col_f3 = st.columns([2, 1, 1])

                with col_f1:
                    brs_km_unicas = sorted(df_km['rodovia_fmt'].unique())
                    brs_km_selecionadas = st.multiselect(
                        "Filtrar Rodovia(s):",
                        options=brs_km_unicas,
                        default=[],
                        placeholder="Todas as rodovias...",
                        key="filtro_km_brs_multiselect"
                    )

                with col_f2:
                    top_n_km = st.selectbox(
                        "Exibir por Rodovia:",
                        options=["Top 1", "Top 3", "Top 5", "Top 10", "Todos"],
                        index=2,
                        key="filtro_km_top_n"
                    )

                with col_f3:
                    min_acidentes = st.number_input(
                        "Mínimo de Acidentes:",
                        min_value=1,
                        value=1,
                        step=1,
                        key="filtro_km_min_acidentes"
                    )

                # Agrupamento por Rodovia e Quilômetro
                agg_dict = {'km_num': 'count'}
                if 'mortos' in df_km.columns:
                    agg_dict['mortos'] = 'sum'
                if 'feridos_graves' in df_km.columns:
                    agg_dict['feridos_graves'] = 'sum'

                df_grouped = df_km.groupby(['rodovia_fmt', 'km_int']).agg(agg_dict).reset_index()

                rename_map = {
                    'rodovia_fmt': 'Rodovia',
                    'km_int': 'Quilômetro',
                    'km_num': 'Total de Acidentes',
                    'mortos': 'Fatalidades',
                    'feridos_graves': 'Feridos Graves'
                }
                df_grouped.rename(columns=rename_map, inplace=True)

                if brs_km_selecionadas:
                    df_grouped = df_grouped[df_grouped['Rodovia'].isin(brs_km_selecionadas)]

                if min_acidentes > 1:
                    df_grouped = df_grouped[df_grouped['Total de Acidentes'] >= min_acidentes]

                # Aplicar Top N por Rodovia
                if top_n_km != "Todos":
                    n_val = int(top_n_km.replace("Top ", ""))
                    df_grouped = (
                        df_grouped.sort_values(by=['Rodovia', 'Total de Acidentes'], ascending=[True, False])
                        .groupby('Rodovia')
                        .head(n_val)
                    )

                df_grouped = df_grouped.sort_values(by=['Total de Acidentes', 'Rodovia'], ascending=[False, True]).reset_index(drop=True)
                df_grouped['Trecho / Km'] = df_grouped['Quilômetro'].apply(lambda x: f"Km {x}")

                col_ordem = ['Rodovia', 'Trecho / Km', 'Total de Acidentes']
                if 'Fatalidades' in df_grouped.columns:
                    col_ordem.append('Fatalidades')
                if 'Feridos Graves' in df_grouped.columns:
                    col_ordem.append('Feridos Graves')

                df_exibir = df_grouped[col_ordem]

                st.dataframe(
                    df_exibir,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Rodovia": st.column_config.TextColumn("Rodovia"),
                        "Trecho / Km": st.column_config.TextColumn("Trecho / Km"),
                        "Total de Acidentes": st.column_config.NumberColumn("Total de Acidentes", format="%d"),
                        "Fatalidades": st.column_config.NumberColumn("Fatalidades", format="%d"),
                        "Feridos Graves": st.column_config.NumberColumn("Feridos Graves", format="%d"),
                    }
                )
            else:
                st.warning("Não há dados válidos de quilometragem para exibição.")
        else:
            st.warning("Não há dados de rodovias e quilômetros disponíveis.")
    else:
        st.info("Colunas de rodovia (br) e quilômetro (km) não foram encontradas no conjunto de dados.")
