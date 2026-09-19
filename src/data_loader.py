import os
from typing import List, Optional
import gdown
import pandas as pd

# ==============================================================================
# LISTA PADRÃO DE IDS DO GOOGLE DRIVE
# ==============================================================================
DEFAULT_DRIVE_IDS = [
    '1TdIUpSkghOxLmVwWwbYH1GI9ICMUxWv0',  # 2023 (~206 MB)
    '13PSlOxY1JUhN9eJIcDzEUg4Wq5FC0XRJ',  # 2024 (~222 MB)
    '1BUikMurrueItOiAJCEd8YAyNdlrNahMG',  # 2025 (~213 MB)
]


def load_data(file_ids: Optional[List[str]] = None) -> pd.DataFrame:
    """Baixa (se necessário) e unifica os arquivos CSV do Google Drive."""
    if file_ids is None:
        file_ids = DEFAULT_DRIVE_IDS

    raw_dir = os.path.join('data', 'raw')
    os.makedirs(raw_dir, exist_ok=True)

    list_dfs = []

    for idx, file_id in enumerate(file_ids, start=1):
        local_path = os.path.join(raw_dir, f'prf_data_{file_id}.csv')

        # Realiza o download se o arquivo local não existir
        if not os.path.exists(local_path):
            print(
                f'Baixando arquivo {idx}/{len(file_ids)} do Google Drive (ID:'
                f' {file_id})...'
            )
            try:
                gdown.download(id=file_id, output=local_path, quiet=False)
            except Exception as err:
                print(f'Erro no gdown ao baixar o ID {file_id}: {err}')

        # Tenta ler o arquivo CSV
        if os.path.exists(local_path):
            try:
                print(f'Lendo arquivo {idx}/{len(file_ids)}: {local_path}...')
                df_temp = pd.read_csv(
                    local_path, sep=';', encoding='latin1', low_memory=False
                )
                df_temp.columns = df_temp.columns.str.lower().str.strip()
                list_dfs.append(df_temp)
            except Exception as err:
                print(f'Erro ao ler o arquivo {local_path}: {err}')

    if not list_dfs:
        raise ValueError(
            'Nenhum arquivo pôde ser carregado. Verifique a conexão e as'
            ' permissões dos IDs no Google Drive.'
        )

    print('Unificando bases...')
    df_unified = pd.concat(list_dfs, ignore_index=True)

    # Tratamento seguro das coordenadas geográficas
    for col in ['latitude', 'longitude']:
        if col in df_unified.columns:
            df_unified[col] = df_unified[col].astype(str).str.replace(',', '.')
            df_unified[col] = pd.to_numeric(df_unified[col], errors='coerce')

    # Tratamento de datas
    if 'data_inversa' in df_unified.columns:
        df_unified['data_inversa'] = pd.to_datetime(
            df_unified['data_inversa'], errors='coerce'
        )
        df_unified['ano'] = df_unified['data_inversa'].dt.year
        df_unified['mes'] = df_unified['data_inversa'].dt.month
        df_unified['mes_ano'] = (
            df_unified['data_inversa'].dt.to_period('M').astype(str)
        )

    print(f'Sucesso! Base unificada com {len(df_unified):,} linhas.')
    return df_unified