"""
Exemplo 6: Gerando cards MCNP

Premissa:
    O formato MCNP suporta duas representações de composição:
    1. Frações de peso (weight fractions) — legado
    2. Densidade atômica (at/b-cm) — recomendado

    O método unificado to_mcnp() permite escolher o modo.

Conceitos:
    - to_mcnp(mat_id, library, mode="atom|weight")
      mode="atom"   (padrão): ZAID.library  atom_density
      mode="weight":         ZAID  library  -weight_frac
    - to_mcnp_atom_density(mat_id, library) — atalho para mode="atom"
    - to_mcnp_string(mat_id, library)       — atalho para mode="weight" (legado)
    - library: sufixo da seção de choque ("70c", "80c", etc.)

Formato MCNP — atom density (recomendado):
    m1
          8016.70c  4.588000e-02
          92234.70c 8.648000e-06
          ...

Formato MCNP — weight fraction (legado):
    m1
          8016 70c -0.118432
          92234 70c -0.000155
          ...
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from materials.factory import MaterialFactory

# ─────────────────────────────────────────────────────────────
# 1. Card MCNP com densidade atômica (recomendado)
# ─────────────────────────────────────────────────────────────

print("=" * 60)
print("Exemplo 6a: MCNP — densidade atômica (recomendado)")
print("=" * 60)

uo2 = MaterialFactory.create(
    "uo2",
    temperature=600,
    enrichment_w_percent=3.2,
    theoretical_density_frac=0.95,
    dishing_percent=1.0
)

print(uo2.to_mcnp(mat_id=1, library="70c", mode="atom"))

# ─────────────────────────────────────────────────────────────
# 2. Card MCNP com frações de peso (legado)
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("Exemplo 6b: MCNP — frações de peso (legado)")
print("=" * 60)

print(uo2.to_mcnp(mat_id=1, library="70c", mode="weight"))

# ─────────────────────────────────────────────────────────────
# 3. Múltiplos materiais com diferentes bibliotecas
# ─────────────────────────────────────────────────────────────
#
# Simulação multi-material com bibliotecas diferentes.

print("\n" + "=" * 60)
print("Exemplo 6c: Múltiplos materiais")
print("=" * 60)

ss316 = MaterialFactory.create("ss316", temperature=600)
na = MaterialFactory.create("sodium", temperature=800)

materials = [
    (uo2, 1, "80c"),    # UO₂ com ENDF/B-VIII
    (ss316, 2, "70c"),  # SS316 com ENDF/B-VII
    (na, 3, "70c"),     # Na com ENDF/B-VII
]

for mat, mat_id, lib in materials:
    print(mat.to_mcnp(mat_id, library=lib, mode="atom"))
    print()
