# Relatório de Validação de Dados — prf_analytics

Gerado automaticamente em 30/09/2026 22:07 pelo script `data-validacao.py`.

## Escopo da validação
Este relatório prioriza integridade estrutural, cobertura temporal, duplicidade, chaves e consistência entre as tabelas. Diferenças de nomenclatura entre anos, valores ausentes na coluna BR e valores sentinela de UF não são tratados como falhas estruturais.

## Objetivo
Verificar a integridade da base de acidentes consolidada e das tabelas de frota de veículos (2023-2025) utilizadas no dashboard.

## Resumo: 22/22 verificações OK

| Verificação | Esperado | Obtido | Status |
|---|---|---|---|
| Base de acidentes carregada | > 0 linhas | 1758277 | ✅ OK |
| Total de acidentes únicos (id.nunique) vs. total de linhas | 213452 acidentes em 1758277 linhas | média de 8.24 linhas por acidente | ✅ OK |
| Linhas totalmente duplicadas | 0 | 0 | ✅ OK |
| Colunas estruturais da base de acidentes presentes | todas as colunas essenciais presentes | todas presentes | ✅ OK |
| Anos presentes na base de acidentes | [2023, 2024, 2025] | [2023, 2024, 2025] | ✅ OK |
| UFs pertencem ao conjunto de 27 UFs válidas | 0 | 0 | ✅ OK |
| Coluna 'ano_base' consistente com o ano de 'data_inversa' | 0 | 0 | ✅ OK |
| [frota_agrupada_por_estado] Tabela carregada | > 0 linhas | 19664 | ✅ OK |
| [frota_agrupada_por_estado] Linhas totalmente duplicadas | 0 | 0 | ✅ OK |
| [frota_agrupada_por_estado] Total de valores nulos na tabela | 0 | 0 | ✅ OK |
| [frota_agrupada_por_estado] 'qtd_veiculos' sem valores negativos | 0 | 0 | ✅ OK |
| [frota_agrupada_por_estado] UFs válidas e valores sentinela reconhecidos | 27 UFs presentes; apenas valores sentinela conhecidos além delas | 27 UFs presentes; valores adicionais: ['NÃO IDENTIFICADO', 'NÃO SE APLICA', 'SEM INFORMAÇÃO'] | ✅ OK |
| [frota_agrupada_por_estado] Cobertura dos anos 2023-2025 | [2023, 2024, 2025] | [2023, 2024, 2025] | ✅ OK |
| [frota_agrupada_por_estado] Chave ['uf', 'ano', 'tipo_veiculo', 'especie_veiculo', 'eixos'] sem duplicidade | 0 | 0 | ✅ OK |
| [frota_media_consolidada] Tabela carregada | > 0 linhas | 819274 | ✅ OK |
| [frota_media_consolidada] Linhas totalmente duplicadas | 0 | 0 | ✅ OK |
| [frota_media_consolidada] Total de valores nulos na tabela | 0 | 0 | ✅ OK |
| [frota_media_consolidada] 'qtd_veiculos' sem valores negativos | 0 | 0 | ✅ OK |
| [frota_media_consolidada] UFs válidas e valores sentinela reconhecidos | 27 UFs presentes; apenas valores sentinela conhecidos além delas | 27 UFs presentes; valores adicionais: ['NÃO IDENTIFICADO', 'NÃO SE APLICA', 'SEM INFORMAÇÃO'] | ✅ OK |
| [frota_media_consolidada] Cobertura dos anos 2023-2025 | [2023, 2024, 2025] | [2023, 2024, 2025] | ✅ OK |
| [frota_media_consolidada] Chave ['uf', 'ano', 'tipo_veiculo', 'especie_veiculo', 'eixos', 'municipio'] sem duplicidade | 0 | 0 | ✅ OK |
| Soma de qtd_veiculos por município (consolidada) bate com a agrupada por estado | 0 | 0 chave(s) só em uma tabela, 0 valor(es) divergente(s) | ✅ OK |

## Observações / divergências encontradas

- **Total de acidentes únicos (id.nunique) vs. total de linhas**: Cada acidente pode ter várias linhas (uma por pessoa/veículo/causa envolvida). Não confundir total de linhas com total de acidentes no dashboard.
- **Colunas estruturais da base de acidentes presentes**: A coluna 'br' não é usada como critério eliminatório neste relatório.

## Conclusão
As verificações estruturais executadas passaram.