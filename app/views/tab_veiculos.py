import plotly.express as px
import streamlit as st


def render_tab_veiculos(df_filtrado, CORES_DASHBOARD, aplicar_tema_grafico):
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
                outsidetextfont=dict(color=CORES_DASHBOARD['texto_escuro']),
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
                color_discrete_sequence=[CORES_DASHBOARD['azul_escuro']],
            )
            fig_veic_bar.update_traces(
                textposition='outside',
                textfont=dict(color=CORES_DASHBOARD['texto_escuro']),
            )
            fig_veic_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(aplicar_tema_grafico(fig_veic_bar), use_container_width=True)
