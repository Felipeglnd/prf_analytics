# -*- coding: utf-8 -*-
"""
data-validacao.py

Script de validação das tabelas usadas no projeto prf_analytics:
  1. prf_acidentes_consolidado.csv           -> base principal de acidentes (2023-2025)
  2. frota_agrupada_por_estado_2023_2025.csv -> frota de veículos agrupada por UF
  3. frota_media_consolidada_2023_2025.csv   -> frota média consolidada

Objetivo:
    Comprovar a integridade das tabelas que alimentam o dashboard Streamlit.

    Para a base de acidentes (schema conhecido, padrão PRF), a validação
    é específica:
      1. Contagem de linhas e de acidentes únicos (coluna `id`)
      2. Linhas totalmente duplicadas
      3. Nulos em colunas obrigatórias
      4. Consistência de categorias (grafia) entre os anos
      5. Totais agregados (mortos, feridos, ilesos) por ano
      6. Intervalo de datas por ano (detectar "vazamento" de datas)
      7. UFs válidas e consistentes

    Para as tabelas de frota (schema não confirmado ainda), a validação
    é GENÉRICA: detecta automaticamente colunas de UF/estado e de ano,
    reporta shape, tipos, nulos, duplicatas, cobertura de UFs/anos, e
    cruza as chaves (UF, ano) entre as duas tabelas de frota.

    -> Se você souber os nomes exatos das colunas de frota, ajuste a
       seção "VALIDAÇÃO DAS TABELAS DE FROTA" para checagens mais
       precisas (ex.: comparar somas/médias entre as duas tabelas).

Como rodar:
    python data-validacao.py

Saída:
    - Log no console com cada verificação e status (OK / ATENÇÃO)
    - Arquivo `data-validation/relatorio_validacao.md` gerado automaticamente
      com o resumo de todas as checagens (pronto para anexar como evidência
      no repositório).
"""

import re
import pandas as pd
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO — caminhos relativos à localização deste arquivo, não ao
# diretório de onde o script é executado (evita erro de "arquivo não
# encontrado" ao rodar pelo botão Run do VS Code, por exemplo).
# ---------------------------------------------------------------------------

# Este script vive em: prf_analytics/data/data-validation/data-validacao.py
# Os dados brutos vivem em: prf_analytics/data/raw/
BASE_DIR = Path(__file__).resolve().parent          # .../data/data-validation
PASTA_DADOS = BASE_DIR.parent / "raw"                # .../data/raw

CAMINHO_ACIDENTES = PASTA_DADOS / "prf_acidentes_consolidado.csv"
CAMINHO_FROTA_AGRUPADA = PASTA_DADOS / "frota_agrupada_por_estado_2023_2025.csv"
CAMINHO_FROTA_MEDIA = PASTA_DADOS / "frota_media_consolidada_2023_2025.csv"

PASTA_SAIDA = BASE_DIR
PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

# Colunas obrigatórias na base de acidentes (não podem ser nulas)
COLUNAS_OBRIGATORIAS = ["id", "data_inversa", "uf", "br", "municipio", "tipo_acidente"]

# Colunas numéricas de severidade
COLUNAS_SEVERIDADE = ["ilesos", "feridos_leves", "feridos_graves", "mortos"]

# Colunas categóricas onde inconsistência de grafia entre anos é comum
COLUNAS_CATEGORICAS = ["tipo_acidente", "causa_acidente", "classificacao_acidente"]

ANOS_ESPERADOS = {2023, 2024, 2025}

UFS_VALIDAS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
}

