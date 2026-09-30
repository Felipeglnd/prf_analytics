import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
import urllib.request

import gdown
import pandas as pd
import streamlit as st

# Configuração do Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Diretório raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent

GEOJSON_URL = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

DEFAULT_DRIVE_IDS = [
    '1TdIUpSkghOxLmVwWwbYH1GI9ICMUxWv0',  # 2023
    '13PSlOxY1JUhN9eJIcDzEUg4Wq5FC0XRJ',  # 2024
    '1BUikMurrueItOiAJCEd8YAyNdlrNahMG',  # 2025
]


@st.cache_data(show_spinner="Carregando GeoJSON dos estados...")
def carregar_geojson(caminho_geojson: Union[Path, str] = ROOT_DIR / "data" / "br_states.json") -> Dict:
    """Carrega o arquivo GeoJSON dos estados do Brasil."""
    caminho = Path(caminho_geojson)
    
    if not caminho.exists():
        logger.info(f"GeoJSON não encontrado em {caminho}. Baixando automaticamente...")
        caminho.parent.mkdir(parents=True, exist_ok=True)
        try:
            urllib.request.urlretrieve(GEOJSON_URL, caminho)
        except Exception as err:
            logger.error(f"Erro ao baixar o GeoJSON: {err}")
            raise FileNotFoundError(f"Arquivo GeoJSON não encontrado e falha ao baixar: {err}")

    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)


@st.cache_data(show_spinner="Carregando e processando dados da PRF...")
def carregar_dados(file_ids: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Baixa os arquivos do Google Drive (se necessário), une-os em um único DataFrame,
    trata os dados e salva um único CSV concatenado e limpo no disco.
    """
    if file_ids is None:
        file_ids = DEFAULT_DRIVE_IDS

    raw_dir = ROOT_DIR / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Caminho do arquivo unificado final
    arquivo_concatenado_path = raw_dir / "prf_dados_concatenados.csv"

    # Se o arquivo já existe e não está vazio, lê direto dele para poupar tempo
    if arquivo_concatenado_path.exists() and arquivo_concatenado_path.stat().st_size > 0:
        logger.info(f"Carregando dados unificados do cache local: {arquivo_concatenado_path}")
        df_unified = pd.read_csv(arquivo_concatenado_path, low_memory=False)
        if 'data_inversa' in df_unified.columns:
            df_unified['data_inversa'] = pd.to_datetime(df_unified['data_inversa'], errors='coerce')
        return df_unified

    # Caso contrário, baixa os arquivos individuais, concatena e salva
    list_dfs = []

    for idx, file_id in enumerate(file_ids, start=1):
        temp_file_path = raw_dir / f"temp_{file_id}.csv"

        if not temp_file_path.exists() or temp_file_path.stat().st_size == 0:
            logger.info(f"Baixando base PRF {idx}/{len(file_ids)} do Google Drive (ID: {file_id})...")
            try:
                gdown.download(id=file_id, output=str(temp_file_path), quiet=False)
            except Exception as err:
                logger.error(f"Erro no gdown ao baixar o ID {file_id}: {err}")

        if temp_file_path.exists() and temp_file_path.stat().st_size > 0:
            try:
                df_temp = pd.read_csv(
                    temp_file_path,
                    sep=';',
                    encoding='latin1',
                    low_memory=False,
                    on_bad_lines='skip',
                )
                df_temp.columns = df_temp.columns.str.lower().str.strip()
                list_dfs.append(df_temp)
            except Exception as err:
                logger.error(f"Erro ao ler o arquivo {temp_file_path}: {err}")
            finally:
                # Remove o arquivo temporário baixado individualmente
                if temp_file_path.exists():
                    temp_file_path.unlink(missing_ok=True)

    if not list_dfs:
        raise ValueError(
            'Nenhum arquivo pôde ser carregado. Verifique a conexão e as'
            ' permissões dos IDs no Google Drive.'
        )

    # Unifica todos os DataFrames
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

    # Tratamento de colunas de métricas
    colunas_kpi = ['mortos', 'feridos_graves', 'feridos_leves', 'feridos', 'pessoas']
    for col in colunas_kpi:
        if col in df_unified.columns:
            df_unified[col] = pd.to_numeric(df_unified[col], errors='coerce').fillna(0)

    # Tratamento de datas
    if 'data_inversa' in df_unified.columns:
        df_unified['data_inversa'] = pd.to_datetime(
            df_unified['data_inversa'], errors='coerce'
        )
        df_unified['ano_base'] = df_unified['data_inversa'].dt.year
        df_unified['mes_num'] = df_unified['data_inversa'].dt.month
        df_unified['mes'] = df_unified['data_inversa'].dt.to_period('M').astype(str)

    # Salva o resultado final unificado no disco em um único arquivo
    logger.info(f"Salvando base unificada em {arquivo_concatenado_path}...")
    df_unified.to_csv(arquivo_concatenado_path, index=False)

    return df_unified


load_data = carregar_dados


# Ids das bases novas
BASES_ADICIONAIS = {
    'frota_media_consolidada_2023_2025': '1H8CHfMJbwDLCxzi6zwR7ulUmleaOZKij',
    'frota_agrupada_por_estado_2023_2025': '1vkXWiFWymu52T9Uytu1PSj3nx-SRY8Jj'
}

@st.cache_data(show_spinner="Carregando bases adicionais...")
def carregar_bases_adicionais() -> Dict[str, pd.DataFrame]:
    """
    Baixa arquivos extras do Google Drive e os retorna
    em um dicionário de DataFrames, sem concatenar.
    """
    raw_dir = ROOT_DIR / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    dicionario_dfs = {}

    for nome_base, file_id in BASES_ADICIONAIS.items():
        arquivo_path = raw_dir / f"{nome_base}.csv"

        # Baixa do Drive se o arquivo não existir localmente
        if not arquivo_path.exists() or arquivo_path.stat().st_size == 0:
            logger.info(f"Baixando '{nome_base}' do Google Drive (ID: {file_id})...")
            try:
                gdown.download(id=file_id, output=str(arquivo_path), quiet=False)
            except Exception as err:
                logger.error(f"Erro ao baixar a base '{nome_base}' (ID {file_id}): {err}")
                continue

        # Carrega o arquivo baixado
        if arquivo_path.exists() and arquivo_path.stat().st_size > 0:
            try:
                df = pd.read_csv(
                    arquivo_path,
                    sep=';', 
                    encoding='latin1',
                    low_memory=False,
                    on_bad_lines='skip'
                )
                dicionario_dfs[nome_base] = df
                logger.info(f"Base '{nome_base}' carregada com sucesso.")
            except Exception as err:
                logger.error(f"Erro ao ler o arquivo {arquivo_path}: {err}")

    return dicionario_dfs