"""
Exemplo 1: Criando Materiais Básicos do Zero

Premissa:
    Demonstrar as duas formas fundamentais de criar um material
    manualmente: por frações de peso (weight fractions) e por
    frações atômicas (atom fractions).

Conceitos:
    - Material.from_weight_fractions() — o mais comum, usado quando
      a composição é dada em % em peso (ex: ligas metálicas).
    - Material.from_atom_fractions() — usado quando a composição é
      dada em átomos (ex: gases, misturas moleculares).
    - expand_element_to_isotopes() — expande um elemento em seus
      isótopos naturais individualmente.
    - calculate_properties() — calcula peso molecular, frações
      atômicas e densidades atômicas.
    - get_summary() — imprime tabela resumo.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from materials.material import Material

# ─────────────────────────────────────────────────────────────
# 1. Material por frações de peso (liga metálica)
# ─────────────────────────────────────────────────────────────
#
# Composição do latão (simplificada):
#   Cu: 70% em peso
#   Zn: 30% em peso
# Densidade: 8,53 g/cm³
#
# O sistema expande automaticamente Cu e Zn em seus isótopos
# naturais usando dados da biblioteca ENDL.

print("=" * 60)
print("Exemplo 1a: Latão por frações de peso")
print("=" * 60)

brass = Material.from_weight_fractions(
    name="Brass_70Cu_30Zn",
    density=8.53,
    elements=["Cu", "Zn"],
    fractions=[0.70, 0.30]
)

print(brass.get_summary())

# ─────────────────────────────────────────────────────────────
# 2. Material por frações atômicas (gás)
# ─────────────────────────────────────────────────────────────
#
# Mistura gasosa (exemplo didático):
#   H: 2/3 dos átomos
#   O: 1/3 dos átomos
# Densidade: 0,0009 g/cm³ (vapor de água a alta temperatura)

print("\n" + "=" * 60)
print("Exemplo 1b: Vapor d'água por frações atômicas")
print("=" * 60)

steam = Material.from_atom_fractions(
    name="Steam_H2O",
    density=0.0009,
    elements=["H", "O"],
    fractions=[2.0/3.0, 1.0/3.0]
)

print(steam.get_summary())

# ─────────────────────────────────────────────────────────────
# 3. Expandir elemento individualmente
# ─────────────────────────────────────────────────────────────
#
# Uso: quando você precisa adicionar um elemento a um material
# existente sem recriá-lo do zero.
#
# Exemplo: material de alumínio puro construído passo a passo.

print("\n" + "=" * 60)
print("Exemplo 1c: Alumínio construído passo a passo")
print("=" * 60)

al = Material("Pure_Al", density=2.70)
al.expand_element_to_isotopes("Al", 1.0)  # 100% em peso de Al
al.calculate_properties()

print(al.get_summary())