# Algumas fontes (ex.: tabelas de frota) trazem o nome do estado por extenso
# em vez da sigla usada na base de acidentes. Mapeamento para normalizar.
NOME_UF_PARA_SIGLA = {
    "ACRE": "AC", "ALAGOAS": "AL", "AMAPA": "AP", "AMAZONAS": "AM",
    "BAHIA": "BA", "CEARA": "CE", "DISTRITO FEDERAL": "DF",
    "ESPIRITO SANTO": "ES", "GOIAS": "GO", "MARANHAO": "MA",
    "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS", "MINAS GERAIS": "MG",
    "PARA": "PA", "PARAIBA": "PB", "PARANA": "PR", "PERNAMBUCO": "PE",
    "PIAUI": "PI", "RIO DE JANEIRO": "RJ", "RIO GRANDE DO NORTE": "RN",
    "RIO GRANDE DO SUL": "RS", "RONDONIA": "RO", "RORAIMA": "RR",
    "SANTA CATARINA": "SC", "SAO PAULO": "SP", "SERGIPE": "SE",
    "TOCANTINS": "TO",
}

# Tolerância para comparar colunas numéricas de ponto flutuante (evita que
# ruído de arredondamento, tipo 36843.16666666666 vs 36843.166666666664,
# seja reportado como divergência real de dado)
TOLERANCIA_FLOAT = 1e-6


def normalizar_uf(valor):
    """Converte UF por extenso ('ACRE') ou sigla ('AC') para sigla padrão.
    Retorna None se o valor não corresponder a nenhuma UF conhecida
    (ex.: 'NÃO IDENTIFICADO', 'SEM INFORMAÇÃO')."""
    if pd.isna(valor):
        return None
    v = str(valor).strip().upper()
    if v in UFS_VALIDAS:
        return v
    return NOME_UF_PARA_SIGLA.get(v)

resultados = []  # acumula cada verificação para o relatório final


def registrar(verificacao, esperado, obtido, ok, observacao=""):
    status = "✅ OK" if ok else "⚠️ ATENÇÃO"
    resultados.append(
        {
            "verificacao": verificacao,
            "esperado": esperado,
            "obtido": obtido,
            "status": status,
            "observacao": observacao,
        }
    )
    print(f"[{status}] {verificacao} | esperado: {esperado} | obtido: {obtido}")
    if observacao:
        print(f"          obs: {observacao}")


def ler_csv(caminho, sep_tentativas=(";", ",")):
    """Lê um CSV tentando detectar separador e encoding automaticamente."""
    for encoding in ("utf-8", "latin1"):
        for sep in sep_tentativas:
            try:
                df = pd.read_csv(caminho, sep=sep, encoding=encoding, low_memory=False)
                if df.shape[1] > 1:  # separador certo produz mais de 1 coluna
                    return df
            except Exception:
                continue
    # último recurso: deixa o pandas tentar sozinho
    return pd.read_csv(caminho, low_memory=False)


def detectar_coluna(df, palavras_chave):
    """Encontra a primeira coluna cujo nome contenha alguma palavra-chave."""
    for col in df.columns:
        nome = col.strip().lower()
        if any(p in nome for p in palavras_chave):
            return col
    return None


# ---------------------------------------------------------------------------
# 1. VALIDAÇÃO DA BASE DE ACIDENTES CONSOLIDADA
# ---------------------------------------------------------------------------

print("=" * 70)
print("VALIDANDO: prf_acidentes_consolidado.csv")
print("=" * 70)

df_acidentes = ler_csv(CAMINHO_ACIDENTES)

if "data_inversa" in df_acidentes.columns:
    df_acidentes["data_inversa"] = pd.to_datetime(df_acidentes["data_inversa"], errors="coerce")
    df_acidentes["_ano"] = df_acidentes["data_inversa"].dt.year

# 1.1 Total de linhas e de acidentes únicos
total_linhas = len(df_acidentes)
total_acidentes = df_acidentes["id"].nunique() if "id" in df_acidentes.columns else None
registrar(
    "Base de acidentes carregada",
    "> 0 linhas",
    total_linhas,
    total_linhas > 0,
)
if total_acidentes is not None:
    registrar(
        "Total de acidentes únicos (id.nunique) vs. total de linhas",
        f"{total_acidentes} acidentes em {total_linhas} linhas",
        f"média de {total_linhas / total_acidentes:.2f} linhas por acidente",
        True,
        "Cada acidente pode ter várias linhas (uma por pessoa/veículo/causa envolvida). "
        "Não confundir total de linhas com total de acidentes no dashboard.",
    )

