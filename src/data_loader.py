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

# Diretório raiz do projeto (subindo um nível a partir de 'src')
ROOT_DIR = Path(__file__).resolve().parent.parent

# URL pública de fallback para o GeoJSON dos estados do Brasil
GEOJSON_URL = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

# ==============================================================================
# IDS E CONFIGURAÇÕES DO GOOGLE DRIVE
# ==============================================================================
DEFAULT_DRIVE_IDS = [
    '1TdIUpSkghOxLmVwWwbYH1GI9ICMUxWv0',  # 2023 (~206 MB)
    '13PSlOxY1JUhN9eJIcDzEUg4Wq5FC0XRJ',  # 2024 (~222 MB)
    '1BUikMurrueItOiAJCEd8YAyNdlrNahMG',  # 2025 (~213 MB)
]

FROTA_DRIVE_ID = '1vkXWiFWymu52T9Uytu1PSj3nx-SRY8Jj'
RODOVIAS_DRIVE_ID = '1PxNnvQXJiAo2edFePvD7aXSg3AC_ypu0'


@st.cache_data(show_spinner="Carregando GeoJSON dos estados...")
def carregar_geojson(caminho_geojson: Union[Path, str] = ROOT_DIR / "data" / "br_states.json") -> Dict:
    """Carrega o arquivo GeoJSON dos estados do Brasil. Se não existir, faz o download automático."""
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
    """Baixa (se necessário), unifica e trata os arquivos CSV do Google Drive."""
    if file_ids is None:
        file_ids = DEFAULT_DRIVE_IDS

    raw_dir = ROOT_DIR / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    list_dfs = []

    for idx, file_id in enumerate(file_ids, start=1):
        local_path = raw_dir / f"prf_data_{file_id}.csv"

        if not local_path.exists() or local_path.stat().st_size == 0:
            logger.info(f"Baixando base PRF {idx}/{len(file_ids)} do Google Drive (ID: {file_id})...")
            try:
                gdown.download(id=file_id, output=str(local_path), quiet=True)
            except Exception as err:
                logger.error(f"Erro no gdown ao baixar o ID {file_id}: {err}")

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

    # Tratamento da coluna 'horario' para extrair a hora (0-23)
    if 'horario' in df_unified.columns:
        # Tenta converter o horário (HH:MM:SS ou HH:MM) e extrair a hora
        df_unified['hora'] = pd.to_datetime(
            df_unified['horario'].astype(str), format='%H:%M:%S', errors='coerce'
        ).dt.hour
        
        # Fallback caso os horários venham sem os segundos (%H:%M)
        if df_unified['hora'].isna().all():
            df_unified['hora'] = pd.to_datetime(
                df_unified['horario'].astype(str), format='%H:%M', errors='coerce'
            ).dt.hour

    return df_unified


# ==============================================================================
# CARGA DE BASES COMPLEMENTARES DO GOOGLE DRIVE
# ==============================================================================

