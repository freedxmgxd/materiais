"""
Exemplo 3: Aço SS316 e Refrigerante Sódio

Premissa:
    Criar dois materiais essenciais para reatores de sódio:
    - SS316: aço inoxidável estrutural do vaso e tubos
    - Na: refrigerante de sódio líquido

Conceitos:
    - SS316 contém Fe, Cr, Ni, Mo, Mn, Si, C expandidos
      naturalmente + substituição C-13→C-12 (para cross-section)
    - Sódio líquido só existe acima de 371 K (ponto de fusão)
    - Densidade do Na: correlação linear ρ = (951,5 - 0,2235·T)/1000
    - Densidade do SS316: correlação quadrática com T

Atenção:
    O SS316 aplica automaticamente a substituição C-13→C-12.
    Se o C-13 não existir no material, um warning é emitido
    e a substituição é ignorada.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from materials.factory import MaterialFactory

# ─────────────────────────────────────────────────────────────
# 1. SS316 a 600 K
# ─────────────────────────────────────────────────────────────

print("=" * 60)
print("Exemplo 3a: Aço inoxidável SS316 a 600 K")
print("=" * 60)

ss316 = MaterialFactory.create("ss316", temperature=600)

print(ss316.get_summary())

# ─────────────────────────────────────────────────────────────
# 2. Sódio líquido a 800 K
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("Exemplo 3b: Sódio líquido a 800 K")
print("=" * 60)

na = MaterialFactory.create("sodium", temperature=800)

print(na.get_summary())

# ─────────────────────────────────────────────────────────────
# 3. Efeito da temperatura no sódio
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("Exemplo 3c: Densidade do Na vs temperatura")
print("=" * 60)

for T in [400, 500, 600, 700, 800, 900, 1000]:
    try:
        na = MaterialFactory.create("sodium", temperature=T)
        print(f"  T = {T:>4d} K  →  ρ = {na.density:.4f} g/cm³")
    except ValueError as e:
        print(f"  T = {T:>4d} K  →  ERRO: {e}")
