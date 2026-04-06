# Tutorial — Sistema de Materiais Nucleares

Este tutorial ensina a usar todas as funcionalidades do sistema de materiais nucleares, desde a criação básica de materiais até geração de cards MCNP, substituições isotópicas, impurezas, banco PNNL e persistência JSON.

---

## Estrutura do Projeto

```
materiais/
├── materials/
│   ├── material.py          ← Classe principal Material
│   ├── factory.py           ← MaterialFactory com plugins
│   ├── models.py            ← NuclideComponent
│   ├── nuclear_data_manager.py  ← Dados nucleares (ENDL)
│   ├── constants.py         ← Constantes (Avogadro, etc.)
│   ├── thermal.py           ← Base para densidade térmica
│   ├── libs/                ← Plugins de materiais
│   │   ├── uo2.py           ← Combustível UO₂
│   │   ├── sodium.py        ← Refrigerante sódio
│   │   ├── ss316.py         ← Aço inoxidável SS316
│   │   ├── lead.py          ← Chumbo líquido
│   │   ├── helium.py        ← Hélio gasoso
│   │   ├── lbe.py           ← Liga Pb-Bi eutética
│   │   ├── zircaloy4.py     ← Zircaloy-4
│   │   └── beo.py           ← Óxido de berílio
│   └── pnnl/json/           ← 372 materiais PNNL
├── nuclear_data/            ← Dados nucleares (massas, abundâncias)
├── examples/                ← Tutoriais práticos
├── refs/                    ← Referências e memoriais
└── plans/                   ← Planejamento
```

---

## Conceitos Fundamentais

### O que é um Material?

Um `Material` representa um material nuclear com:
- **Nuclídeos**: Lista de isótopos com frações de peso, frações atômicas e densidades atômicas
- **Propriedades macroscópicas**: peso molecular, densidade atômica total, densidade (g/cm³)

### Como os isótopos são tratados

Quando você cria um material com elementos (ex: `Fe`, `U`), o sistema automaticamente os expande em seus isótopos naturais usando dados da biblioteca ENDL. Por exemplo, `Fe` natural vira Fe-54, Fe-56, Fe-57, Fe-58 com suas abundâncias naturais.

### Fluxo típico de trabalho

1. **Criar** o material (via Factory ou manualmente)
2. **Modificar** (substituições isotópicas, impurezas)
3. **Exportar** (MCNP, JSON, sumário)

---

## Exemplos Práticos

| # | Arquivo | Descrição |
|---|---------|-----------|
| 01 | `ex_01_basic_materials.py` | Criar materiais do zero (weight fractions, atom fractions, expand individual) |
| 02 | `ex_02_uo2_fuel.py` | UO₂ com enriquecimento, TD, dishing e temperatura |
| 03 | `ex_03_reactor_materials.py` | Aço SS316 e sódio líquido |
| 04 | `ex_04_isotope_substitution.py` | Substituição isotópica (C-13→C-12, distribuição, warnings) |
| 05 | `ex_05_impurities.py` | Impurezas (µg/g U, ppm_w, balance element) |
| 06 | `ex_06_mcnp_output.py` | cards MCNP (atom density e weight fraction, múltiplos materiais) |
| 07 | `ex_07_json_io.py` | Salvar e carregar materiais em JSON |
| 08 | `ex_08_tabn_verification.py` | Verificação contra memorial tabn.md (3 enriquecimentos) |
| 09 | `ex_09_custom_zircaloy.py` | Zircaloy-4 manual e equivalência de métodos |
| 10 | `ex_10_pnnl_materials.py` | 372 materiais PNNL, acesso por ID, modificação |

---

## Referências Rápidas

### Unidades
- **Densidade**: g/cm³
- **Densidade atômica**: átomos/barn·cm (at/b-cm)
- **Frações**: adimensionais (0 a 1)
- **Temperatura**: Kelvin

### Formato ZAID
O identificador de nuclídeo segue o padrão MCNP: `ZAID = Z × 1000 + A`
- U-235 → `92235` (Z=92, A=235)
- O-16 → `8016` (Z=8, A=16)

### Bibliotecas de seção de choque
Sufixos usados no MCNP: `70c` (ENDF/B-VII), `80c` (ENDF/B-VIII), etc.

### Plugins disponíveis
```python
from materials.factory import MaterialFactory
MaterialFactory.list_materials()
# ['uo2', 'ss316', 'zircaloy4', 'beo', 'sodium', 'lead', 'lbe', 'helium']
```

### Materiais PNNL (372 materiais)
```python
# Acesso por ID:
mat = MaterialFactory.create("pnnl:006")   # Aluminum
mat = MaterialFactory.create("pnnl:354")   # Water, Liquid
mat = MaterialFactory.create("pnnl:044")   # Lead
mat = MaterialFactory.create("pnnl:053")   # Polyethylene
```

---

## API Principal

### Criar materiais

```python
# Via Factory (plugins)
uo2 = MaterialFactory.create("uo2", temperature=600,
    enrichment_w_percent=3.2,
    theoretical_density_frac=0.95,
    dishing_percent=1.0)

# Manual — frações de peso
brass = Material.from_weight_fractions(
    name="Brass", density=8.53,
    elements=["Cu", "Zn"],
    fractions=[0.70, 0.30])

# Manual — frações atômicas
steam = Material.from_atom_fractions(
    name="Steam", density=0.0009,
    elements=["H", "O"],
    fractions=[2.0/3.0, 1.0/3.0])

# PNNL
al = MaterialFactory.create("pnnl:006")
```

### Modificar

```python
# Substituir isótopo
mat.apply_substitution_element("C", from_A=13, to_A=12)
mat.apply_substitution(6013, 6012)  # via ZAID
mat.apply_substitution(6013, None)  # distribuir entre demais

# Adicionar impurezas
mat.add_impurities({"Al": 250, "Fe": 250}, unit="ug/g_ref",
    reference_element="U")
mat.add_impurities({"B": 1000}, unit="ppm_w", balance_element="H")
```

### Exportar

```python
# MCNP — densidade atômica (recomendado)
print(mat.to_mcnp(mat_id=1, library="70c", mode="atom"))

# MCNP — frações de peso (legado)
print(mat.to_mcnp(mat_id=1, library="70c", mode="weight"))

# JSON
mat.to_json("material.json")
mat2 = Material.from_json("material.json")

# Sumário
print(mat.get_summary())
```