@st.cache_data(show_spinner="Carregando dados da frota de veículos...")
def carregar_frota(file_id: str = FROTA_DRIVE_ID) -> pd.DataFrame:
    """Baixa (se necessário) e carrega a base de frota agrupada por estado do Google Drive."""
    raw_dir = ROOT_DIR / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    local_path = raw_dir / "frota_agrupada_por_estado_2023_2025.csv"

    if not local_path.exists() or local_path.stat().st_size == 0:
        logger.info(f"Baixando base de frota do Google Drive (ID: {file_id})...")
        try:
            gdown.download(id=file_id, output=str(local_path), quiet=True)
        except Exception as err:
            logger.error(f"Erro no gdown ao baixar frota: {err}")

    if not local_path.exists() or local_path.stat().st_size == 0:
        raise FileNotFoundError(f"Falha ao carregar frota do Google Drive (ID: {file_id}). Verifique as permissões de compartilhamento.")

    try:
        df = pd.read_csv(local_path, sep=';', encoding='utf-8', low_memory=False)
        if len(df.columns) <= 1:
            df = pd.read_csv(local_path, sep=',', encoding='utf-8', low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(local_path, sep=';', encoding='latin1', low_memory=False)
        if len(df.columns) <= 1:
            df = pd.read_csv(local_path, sep=',', encoding='latin1', low_memory=False)

    df.columns = df.columns.str.lower().str.strip()

    # =========================================================
    # Mapeamento de Nomes de Estados para Siglas (UF)
    # =========================================================
    if 'uf' in df.columns:
        mapa_estados = {
            'ACRE': 'AC', 'ALAGOAS': 'AL', 'AMAPÁ': 'AP', 'AMAPA': 'AP',
            'AMAZONAS': 'AM', 'BAHIA': 'BA', 'CEARÁ': 'CE', 'CEARA': 'CE',
            'DISTRITO FEDERAL': 'DF', 'ESPÍRITO SANTO': 'ES', 'ESPIRITO SANTO': 'ES',
            'GOIÁS': 'GO', 'GOIAS': 'GO', 'MARANHÃO': 'MA', 'MARANHAO': 'MA',
            'MATO GROSSO': 'MT', 'MATO GROSSO DO SUL': 'MS', 'MINAS GERAIS': 'MG',
            'PARÁ': 'PA', 'PARA': 'PA', 'PARAÍBA': 'PB', 'PARAIBA': 'PB',
            'PARANÁ': 'PR', 'PARANA': 'PR', 'PERNAMBUCO': 'PE', 'PIAUÍ': 'PI',
            'PIAUI': 'PI', 'RIO DE JANEIRO': 'RJ', 'RIO GRANDE DO NORTE': 'RN',
            'RIO GRANDE DO SUL': 'RS', 'RONDÔNIA': 'RO', 'RONDONIA': 'RO',
            'RORAIMA': 'RR', 'SANTA CATARINA': 'SC', 'SÃO PAULO': 'SP', 'SAO PAULO': 'SP',
            'SERGIPE': 'SE', 'TOCANTINS': 'TO'
        }
        
        # Remove espaços nas pontas e padroniza para maiúsculo antes de mapear
        df['uf'] = df['uf'].astype(str).str.strip().str.upper()
        
        # Mapeia os nomes para as siglas. Se algo não estiver no dicionário, mantém o valor original
        df['uf'] = df['uf'].map(mapa_estados).fillna(df['uf'])

    return df


@st.cache_data(show_spinner="Carregando relatório consolidado de rodovias...")
def carregar_relatorio_rodovias(file_id: str = RODOVIAS_DRIVE_ID) -> pd.DataFrame:
    """Baixa (se necessário) e carrega o relatório consolidado de rodovias do Google Drive."""
    raw_dir = ROOT_DIR / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    local_path = raw_dir / "relatorio_rodovias_federais_formato_longo_consolidado_2023_2025.csv"

    if not local_path.exists() or local_path.stat().st_size == 0:
        logger.info(f"Baixando relatório de rodovias do Google Drive (ID: {file_id})...")
        try:
            gdown.download(id=file_id, output=str(local_path), quiet=True)
        except Exception as err:
            logger.error(f"Erro no gdown ao baixar relatório de rodovias: {err}")

    if not local_path.exists() or local_path.stat().st_size == 0:
        raise FileNotFoundError(f"Falha ao carregar relatório de rodovias do Google Drive (ID: {file_id}). Verifique as permissões de compartilhamento.")

    try:
        df = pd.read_csv(local_path, sep=';', encoding='utf-8', low_memory=False)
        if len(df.columns) <= 1:
            df = pd.read_csv(local_path, sep=',', encoding='utf-8', low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(local_path, sep=';', encoding='latin1', low_memory=False)
        if len(df.columns) <= 1:
            df = pd.read_csv(local_path, sep=',', encoding='latin1', low_memory=False)

    df.columns = df.columns.str.lower().str.strip()
    return df


load_data = carregar_dados
