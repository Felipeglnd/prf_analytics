# Relatório de Validação de Dados — prf_analytics

Gerado automaticamente em 29/09/2026 23:52 pelo script `data-validacao.py`.

## Objetivo
Verificar a integridade da base de acidentes consolidada e das tabelas de frota de veículos (2023-2025) utilizadas no dashboard.

## Resumo: 20/25 verificações OK

| Verificação | Esperado | Obtido | Status |
|---|---|---|---|
| Base de acidentes carregada | > 0 linhas | 1758277 | ✅ OK |
| Total de acidentes únicos (id.nunique) vs. total de linhas | 213452 acidentes em 1758277 linhas | média de 8.24 linhas por acidente | ✅ OK |
| Linhas totalmente duplicadas | 0 | 0 | ✅ OK |
| Nulos em colunas obrigatórias (id, data, uf, br, municipio, tipo_acidente) | 0 | 4628 | ⚠️ ATENÇÃO |
| Anos presentes na base de acidentes | [2023, 2024, 2025] | [2023, 2024, 2025] | ✅ OK |
| UFs pertencem ao conjunto de 27 UFs válidas | 0 | 0 | ✅ OK |
| Categorias de 'tipo_acidente' consistentes entre os anos (sem divergência de grafia) | sem divergências | 1 categoria(s) com grafia divergente | ⚠️ ATENÇÃO |
| Categorias de 'causa_acidente' consistentes entre os anos (sem divergência de grafia) | sem divergências | 6 categoria(s) com grafia divergente | ⚠️ ATENÇÃO |
| Categorias de 'classificacao_acidente' consistentes entre os anos (sem divergência de grafia) | sem divergências | sem divergências | ✅ OK |
| Coluna 'ano_base' consistente com o ano de 'data_inversa' | 0 | 0 | ✅ OK |
| [frota_agrupada_por_estado] Tabela carregada | > 0 linhas | 19664 | ✅ OK |
| [frota_agrupada_por_estado] Linhas totalmente duplicadas | 0 | 0 | ✅ OK |
| [frota_agrupada_por_estado] Total de valores nulos na tabela | 0 | 0 | ✅ OK |
| [frota_agrupada_por_estado] 'qtd_veiculos' sem valores negativos | 0 | 0 | ✅ OK |
| [frota_agrupada_por_estado] Cobertura das 27 UFs (sigla ou nome por extenso) | 27 | 27 | ⚠️ ATENÇÃO |
| [frota_agrupada_por_estado] Cobertura dos anos 2023-2025 | [2023, 2024, 2025] | [2023, 2024, 2025] | ✅ OK |
| [frota_agrupada_por_estado] Chave ['uf', 'ano', 'tipo_veiculo', 'especie_veiculo', 'eixos'] sem duplicidade | 0 | 0 | ✅ OK |
| [frota_media_consolidada] Tabela carregada | > 0 linhas | 819274 | ✅ OK |
| [frota_media_consolidada] Linhas totalmente duplicadas | 0 | 0 | ✅ OK |
| [frota_media_consolidada] Total de valores nulos na tabela | 0 | 0 | ✅ OK |
| [frota_media_consolidada] 'qtd_veiculos' sem valores negativos | 0 | 0 | ✅ OK |
| [frota_media_consolidada] Cobertura das 27 UFs (sigla ou nome por extenso) | 27 | 27 | ⚠️ ATENÇÃO |
| [frota_media_consolidada] Cobertura dos anos 2023-2025 | [2023, 2024, 2025] | [2023, 2024, 2025] | ✅ OK |
| [frota_media_consolidada] Chave ['uf', 'ano', 'tipo_veiculo', 'especie_veiculo', 'eixos', 'municipio'] sem duplicidade | 0 | 0 | ✅ OK |
| Soma de qtd_veiculos por município (consolidada) bate com a agrupada por estado | 0 | 0 chave(s) só em uma tabela, 0 valor(es) divergente(s) | ✅ OK |

## Observações / divergências encontradas

- **Total de acidentes únicos (id.nunique) vs. total de linhas**: Cada acidente pode ter várias linhas (uma por pessoa/veículo/causa envolvida). Não confundir total de linhas com total de acidentes no dashboard.
- **Nulos em colunas obrigatórias (id, data, uf, br, municipio, tipo_acidente)**: {'br': 4628}
- **Categorias de 'tipo_acidente' consistentes entre os anos (sem divergência de grafia)**: ['sinistro pessoal de trânsito']
- **Categorias de 'causa_acidente' consistentes entre os anos (sem divergência de grafia)**: ['ingestão de álcool e/ou substâncias psicoativas pelo pedestre', 'ingestão de álcool ou de substâncias psicoativas pelo pedestre', 'obras na pista', 'obstrução na via', 'obstrução via tentativa assalto', 'pista em desnível']
- **[frota_agrupada_por_estado] Cobertura das 27 UFs (sigla ou nome por extenso)**: faltando: []; valores não reconhecidos como UF: ['Não Identificado', 'Não se Aplica', 'Sem Informação']
- **[frota_media_consolidada] Cobertura das 27 UFs (sigla ou nome por extenso)**: faltando: []; valores não reconhecidos como UF: ['Não Identificado', 'Não se Aplica', 'Sem Informação']

## Conclusão
Foram encontradas divergências (marcadas com ⚠️ acima). Revisar as tabelas antes de considerar os dados validados.