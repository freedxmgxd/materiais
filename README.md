# Sistema de Materiais Nucleares

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Dependencies: None](https://img.shields.io/badge/dependencies-none-brightgreen.svg)]()

Um framework modular e de alta fidelidade para o gerenciamento de **composições de materiais nucleares** e geração automatizada de **cards MCNP**. 

Projetado para pesquisadores e engenheiros que precisam de controle preciso sobre enriquecimentos, frações isotópicas, impurezas e dependência térmica sem depender de bibliotecas externas pesadas.

---

## 🚀 Principais Funcionalidades

- **Zero Dependências Externas**: Funciona apenas com a biblioteca padrão do Python (stdlib).
- **Isotopic Expansion Automática**: Converte elementos naturais em seus isótopos (dados da biblioteca ENDL).
- **Substituição Isotópica Flexível**: Mapeamento de isótopos para compatibilidade com seções de choque (ex: O-18 → O-16).
- **Base de Dados PNNL**: Acesso imediato a **372 materiais** da norma PNNL-15870.
- **Dependência Térmica**: Modelos integrados de densidade para combustíveis (UO₂) e refrigerantes (Sódio, Chumbo, LBE).
- **MCNP ready**: Exportação direta para formatos `atom_density` (at/b-cm) e `weight_fraction`.
- **Validação Física**: Verificado contra memoriais de cálculo (`tabn.md`) com erro inferior a 0,01%.

---

## 🛠️ Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/materiais.git
cd materiais

# Instale em modo desenvolvedor (opcional, para usar como pacote)
pip install -e .
```

---

## 📖 Uso Rápido

### 1. Combustível UO₂ com Enriquecimento
```python
from materials.factory import MaterialFactory

# UO2 enriquecido a 3.2%, 600K, com 95% da densidade teórica e 1% de dishing
uo2 = MaterialFactory.create(
    "uo2",
    temperature=600,
    enrichment_w_percent=3.2,
    theoretical_density_frac=0.95,
    dishing_percent=1.0
)

# Gerar card MCNP (Material 1, biblioteca 70c)
print(uo2.to_mcnp(mat_id=1, library="70c"))
```

### 2. Materiais Industriais (PNNL)
```python
# Acessando Boral (ID 034) ou Água (ID 354)
boral = MaterialFactory.create("pnnl:034")
water = MaterialFactory.create("pnnl:354")

print(f"Boral Density: {boral.density:.4f} g/cm3")
```

### 3. Substituições e Impurezas
```python
# Remover C-13 e distribuir sua massa entre os demais isótopos de Carbono
mat.apply_substitution_element("C", from_A=13, to_A=None)

# Adicionar impurezas em µg por grama de Urânio
mat.add_impurities({"Gd": 2, "B": 1.5}, unit="ug/g_ref", reference_element="U")
```

---

## 📁 Estrutura do Projeto

```text
materiais/
├── materials/               # Pacote principal
│   ├── material.py          # Classe base Material (Lógica de conversão)
│   ├── factory.py           # Factory e sistema de plugins
│   ├── libs/                # Plugins específicos (UO2, SS316, Sodium...)
│   ├── pnnl/                # Base de dados compositional PNNL
│   └── nuclear_data_manager.py # Carregamento de dados ENDL
├── nuclear_data/            # JSONs de massas atômicas e abundâncias
├── examples/                # Scripts didáticos (ex_01 a ex_10)
├── tutorial/                # Guia detalhado passo-a-passo
├── refs/                    # Memoriais de cálculo e validação
├── LICENSE                  # Licença MIT
└── pyproject.toml           # Configuração do pacote Python
```

---

## ✅ Verificação e Qualidade

O sistema foi submetido a testes rigorosos de convergência física:
- **UO₂ Enrichment**: Paridade com o memorial `refs/tabn.md` (Textbook standard).
- **Impurezas**: Verificação contra norma ESP/MA-83.02 em `refs/impurezas 1.md`.
- **Estabilidade**: Zero dependências, garantindo reprodutibilidade em qualquer ambiente Python 3.9+.

---

## 📜 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

---

**Desenvolvido por Pedro CR Rossi**
