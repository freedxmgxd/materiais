"""
Exemplo 5: Adicionando Impurezas

Premissa:
    Pastilhas de UO₂ reais contêm impurezas metálicas e não-
    metálicas especificadas por normas (ex: ESP/MA-83.02).
    Estas impurezas afetam levemente a criticalidade e devem
    ser incluídas em simulações de alta precisão.

Conceitos:
    - add_impurities(impurities, unit, balance_element, reference_element)
    - Unidades suportadas:
        "ppm_w"       — partes por milhão em peso (fração mássica × 1e6)
        "ppm_a"       — partes por milhão em átomos
        "ug/g_ref"    — microgramas por grama de elemento de referência
        "w_frac"      — fração de peso direta
        "a_frac"      — fração atômica direta
    - reference_element: usado em "ug/g_ref" para calcular a fração
      relativa a esse elemento (ex: µg/g U)
    - balance_element: elemento cuja fração é reduzida para compensar
      a adição de impurezas

Caso real — Pastilha UO₂ (impurezas 1.md):
    - ρ = 10,292 g/cm³
    - ε = 4,25% U-235
    - Impurezas em µg/g U (relativo ao Urânio, NÃO à pastilha)
    - O cálculo correto usa m_imp = m_U × C_i × 1e-6
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from materials.factory import MaterialFactory

# ─────────────────────────────────────────────────────────────
# 1. Impurezas especificadas em µg/g U (caso do memorial)
# ─────────────────────────────────────────────────────────────
#
# Tabela de impurezas máxima (ESP/MA-83.02):
#   Al:250  Cl:15  F:10  N:30  C:100  Gd:3  Ca:100
#   Fe:250  Ni:100  Si:100  Zn:200

print("=" * 60)
print("Exemplo 5a: UO₂ com impurezas da norma ESP/MA-83.02")
print("=" * 60)

# Criar UO₂ base com ε = 4,25%
uo2 = MaterialFactory.create(
    "uo2",
    temperature=300,
    enrichment_w_percent=4.25,
    theoretical_density_frac=1.0,
    dishing_percent=0.0
)

# Ajustar densidade para o valor do memorial
uo2.density = 10.292
uo2.calculate_properties(based_on_atom=False)

print(f"UO₂ base: ρ = {uo2.density:.4f} g/cm³")
print(f"Nº nuclídeos antes: {len(uo2.nuclides)}")

impurities = {
    "Al": 250, "Cl": 15, "F": 10, "N": 30, "C": 100,
    "Gd": 3, "Ca": 100, "Fe": 250, "Ni": 100, "Si": 100, "Zn": 200
}

uo2.add_impurities(impurities, unit="ug/g_ref", reference_element="U")

print(f"Nº nuclídeos depois: {len(uo2.nuclides)}")
print()

print(f"{'Nuclídeo':<12} {'at/b-cm':>16}")
print("-" * 30)
for n in sorted(uo2.nuclides, key=lambda x: x.atom_density, reverse=True):
    print(f"  {n.element}-{n.A:<3d}     {n.atom_density:>14.6e}")

# ─────────────────────────────────────────────────────────────
# 2. Impurezas simples em ppm_w
# ─────────────────────────────────────────────────────────────
#
# Caso mais simples: adicionar Boro como impureza em ppm peso.

print("\n" + "=" * 60)
print("Exemplo 5b: Impureza de Boro em ppm peso")
print("=" * 60)

uo2_simple = MaterialFactory.create(
    "uo2",
    temperature=600,
    enrichment_w_percent=3.2,
    theoretical_density_frac=0.95,
    dishing_percent=1.0
)

print(f"Antes: ρ = {uo2_simple.density:.4f}, MW = {uo2_simple.molecular_weight:.4f}")

# Adicionar 10 ppm de Boro natural (por peso)
uo2_simple.add_impurities({"B": 10}, unit="ppm_w", balance_element="U")

print(f"Depois: ρ = {uo2_simple.density:.4f}, MW = {uo2_simple.molecular_weight:.4f}")

# Verificar B na composição
b_total = sum(n.atom_density for n in uo2_simple.nuclides if n.element == "B")
print(f"  Boro total: {b_total:.6e} at/b-cm")
