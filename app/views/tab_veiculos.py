import plotly.express as px
import streamlit as st
import pandas as pd


def render_tab_veiculos(df_filtrado, CORES_DASHBOARD, aplicar_tema_grafico):
    st.subheader("Análise dos Tipos de Veículos Envolvidos")

    if 'tipo_veiculo' not in df_filtrado.columns or df_filtrado['tipo_veiculo'].dropna().empty:
        st.warning("Nenhum dado de veículo disponível para exibição.")
        return

    # Padronização segura da coluna de tipo de veículo
    df_temp = df_filtrado.copy()
    df_temp['tipo_veiculo_clean'] = (
        df_temp['tipo_veiculo']
        .fillna('Não Informado')
        .astype(str)
        .str.title()
    )

    # Exclusão de 'Não Informado' e 'Chassi-Plataforma' (e variações)
    termos_excluir = ['não informado', 'nao informado', 'chassi-plataforma', 'chassi - plataforma', 'chassi plataforma']
    df_temp = df_temp[
        ~df_temp['tipo_veiculo_clean'].str.lower().isin(termos_excluir)
    ].copy()

    if df_temp.empty:
        st.warning("Nenhum dado válido de veículo encontrado após a exclusão dos tipos não informados/chassi-plataforma.")
        return

    # Identificação automática da coluna de marca/fabricante
    col_marca = None
    for col in ['marca', 'marca_modelo', 'fabricante']:
        if col in df_temp.columns:
            col_marca = col
            break

    if col_marca:
        df_temp['marca_clean'] = (
            df_temp[col_marca]
            .fillna('Não Informado')
            .astype(str)
            .str.upper()
            .str.strip()
        )
        df_temp['marca_clean'] = df_temp['marca_clean'].replace(
            {'': 'Não Informado', 'NAN': 'Não Informado', 'NONE': 'Não Informado'}
        )
    else:
        df_temp['marca_clean'] = 'Não Informado'

    todos_veiculos = sorted(df_temp['tipo_veiculo_clean'].unique().tolist())

    col_veic1, col_veic2 = st.columns(2)

    # ==========================================
    # Gráfico 1: Distribuição de Acidentes (Paleta Heterogênea)
    # ==========================================
    with col_veic1:
        st.markdown("##### Distribuição de Acidentes por Tipo de Veículo")
        
        veiculos_g1 = st.multiselect(
            "Filtrar tipo(s) de veículo:",
            options=todos_veiculos,
            default=[],  
            key="filtro_veiculos_g1",
            placeholder="Todos os veículos (ou selecione para filtrar)..."
        )

        df_top = df_temp[df_temp['tipo_veiculo_clean'].isin(veiculos_g1)].copy() if veiculos_g1 else df_temp.copy()
        df_top['Tipo de Veículo'] = df_top['tipo_veiculo_clean']

        col_empilhamento = None
        if 'tipo_acidente' in df_top.columns and df_top['tipo_acidente'].dropna().nunique() > 1:
            col_empilhamento = 'tipo_acidente'
            nome_legenda = 'Tipo de Acidente'
        elif 'classificacao_acidente' in df_top.columns and df_top['classificacao_acidente'].dropna().nunique() > 1:
            col_empilhamento = 'classificacao_acidente'
            nome_legenda = 'Classificação do Acidente'

        if col_empilhamento:
            df_top[nome_legenda] = df_top[col_empilhamento].fillna('Outros').astype(str).str.title()
            top_subcats = df_top[nome_legenda].value_counts().head(5).index.tolist()
            df_top['Subcategoria'] = df_top[nome_legenda].apply(lambda x: x if x in top_subcats else 'Outros')

            df_grouped = (
                df_top.groupby(['Tipo de Veículo', 'Subcategoria'])
                .size()
                .reset_index(name='Total')
            )
            
            df_grouped['Soma_Veiculo'] = df_grouped.groupby('Tipo de Veículo')['Total'].transform('sum')
            df_grouped['Porcentagem'] = (df_grouped['Total'] / df_grouped['Soma_Veiculo']) * 100
            df_grouped['Texto_Pct'] = df_grouped['Porcentagem'].map('{:.1f}%'.format)

            fig_veiculo = px.bar(
                df_grouped,
                x='Porcentagem',
                y='Tipo de Veículo',
                color='Subcategoria',
                orientation='h',
                text='Texto_Pct',
                color_discrete_sequence=px.colors.qualitative.Vivid,  # Paleta heterogênea
            )
        else:
            df_counts = df_top['Tipo de Veículo'].value_counts().reset_index()
            df_counts.columns = ['Tipo de Veículo', 'Total']
            total_geral = df_counts['Total'].sum()
            df_counts['Porcentagem'] = (df_counts['Total'] / total_geral) * 100
            df_counts['Texto_Pct'] = df_counts['Porcentagem'].map('{:.1f}%'.format)
            df_counts['Categoria'] = 'Distribuição de Veículos'

            fig_veiculo = px.bar(
                df_counts,
                x='Porcentagem',
                y='Categoria',
                color='Tipo de Veículo',
                orientation='h',
                text='Texto_Pct',
                color_discrete_sequence=px.colors.qualitative.Vivid,  # Paleta heterogênea
            )

        num_veiculos_g1 = df_top['Tipo de Veículo'].nunique()
        altura_calculada_g1 = max(400, num_veiculos_g1 * 35)

        fig_veiculo.update_traces(
            textposition='inside',
            insidetextanchor='middle',
            textfont=dict(color='#FFFFFF', size=11),
        )
        
        fig_veiculo.update_layout(
            barmode='stack',
            height=altura_calculada_g1,
            xaxis=dict(
                title='%GT Sum of Index',
                range=[0, 100],
                ticksuffix='%',
                showgrid=True,
                gridcolor='#E2E8F0',
            ),
            yaxis=dict(
                title='Tipo de Veículo' if col_empilhamento else '',
                autorange='reversed',
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='left',
                x=0,
                title=None,
            ),
        )

        with st.container(height=500):
            st.plotly_chart(aplicar_tema_grafico(fig_veiculo), use_container_width=True)

    # ==========================================
    # Gráfico 2: Volume Total por Categoria
    # ==========================================
    with col_veic2:
        st.markdown("##### Volume Total por Categoria de Veículo")
        
        veiculos_g2 = st.multiselect(
            "Filtrar tipo(s) de veículo:",
            options=todos_veiculos,
            default=[],  
            key="filtro_veiculos_g2",
            placeholder="Todos os veículos (ou selecione para filtrar)..."
        )

        df_veic2 = df_temp[df_temp['tipo_veiculo_clean'].isin(veiculos_g2)].copy() if veiculos_g2 else df_temp.copy()

        top_veic_bar = (
            df_veic2['tipo_veiculo_clean']
            .value_counts()
            .reset_index()
        )
        top_veic_bar.columns = ['Veículo', 'Total']

        fig_veic_bar = px.bar(
            top_veic_bar,
            x='Total',
            y='Veículo',
            orientation='h',
            text='Total',
            color_discrete_sequence=[CORES_DASHBOARD.get('azul_escuro', '#0A192F')],
        )

        num_veiculos_g2 = len(top_veic_bar)
        altura_calculada_g2 = max(400, num_veiculos_g2 * 35)

        fig_veic_bar.update_traces(
            textposition='outside',
            textfont=dict(color=CORES_DASHBOARD.get('texto_escuro', '#0F172A')),
        )
        fig_veic_bar.update_layout(
            height=altura_calculada_g2,
            yaxis={'categoryorder': 'total ascending'}
        )

        with st.container(height=500):
            st.plotly_chart(aplicar_tema_grafico(fig_veic_bar), use_container_width=True)

    # ==========================================
    # Gráfico 3: Marca Mais Presente por Tipo de Veículo
    # ==========================================
    st.markdown("---")
    st.markdown("##### Marca Mais Presente em Acidentes por Tipo de Veículo")

    veiculos_g3 = st.multiselect(
        "Filtrar tipo(s) de veículo para marcas:",
        options=todos_veiculos,
        default=[],
        key="filtro_veiculos_g3",
        placeholder="Todos os veículos (ou selecione para filtrar)..."
    )

    df_g3 = df_temp[df_temp['tipo_veiculo_clean'].isin(veiculos_g3)].copy() if veiculos_g3 else df_temp.copy()

    df_marca_counts = (
        df_g3.groupby(['tipo_veiculo_clean', 'marca_clean'])
        .size()
        .reset_index(name='qtd_acidentes')
    )

    df_top_marca = (
        df_marca_counts.sort_values(['tipo_veiculo_clean', 'qtd_acidentes'], ascending=[True, False])
        .groupby('tipo_veiculo_clean')
        .first()
        .reset_index()
    )

    df_top_marca.rename(columns={
        'tipo_veiculo_clean': 'Tipo de Veículo',
        'marca_clean': 'Marca Mais Presente',
        'qtd_acidentes': 'Total de Acidentes'
    }, inplace=True)

    df_top_marca['Rotulo'] = df_top_marca.apply(
        lambda r: f"{r['Marca Mais Presente']} ({int(r['Total de Acidentes']):,}".replace(',', '.') + " acidentes)",
        axis=1
    )

    fig_marca = px.bar(
        df_top_marca,
        x='Total de Acidentes',
        y='Tipo de Veículo',
        orientation='h',
        text='Rotulo',
        color_discrete_sequence=[CORES_DASHBOARD.get('laranja_destaque', '#D97706')],
    )

    num_veiculos_g3 = len(df_top_marca)
    altura_calculada_g3 = max(400, num_veiculos_g3 * 38)

    fig_marca.update_traces(
        textposition='outside',
        textfont=dict(color=CORES_DASHBOARD.get('texto_escuro', '#0F172A')),
    )
    fig_marca.update_layout(
        height=altura_calculada_g3,
        yaxis={'categoryorder': 'total ascending'},
        xaxis_title="Acidentes da Marca Líder",
        yaxis_title="Tipo de Veículo"
    )

    with st.container(height=500):
        st.plotly_chart(aplicar_tema_grafico(fig_marca), use_container_width=True)