# 1.2 Linhas totalmente duplicadas
dup = df_acidentes.duplicated().sum()
registrar("Linhas totalmente duplicadas", 0, int(dup), dup == 0)

# 1.3 Nulos em colunas obrigatórias
colunas_presentes = [c for c in COLUNAS_OBRIGATORIAS if c in df_acidentes.columns]
nulos = df_acidentes[colunas_presentes].isnull().sum()
total_nulos = int(nulos.sum())
registrar(
    "Nulos em colunas obrigatórias (id, data, uf, br, municipio, tipo_acidente)",
    0,
    total_nulos,
    total_nulos == 0,
    nulos[nulos > 0].to_dict() if total_nulos else "",
)

# 1.4 Anos presentes na base — deve ser exatamente 2023, 2024, 2025
if "_ano" in df_acidentes.columns:
    anos_presentes = set(int(a) for a in df_acidentes["_ano"].dropna().unique())
    registrar(
        "Anos presentes na base de acidentes",
        sorted(ANOS_ESPERADOS),
        sorted(anos_presentes),
        anos_presentes == ANOS_ESPERADOS,
    )

    # 1.5 Totais de severidade por ano (o que normalmente vai pro dashboard)
    for coluna in COLUNAS_SEVERIDADE:
        if coluna not in df_acidentes.columns:
            continue
        totais_por_ano = df_acidentes.groupby("_ano")[coluna].sum().to_dict()
        print(f"    Totais de '{coluna}' por ano: {totais_por_ano}")

# 1.6 UFs válidas
if "uf" in df_acidentes.columns:
    ufs_encontradas = set(df_acidentes["uf"].dropna().unique())
    ufs_invalidas = ufs_encontradas - UFS_VALIDAS
    registrar(
        "UFs pertencem ao conjunto de 27 UFs válidas",
        0,
        len(ufs_invalidas),
        len(ufs_invalidas) == 0,
        sorted(ufs_invalidas) if ufs_invalidas else "",
    )

# 1.7 Categorias com grafia divergente entre anos
if "_ano" in df_acidentes.columns:
    for coluna in COLUNAS_CATEGORICAS:
        if coluna not in df_acidentes.columns:
            continue
        categorias_por_ano = {
            ano: set(grupo[coluna].dropna().str.strip().str.lower())
            for ano, grupo in df_acidentes.groupby("_ano")
        }
        anos_com_dados = [a for a in categorias_por_ano if a in ANOS_ESPERADOS]
        todas = set().union(*categorias_por_ano.values()) if categorias_por_ano else set()
        divergentes = {
            cat for cat in todas
            if not all(cat in categorias_por_ano.get(ano, set()) for ano in anos_com_dados)
        }
        registrar(
            f"Categorias de '{coluna}' consistentes entre os anos (sem divergência de grafia)",
            "sem divergências",
            f"{len(divergentes)} categoria(s) com grafia divergente" if divergentes else "sem divergências",
            len(divergentes) == 0,
            sorted(divergentes)[:10] if divergentes else "",
        )

# 1.8 Coluna ano_base bate com o ano de data_inversa
if "ano_base" in df_acidentes.columns and "_ano" in df_acidentes.columns:
    divergencia_ano_base = (
        df_acidentes["ano_base"].astype("Int64") != df_acidentes["_ano"].astype("Int64")
    ).sum()
    registrar(
        "Coluna 'ano_base' consistente com o ano de 'data_inversa'",
        0,
        int(divergencia_ano_base),
        divergencia_ano_base == 0,
    )

# ---------------------------------------------------------------------------
# 2. VALIDAÇÃO DAS TABELAS DE FROTA (schema conhecido)
# ---------------------------------------------------------------------------
# frota_agrupada_por_estado: uf, ano, tipo_veiculo, especie_veiculo, eixos, qtd_veiculos
# frota_media_consolidada:   uf, ano, municipio, tipo_veiculo, especie_veiculo, eixos, qtd_veiculos
#
# A tabela "agrupada por estado" deveria ser exatamente a tabela "consolidada"
# agregada por (uf, ano, tipo_veiculo, especie_veiculo, eixos), somando
# qtd_veiculos de todos os municípios. É essa relação que validamos abaixo.

