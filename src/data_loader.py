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

# Diretório raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent

GEOJSON_URL = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

# ==============================================================================
# IDS DO GOOGLE DRIVE (Arquivos Consolidados)
# ==============================================================================
ID_ACIDENTES = '1eBg_ZKzTNr6c6bi6Zu4ztQfXbGeR_IQx'
ID_VEICULOS = '1tIg-N6PCftTPOiziO65G5GDN7Ve7Gupj'

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


<<<<<<< HEAD
@st.cache_data(show_spinner="Carregando e processando base consolidada de acidentes...")
def carregar_dados_acidentes() -> pd.DataFrame:
    """Baixa (se necessário) e trata o arquivo CSV consolidado de acidentes do Google Drive."""
=======
@st.cache_data(show_spinner="Carregando e processando dados da PRF...")
def carregar_dados(file_ids: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Baixa os arquivos do Google Drive (se necessário), une-os em um único DataFrame,
    trata os dados e salva um único CSV concatenado e limpo no disco.
    """
    if file_ids is None:
        file_ids = DEFAULT_DRIVE_IDS

>>>>>>> a1aa441262e020dfd1f242f5ebd0de7f1c2527e2
    raw_dir = ROOT_DIR / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    local_path = raw_dir / "prf_acidentes_consolidado.csv"

<<<<<<< HEAD
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
=======
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
>>>>>>> a1aa441262e020dfd1f242f5ebd0de7f1c2527e2

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

<<<<<<< HEAD
    # Tratamento da coluna 'horario' para extrair a hora (0-23)
    if 'horario' in df_unified.columns:
        df_unified['hora'] = pd.to_datetime(
            df_unified['horario'].astype(str), format='%H:%M:%S', errors='coerce'
        ).dt.hour
        
        if df_unified['hora'].isna().all():
            df_unified['hora'] = pd.to_datetime(
                df_unified['horario'].astype(str), format='%H:%M', errors='coerce'
            ).dt.hour
=======
    # Salva o resultado final unificado no disco em um único arquivo
    logger.info(f"Salvando base unificada em {arquivo_concatenado_path}...")
    df_unified.to_csv(arquivo_concatenado_path, index=False)
>>>>>>> a1aa441262e020dfd1f242f5ebd0de7f1c2527e2

    return df_unified


<<<<<<< HEAD
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
=======
load_data = carregar_dados
>>>>>>> a1aa441262e020dfd1f242f5ebd0de7f1c2527e2
