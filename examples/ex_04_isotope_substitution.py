"""
Exemplo 4: Substituição Isotópica

Premissa:
    Em simulações de criticalidade e blindagem, às vezes é
    necessário alterar a composição isotópica natural de um
    elemento. Exemplos comuns:
    - Enriquecimento de urânio (aumentar U-235)
    - Empobrecimento de boro (remover B-10)
    - Substituir C-13 por C-12 (aço para seções de choque)

Conceitos:
    - apply_substitution_element(el, from_A, to_A):
      move toda a fração do isótopo from_A para to_A
    - apply_substitution(from_zaid, to_zaid):
      versão de baixo nível com ZAIDs
    - apply_substitution(from_zaid, None):
      distribui a fração entre os demais isótopos do mesmo
      elemento proporcionalmente às abundâncias naturais
      (usado em cálculos de colisão probabilística)
    - Warning é emitido se o nuclídeo de origem não existir

Formato ZAID:
    ZAID = Z × 1000 + A
    Ex: C-13 → 6013, C-12 → 6012
"""

import sys, os, warnings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from materials.material import Material

# ─────────────────────────────────────────────────────────────
# 1. Substituir C-13 → C-12 em carbono puro
# ─────────────────────────────────────────────────────────────

print("=" * 60)
print("Exemplo 4a: Substituir C-13 → C-12")
print("=" * 60)

# Carbono puro natural
carbon = Material.from_weight_fractions(
    name="Carbon_natural",
    density=2.26,
    elements=["C"],
    fractions=[1.0]
)

print("\nAntes (C natural):")
for n in carbon.nuclides:
    print(f"  {n.element}-{n.A:<3d}  w_frac={n.weight_frac:.6f}  atom_frac={n.atom_frac:.6f}")

# Substituir: mover C-13 para C-12
carbon.apply_substitution_element("C", from_A=13, to_A=12)

print("\nDepois (C-13 → C-12):")
for n in carbon.nuclides:
    print(f"  {n.element}-{n.A:<3d}  w_frac={n.weight_frac:.6f}  atom_frac={n.atom_frac:.6f}")

# ─────────────────────────────────────────────────────────────
# 2. Distribuir fração de um isótopo entre os demais
# ─────────────────────────────────────────────────────────────
#
# apply_substitution(zaid, None) distribui a fração do nuclídeo
# removido entre os isótopos restantes do mesmo elemento.

print("\n" + "=" * 60)
print("Exemplo 4b: Distribuir Fe-54 entre demais isótopos")
print("=" * 60)

fe = Material.from_weight_fractions(
    name="Fe_pure",
    density=7.87,
    elements=["Fe"],
    fractions=[1.0]
)

print("\nAntes:")
for n in fe.nuclides:
    print(f"  {n.element}-{n.A:<3d}  atom_frac={n.atom_frac:.6f}")

# Remover Fe-54 e distribuir entre Fe-56, Fe-57, Fe-58
fe.apply_substitution(26054, None)

print("\nDepois (Fe-54 distribuído):")
for n in fe.nuclides:
    print(f"  {n.element}-{n.A:<3d}  atom_frac={n.atom_frac:.6f}")

# ─────────────────────────────────────────────────────────────
# 3. Warning quando nuclídeo não existe
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("Exemplo 4c: Warning ao tentar substituir nuclídeo ausente")
print("=" * 60)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    fe.apply_substitution(999001, None)  # Z=99 não existe no material

    if w:
        print(f"  ⚠ Warning capturado:")
        print(f"    {w[0].message}")