CHAVE_FROTA = ["uf", "ano", "tipo_veiculo", "especie_veiculo", "eixos"]


def validar_tabela_frota(caminho, nome_tabela, colunas_chave, tem_municipio):
    print("\n" + "=" * 70)
    print(f"VALIDANDO: {nome_tabela}")
    print("=" * 70)

    df = ler_csv(caminho)
    print(f"    Shape: {df.shape}")
    print(f"    Colunas: {list(df.columns)}")

    registrar(f"[{nome_tabela}] Tabela carregada", "> 0 linhas", len(df), len(df) > 0)

    # Duplicatas totais
    dup = df.duplicated().sum()
    registrar(f"[{nome_tabela}] Linhas totalmente duplicadas", 0, int(dup), dup == 0)

    # Nulos por coluna
    nulos = df.isnull().sum()
    total_nulos = int(nulos.sum())
    registrar(
        f"[{nome_tabela}] Total de valores nulos na tabela",
        0,
        total_nulos,
        total_nulos == 0,
        nulos[nulos > 0].to_dict() if total_nulos else "",
    )

    # qtd_veiculos não pode ser negativo
    if "qtd_veiculos" in df.columns:
        negativos = (pd.to_numeric(df["qtd_veiculos"], errors="coerce") < 0).sum()
        registrar(
            f"[{nome_tabela}] 'qtd_veiculos' sem valores negativos",
            0,
            int(negativos),
            negativos == 0,
        )

    # Cobertura das 27 UFs (aceita sigla ou nome por extenso)
    if "uf" in df.columns:
        df["_uf_normalizada"] = df["uf"].apply(normalizar_uf)
        nao_mapeados = df.loc[df["_uf_normalizada"].isnull(), "uf"].dropna().unique()
        ufs_encontradas = set(df["_uf_normalizada"].dropna().unique())
        faltando = UFS_VALIDAS - ufs_encontradas
        registrar(
            f"[{nome_tabela}] Cobertura das 27 UFs (sigla ou nome por extenso)",
            27,
            len(ufs_encontradas),
            len(faltando) == 0 and len(nao_mapeados) == 0,
            f"faltando: {sorted(faltando)}; valores não reconhecidos como UF: {sorted(nao_mapeados)}"
            if (faltando.__len__() or len(nao_mapeados)) else "",
        )

    # Cobertura dos anos 2023-2025
    if "ano" in df.columns:
        anos_encontrados = set(int(a) for a in pd.to_numeric(df["ano"], errors="coerce").dropna().unique())
        registrar(
            f"[{nome_tabela}] Cobertura dos anos 2023-2025",
            sorted(ANOS_ESPERADOS),
            sorted(anos_encontrados),
            ANOS_ESPERADOS.issubset(anos_encontrados),
        )

    # Duplicidade da chave de granularidade da tabela
    chave_presente = [c for c in colunas_chave if c in df.columns]
    if len(chave_presente) == len(colunas_chave):
        chave_dup = df.duplicated(subset=chave_presente).sum()
        registrar(
            f"[{nome_tabela}] Chave {chave_presente} sem duplicidade",
            0,
            int(chave_dup),
            chave_dup == 0,
        )

    return df


df_frota_agrupada = validar_tabela_frota(
    CAMINHO_FROTA_AGRUPADA, "frota_agrupada_por_estado", CHAVE_FROTA, tem_municipio=False
)
df_frota_media = validar_tabela_frota(
    CAMINHO_FROTA_MEDIA, "frota_media_consolidada", CHAVE_FROTA + ["municipio"], tem_municipio=True
)

