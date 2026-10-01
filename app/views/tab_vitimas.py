import pandas as pd
import plotly.express as px
import streamlit as st


def render_tab_vitimas(df_filtrado, CORES_DASHBOARD, aplicar_tema_grafico):
    st.subheader("Análise do Perfil das Vítimas e Gravidade")

    df_temp = df_filtrado.copy()

    # -------------------------------------------------------------
    # 0. Cálculo Seguro de Total de Feridos e Óbitos
    # -------------------------------------------------------------
    if 'total_feridos' not in df_temp.columns:
        if 'feridos_leves' in df_temp.columns and 'feridos_graves' in df_temp.columns:
            df_temp['total_feridos'] = (
                pd.to_numeric(df_temp['feridos_leves'], errors='coerce').fillna(0) +
                pd.to_numeric(df_temp['feridos_graves'], errors='coerce').fillna(0)
            )
        elif 'feridos' in df_temp.columns:
            df_temp['total_feridos'] = pd.to_numeric(df_temp['feridos'], errors='coerce').fillna(0)
        elif 'feridos_graves' in df_temp.columns:
            df_temp['total_feridos'] = pd.to_numeric(df_temp['feridos_graves'], errors='coerce').fillna(0)
        else:
            df_temp['total_feridos'] = 0

    if 'mortos' in df_temp.columns:
        df_temp['mortos'] = pd.to_numeric(df_temp['mortos'], errors='coerce').fillna(0)
    else:
        df_temp['mortos'] = 0

    # -------------------------------------------------------------
    # 1. Primeira Linha: Estado Físico e UF (Todos os Estados + DF)
    # -------------------------------------------------------------
    col_v1, col_v2 = st.columns(2)

    with col_v1:
        st.markdown("##### Distribuição do Estado Físico das Vítimas")

        mapa_colunas = {
            'ilesos': 'Ileso',
            'feridos_leves': 'Ferimento Leve',
            'feridos_graves': 'Ferimento Grave',
            'mortos': 'Óbito',
        }

        # 1.1. Verifica se as colunas agregadas existem
        cols_presentes = [c for c in mapa_colunas.keys() if c in df_temp.columns]

        if cols_presentes:
            totais = {
                mapa_colunas[col]: pd.to_numeric(df_temp[col], errors='coerce').fillna(0).sum()
                for col in cols_presentes
            }
            df_gravidade = pd.DataFrame(list(totais.items()), columns=['Estado Físico', 'Total'])
            df_gravidade = df_gravidade[df_gravidade['Total'] > 0]

        # 1.2. Caso o DataFrame esteja no formato individual por vítima
        elif 'vitima_estado' in df_temp.columns or 'estado_fisico' in df_temp.columns:
            col_estado = 'vitima_estado' if 'vitima_estado' in df_temp.columns else 'estado_fisico'
            df_gravidade = df_temp[col_estado].value_counts().reset_index()
            df_gravidade.columns = ['Estado Físico', 'Total']

            de_para = {
                'ileso': 'Ileso',
                'feridos_leves': 'Ferimento Leve',
                'ferimento leve': 'Ferimento Leve',
                'feridos_graves': 'Ferimento Grave',
                'ferimento grave': 'Ferimento Grave',
                'mortos': 'Óbito',
                'óbito': 'Óbito',
                'obito': 'Óbito',
            }
            df_gravidade['Estado Físico'] = (
                df_gravidade['Estado Físico']
                .astype(str)
                .str.lower()
                .map(lambda x: de_para.get(x, 'Não Informado' if x in ['ignorado', 'invalido', 'inválido', 'nan', 'none'] else x.title()))
            )
            df_gravidade = df_gravidade.groupby('Estado Físico')['Total'].sum().reset_index()

        # 1.3. Fallback para classificação do acidente
        elif 'classificacao_acidente' in df_temp.columns:
            df_gravidade = df_temp['classificacao_acidente'].value_counts().reset_index()
            df_gravidade.columns = ['Estado Físico', 'Total']
        else:
            df_gravidade = pd.DataFrame(columns=['Estado Físico', 'Total'])

        if not df_gravidade.empty:
            mapa_cores = {
                'Ileso': CORES_DASHBOARD['azul_medio'],
                'Ferimento Leve': '#337733',
                'Ferimento Grave': CORES_DASHBOARD['laranja_destaque'],
                'Óbito': CORES_DASHBOARD['vermelho'],
                'Não Informado': CORES_DASHBOARD['cinza_texto'],
            }

            fig_donut = px.pie(
                df_gravidade,
                values='Total',
                names='Estado Físico',
                color='Estado Físico',
                color_discrete_map=mapa_cores,
                hole=0.55,
            )
            fig_donut.update_traces(
                textposition='inside',
                textinfo='percent+label',
                insidetextfont=dict(color='#FFFFFF'),
                outsidetextfont=dict(color=CORES_DASHBOARD['texto_escuro']),
            )
            st.plotly_chart(aplicar_tema_grafico(fig_donut), use_container_width=True)

    with col_v2:
        st.markdown("##### Total de Feridos vs Óbitos por UF (Todos os Estados e DF)")
        if 'uf' in df_temp.columns:
            # Agrupa por todas as UFs sem limitar com .head()
            df_vitimas_uf = (
                df_temp.groupby('uf')[['total_feridos', 'mortos']]
                .sum()
                .reset_index()
                .sort_values('total_feridos', ascending=False)
            )

            fig_vit_bar = px.bar(
                df_vitimas_uf,
                x='uf',
                y=['total_feridos', 'mortos'],
                barmode='group',
                labels={'value': 'Quantidade', 'variable': 'Métrica', 'uf': 'UF'},
                color_discrete_map={
                    'total_feridos': CORES_DASHBOARD['laranja_destaque'],
                    'mortos': CORES_DASHBOARD['vermelho'],
                },
            )
            
            fig_vit_bar.for_each_trace(
                lambda t: t.update(
                    name={'total_feridos': 'Total Feridos', 'mortos': 'Óbitos'}.get(t.name, t.name)
                )
            )
            st.plotly_chart(aplicar_tema_grafico(fig_vit_bar), use_container_width=True)

    st.markdown("---")

    # -------------------------------------------------------------
    # 2. Segunda Linha: Feridos por Sexo e Feridos por Idade
    # -------------------------------------------------------------
    col_v3, col_v4 = st.columns(2)

    with col_v3:
        st.markdown("##### Total de Feridos por Sexo")
        col_sexo = next((c for c in ['sexo', 'tipo_sexo', 'sexo_vitima'] if c in df_temp.columns), None)

        if col_sexo:
            df_sexo = df_temp.copy()

            # Normalização de Sexo e substituição de Ignorado/Nulo por "Não Informado"
            mapa_sexo = {
                'm': 'Masculino', 'masculino': 'Masculino',
                'f': 'Feminino', 'feminino': 'Feminino',
                'ignorado': 'Não Informado', 'invalido': 'Não Informado', 'inválido': 'Não Informado',
                'não informado': 'Não Informado', 'nao informado': 'Não Informado',
                'nan': 'Não Informado', 'none': 'Não Informado', '': 'Não Informado'
            }

            s_limpo = (
                df_sexo[col_sexo]
                .fillna('Não Informado')
                .astype(str)
                .str.strip()
                .str.lower()
            )
            df_sexo['Sexo'] = s_limpo.map(lambda x: mapa_sexo.get(x, 'Não Informado'))

            # Se for nível de vítima individual:
            if 'vitima_estado' in df_sexo.columns and df_sexo['vitima_estado'].str.contains('Ferido', case=False, na=False).any():
                df_feridos_s = df_sexo[df_sexo['vitima_estado'].astype(str).str.contains('Ferido|Lesões', case=False, na=False)]
                df_sexo_chart = df_feridos_s['Sexo'].value_counts().reset_index()
                df_sexo_chart.columns = ['Sexo', 'Total Feridos']
            else:
                df_sexo_chart = df_sexo.groupby('Sexo')['total_feridos'].sum().reset_index()
                df_sexo_chart.columns = ['Sexo', 'Total Feridos']

            fig_sexo = px.bar(
                df_sexo_chart,
                x='Sexo',
                y='Total Feridos',
                text_auto=True,
                color='Sexo',
                color_discrete_map={
                    'Masculino': CORES_DASHBOARD['azul_medio'],
                    'Feminino': '#C71585',
                    'Não Informado': CORES_DASHBOARD['cinza_borda'],
                }
            )
            fig_sexo.update_traces(textposition='outside')
            st.plotly_chart(aplicar_tema_grafico(fig_sexo), use_container_width=True)
        else:
            st.info("Coluna de sexo não encontrada no conjunto de dados.")

    with col_v4:
        st.markdown("##### Total de Feridos por Faixa Etária")
        col_idade = next((c for c in ['idade', 'idade_vitima'] if c in df_temp.columns), None)

        if col_idade:
            df_idade = df_temp.copy()
            df_idade['idade_num'] = pd.to_numeric(df_idade[col_idade], errors='coerce')

            # Definição das faixas etárias
            bins = [-1, 12, 17, 24, 34, 44, 54, 64, 120]
            labels = ['0-12 anos', '13-17 anos', '18-24 anos', '25-34 anos', '35-44 anos', '45-54 anos', '55-64 anos', '65+ anos']

            df_idade['Faixa Etária'] = pd.cut(df_idade['idade_num'], bins=bins, labels=labels)
            
            # Tratamento para valores ausentes/ignorados na idade
            df_idade['Faixa Etária'] = (
                df_idade['Faixa Etária']
                .astype(str)
                .replace({'nan': 'Não Informado', 'NaN': 'Não Informado', 'None': 'Não Informado', '<NA>': 'Não Informado'})
            )

            # Se for nível de vítima individual:
            if 'vitima_estado' in df_idade.columns and df_idade['vitima_estado'].str.contains('Ferido', case=False, na=False).any():
                df_feridos_i = df_idade[df_idade['vitima_estado'].astype(str).str.contains('Ferido|Lesões', case=False, na=False)]
                df_idade_chart = df_feridos_i['Faixa Etária'].value_counts().reset_index()
                df_idade_chart.columns = ['Faixa Etária', 'Total Feridos']
            else:
                df_idade_chart = df_idade.groupby('Faixa Etária')['total_feridos'].sum().reset_index()
                df_idade_chart.columns = ['Faixa Etária', 'Total Feridos']

            # Ordenação personalizada mantendo "Não Informado" no final
            ordem_faixas = labels + ['Não Informado']
            df_idade_chart['Faixa Etária'] = pd.Categorical(df_idade_chart['Faixa Etária'], categories=ordem_faixas, ordered=True)
            df_idade_chart = df_idade_chart.sort_values('Faixa Etária')

            fig_idade = px.bar(
                df_idade_chart,
                x='Faixa Etária',
                y='Total Feridos',
                text_auto=True,
                color_discrete_sequence=[CORES_DASHBOARD['azul_medio']]
            )
            fig_idade.update_traces(textposition='outside')
            st.plotly_chart(aplicar_tema_grafico(fig_idade), use_container_width=True)
        else:
            st.info("Coluna de idade não encontrada no conjunto de dados.")
