# Exemplos — Sistema de Materiais Nucleares

## Tutoriais (ex_01 a ex_10)

Exemplos documentados com premissa, explicação e resultado.

| # | Arquivo | Descrição |
|---|---------|-----------|
| 01 | `ex_01_basic_materials.py` | Criar materiais do zero (weight fractions, atom fractions, expand individual) |
| 02 | `ex_02_uo2_fuel.py` | UO₂ com enriquecimento, TD, dishing e temperatura |
| 03 | `ex_03_reactor_materials.py` | Aço SS316 e sódio líquido |
| 04 | `ex_04_isotope_substitution.py` | Substituição isotópica (C-13→C-12, distribuição, warnings) |
| 05 | `ex_05_impurities.py` | Impurezas (µg/g U, ppm_w, balance element) |
| 06 | `ex_06_mcnp_output.py` | Cartas MCNP (atom density e weight fraction, múltiplos materiais) |
| 07 | `ex_07_json_io.py` | Salvar e carregar materiais em JSON |
| 08 | `ex_08_tabn_verification.py` | Verificação contra memorial tabn.md (3 enriquecimentos) |
| 09 | `ex_09_custom_zircaloy.py` | Zircaloy-4 manual e equivalência de métodos |
| 10 | `ex_10_pnnl_materials.py` | 372 materiais PNNL, acesso por ID, modificação |

## Validação Interna

Scripts de verificação usados no desenvolvimento e correção do sistema.

| Arquivo | Descrição |
|---------|-----------|
| `09_corrections_validation.py` | Valida todas as 7 correções de código implementadas |
| `10_impurity_verification.py` | Verifica impurezas contra memorial corrigido (impurezas 1.md) |

## Saídas

A pasta `output/` contém cartas MCNP geradas pelos exemplos.