# 2.1 A soma de qtd_veiculos por município na tabela consolidada deve bater
#     exatamente com qtd_veiculos na tabela agrupada por estado
colunas_necessarias = CHAVE_FROTA + ["qtd_veiculos"]
if all(c in df_frota_agrupada.columns for c in colunas_necessarias) and all(
    c in df_frota_media.columns for c in colunas_necessarias
):
    agregado_a_partir_da_media = (
        df_frota_media.groupby(CHAVE_FROTA, dropna=False)["qtd_veiculos"]
        .sum()
        .reset_index()
        .rename(columns={"qtd_veiculos": "qtd_veiculos_calculado"})
    )
    comparacao = df_frota_agrupada.merge(
        agregado_a_partir_da_media, on=CHAVE_FROTA, how="outer", indicator=True
    )
    so_em_um_lado = (comparacao["_merge"] != "both").sum()
    comparacao_ambos = comparacao[comparacao["_merge"] == "both"].copy()
    # Comparação com tolerância — evita falso positivo por ruído de
    # ponto flutuante (ex.: 36843.16666666666 vs 36843.166666666664)
    diferenca = (
        comparacao_ambos["qtd_veiculos"] - comparacao_ambos["qtd_veiculos_calculado"]
    ).abs()
    mascara_divergente = diferenca > TOLERANCIA_FLOAT
    divergentes = mascara_divergente.sum()
    registrar(
        "Soma de qtd_veiculos por município (consolidada) bate com a agrupada por estado",
        0,
        f"{int(so_em_um_lado)} chave(s) só em uma tabela, {int(divergentes)} valor(es) divergente(s)",
        so_em_um_lado == 0 and divergentes == 0,
        (
            comparacao_ambos.loc[
                mascara_divergente,
                CHAVE_FROTA + ["qtd_veiculos", "qtd_veiculos_calculado"],
            ]
            .head(10)
            .to_dict("records")
            if divergentes
            else ""
        ),
    )
else:
    print("\n⚠️  Não foi possível comparar as somas — alguma coluna esperada não está presente.")

# ---------------------------------------------------------------------------
# 3. GERAÇÃO DO RELATÓRIO MARKDOWN (evidência para o repositório)
# ---------------------------------------------------------------------------

df_resultados = pd.DataFrame(resultados)
caminho_csv = PASTA_SAIDA / "evidencias_validacao.csv"
df_resultados.to_csv(caminho_csv, index=False, encoding="utf-8")

total_checks = len(df_resultados)
total_ok = (df_resultados["status"] == "✅ OK").sum()

linhas_md = [
    "# Relatório de Validação de Dados — prf_analytics",
    "",
    f"Gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M')} "
    "pelo script `data-validacao.py`.",
    "",
    "## Objetivo",
    "Verificar a integridade da base de acidentes consolidada e das tabelas "
    "de frota de veículos (2023-2025) utilizadas no dashboard.",
    "",
    f"## Resumo: {total_ok}/{total_checks} verificações OK",
    "",
    "| Verificação | Esperado | Obtido | Status |",
    "|---|---|---|---|",
]
for r in resultados:
    linhas_md.append(f"| {r['verificacao']} | {r['esperado']} | {r['obtido']} | {r['status']} |")

linhas_md += ["", "## Observações / divergências encontradas", ""]
observacoes = [r for r in resultados if r["observacao"]]
if observacoes:
    for r in observacoes:
        linhas_md.append(f"- **{r['verificacao']}**: {r['observacao']}")
else:
    linhas_md.append("Nenhuma divergência com observações adicionais.")

linhas_md += [
    "",
    "## Conclusão",
    (
        "Os dados utilizados no dashboard foram validados com sucesso: "
        "todas as verificações passaram."
        if total_ok == total_checks
        else "Foram encontradas divergências (marcadas com ⚠️ acima). "
        "Revisar as tabelas antes de considerar os dados validados."
    ),
]

caminho_md = PASTA_SAIDA / "relatorio_validacao.md"
caminho_md.write_text("\n".join(linhas_md), encoding="utf-8")

print("\n" + "=" * 70)
print(f"Validação concluída: {total_ok}/{total_checks} verificações OK")
print(f"Relatório salvo em: {caminho_md}")
print(f"Evidências (CSV) salvas em: {caminho_csv}")
print("=" * 70)