import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

import gdown
import pandas as pd
import streamlit as st

# Configuração do Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Diretório raiz do projeto (subindo um nível a partir de 'src')
ROOT_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# LISTA PADRÃO DE IDS DO GOOGLE DRIVE
# ==============================================================================
DEFAULT_DRIVE_IDS = [
    '1TdIUpSkghOxLmVwWwbYH1GI9ICMUxWv0',  # 2023 (~206 MB)
    '13PSlOxY1JUhN9eJIcDzEUg4Wq5FC0XRJ',  # 2024 (~222 MB)
    '1BUikMurrueItOiAJCEd8YAyNdlrNahMG',  # 2025 (~213 MB)
]


def carregar_geojson(caminho_geojson: Union[Path, str] = ROOT_DIR / "data" / "br_states.json") -> Dict:
    """Carrega o arquivo GeoJSON com os contornos dos estados do Brasil."""
    caminho = Path(caminho_geojson)
    
    if not caminho.exists():
        logger.error(f"Arquivo GeoJSON não encontrado em: {caminho}")
        raise FileNotFoundError(f"Arquivo GeoJSON não encontrado: {caminho}")

    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)


@st.cache_data(show_spinner="Carregando e processando dados da PRF...")
def carregar_dados(file_ids: Optional[List[str]] = None) -> pd.DataFrame:
    """Baixa (se necessário), unifica e trata os arquivos CSV do Google Drive."""
    if file_ids is None:
        file_ids = DEFAULT_DRIVE_IDS

    raw_dir = ROOT_DIR / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    list_dfs = []

    for idx, file_id in enumerate(file_ids, start=1):
        local_path = raw_dir / f"prf_data_{file_id}.csv"

        # Download via gdown se o arquivo não existir ou estiver corrompido/vazio
        if not local_path.exists() or local_path.stat().st_size == 0:
            logger.info(f"Baixando base PRF {idx}/{len(file_ids)} do Google Drive (ID: {file_id})...")
            try:
                gdown.download(id=file_id, output=str(local_path), quiet=True)
            except Exception as err:
                logger.error(f"Erro no gdown ao baixar o ID {file_id}: {err}")

        # Leitura do arquivo CSV com tratamentos de segurança
        if local_path.exists() and local_path.stat().st_size > 0:
            try:
                df_temp = pd.read_csv(
                    local_path,
                    sep=';',
                    encoding='latin1',
                    low_memory=False,
                    on_bad_lines='skip',
                )
                df_temp.columns = df_temp.columns.str.lower().str.strip()
                list_dfs.append(df_temp)
            except Exception as err:
                logger.error(f"Erro ao ler o arquivo {local_path}: {err}")
                # Remove o arquivo potencialmente corrompido para nova tentativa futura
                if local_path.exists():
                    local_path.unlink(missing_ok=True)

    if not list_dfs:
        raise ValueError(
            'Nenhum arquivo pôde ser carregado. Verifique a conexão e as'
            ' permissões dos IDs no Google Drive.'
        )

    df_unified = pd.concat(list_dfs, ignore_index=True)

    # Tratamento de coordenadas geográficas
    for col in ['latitude', 'longitude']:
        if col in df_unified.columns:
            df_unified[col] = (
                df_unified[col]
                .astype(str)
                .str.replace(',', '.', regex=False)
            )
            df_unified[col] = pd.to_numeric(df_unified[col], errors='coerce')

    # Garantir pré-tratamento numérico das colunas de métricas/KPIs
    colunas_kpi = ['mortos', 'feridos_graves', 'feridos_leves', 'feridos', 'pessoas']
    for col in colunas_kpi:
        if col in df_unified.columns:
            df_unified[col] = pd.to_numeric(df_unified[col], errors='coerce').fillna(0)

    # Tratamento de datas e extração de metadados temporais
    if 'data_inversa' in df_unified.columns:
        df_unified['data_inversa'] = pd.to_datetime(
            df_unified['data_inversa'], errors='coerce'
        )
        df_unified['ano_base'] = df_unified['data_inversa'].dt.year
        df_unified['mes_num'] = df_unified['data_inversa'].dt.month
        df_unified['mes'] = df_unified['data_inversa'].dt.to_period('M').astype(str)

    return df_unified


# Alias para compatibilidade
load_data = carregar_dados
