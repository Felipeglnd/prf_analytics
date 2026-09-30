import json
import logging
from pathlib import Path
from typing import Dict, Union
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
# IDS DO GOOGLE DRIVE (Arquivos Consolidados)
# ==============================================================================
ID_ACIDENTES = '1eBg_ZKzTNr6c6bi6Zu4ztQfXbGeR_IQx'
ID_VEICULOS = '1tIg-N6PCftTPOiziO65G5GDN7Ve7Gupj'

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


@st.cache_data(show_spinner="Carregando e processando base consolidada de acidentes...")
def carregar_dados_acidentes() -> pd.DataFrame:
    """Baixa (se necessário) e trata o arquivo CSV consolidado de acidentes do Google Drive."""
    raw_dir = ROOT_DIR / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    local_path = raw_dir / "prf_acidentes_consolidado.csv"

    if not local_path.exists() or local_path.stat().st_size == 0:
        logger.info("Baixando base consolidada de acidentes do Google Drive...")
        try:
            gdown.download(id=ID_ACIDENTES, output=str(local_path), quiet=True)
        except Exception as err:
            logger.error(f"Erro no gdown ao baixar acidentes: {err}")

    df_unified = pd.DataFrame()
    if local_path.exists() and local_path.stat().st_size > 0:
        try:
            # Tenta leitura com ';' (Padrão PRF)
            df_unified = pd.read_csv(local_path, sep=';', encoding='latin1', low_memory=False, on_bad_lines='skip')
            # Fallback caso o CSV consolidado tenha sido salvo com vírgula ','
            if len(df_unified.columns) == 1:
                df_unified = pd.read_csv(local_path, sep=',', encoding='utf-8', low_memory=False, on_bad_lines='skip')
            
            df_unified.columns = df_unified.columns.str.lower().str.strip()
        except Exception as err:
            logger.error(f"Erro ao ler o arquivo {local_path}: {err}")
            if local_path.exists():
                local_path.unlink(missing_ok=True)

    if df_unified.empty:
        raise ValueError('Nenhum dado pôde ser carregado. Verifique a conexão e as permissões no Google Drive.')

    # Tratamento de coordenadas geográficas
    for col in ['latitude', 'longitude']:
        if col in df_unified.columns:
            df_unified[col] = df_unified[col].astype(str).str.replace(',', '.', regex=False)
            df_unified[col] = pd.to_numeric(df_unified[col], errors='coerce')

    # Tratamento de colunas de métricas
    colunas_kpi = ['mortos', 'feridos_graves', 'feridos_leves', 'feridos', 'pessoas']
    for col in colunas_kpi:
        if col in df_unified.columns:
            df_unified[col] = pd.to_numeric(df_unified[col], errors='coerce').fillna(0)

    # Tratamento de datas
    if 'data_inversa' in df_unified.columns:
        df_unified['data_inversa'] = pd.to_datetime(df_unified['data_inversa'], errors='coerce')
        df_unified['ano_base'] = df_unified['data_inversa'].dt.year
        df_unified['mes_num'] = df_unified['data_inversa'].dt.month
        df_unified['mes'] = df_unified['data_inversa'].dt.to_period('M').astype(str)

    # Tratamento da coluna 'horario' para extrair a hora (0-23)
    if 'horario' in df_unified.columns:
        df_unified['hora'] = pd.to_datetime(
            df_unified['horario'].astype(str), format='%H:%M:%S', errors='coerce'
        ).dt.hour
        
        if df_unified['hora'].isna().all():
            df_unified['hora'] = pd.to_datetime(
                df_unified['horario'].astype(str), format='%H:%M', errors='coerce'
            ).dt.hour

    return df_unified


<<<<<<< HEAD
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
=======
@st.cache_data(show_spinner="Carregando e guardando em cache a base consolidada de veículos...")
def carregar_dados_veiculos() -> pd.DataFrame:
    """Baixa (se necessário) a base consolidada de frota de veículos do Google Drive."""
    raw_dir = ROOT_DIR / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    local_path = raw_dir / "frota_veiculos_consolidado.csv"

    if not local_path.exists() or local_path.stat().st_size == 0:
        logger.info("Baixando base de veículos do Google Drive...")
        try:
            gdown.download(id=ID_VEICULOS, output=str(local_path), quiet=True)
        except Exception as err:
            logger.error(f"Erro no gdown ao baixar veículos: {err}")

    df_veiculos = pd.DataFrame()
    if local_path.exists() and local_path.stat().st_size > 0:
        try:
            df_veiculos = pd.read_csv(local_path, sep=';', encoding='latin1', low_memory=False, on_bad_lines='skip')
            if len(df_veiculos.columns) == 1:
                df_veiculos = pd.read_csv(local_path, sep=',', encoding='utf-8', low_memory=False, on_bad_lines='skip')
            
            df_veiculos.columns = df_veiculos.columns.str.lower().str.strip()
        except Exception as err:
            logger.error(f"Erro ao ler o arquivo de veículos: {err}")

    return df_veiculos

# Alias para não quebrar compatibilidade
carregar_dados = carregar_dados_acidentes
>>>>>>> eb193cc6b64011c8ef1a0e220f83ba18a1793cad
