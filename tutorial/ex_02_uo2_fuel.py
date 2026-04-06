"""
Exemplo 2: Combustível UO₂ com Enriquecimento e Temperatura

Premissa:
    Criar combustível nuclear de dióxido de urânio (UO₂) com
    enriquecimento específico de U-235, densidade teórica e
    dishing (rebaixamento na pastilha), considerando a temperatura
    de operação que afeta a densidade por expansão térmica.

Conceitos:
    - MaterialFactory.create("uo2", ...) — criação via plugin
    - enrichment_w_percent — enriquecimento de U-235 em % peso
    - theoretical_density_frac — fração da densidade teórica
      (0,95 = 95% TD, típico de pastilha sinterizada)
    - dishing_percent — redução de densidade por rebaixamento
      na face da pastilha (~1%)
    - temperature — afeta a densidade via expansão térmica do UO₂
    - Fórmula U-234: η = 0,007731 × ε^1,0837 (regulatório)

Física:
    A densidade do UO₂ varia com temperatura conforme correlação
    experimental. A fórmula do plugin usa dois regimes:
      273–923 K:  0,99734 + 9,802e-6·T - 2,705e-10·T² + 4,291e-13·T³
      923–3120 K: 0,99672 + 1,179e-5·T - 2,429e-9·T² + 1,219e-12·T³
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from materials.factory import MaterialFactory

# ─────────────────────────────────────────────────────────────
# 1. UO₂ típico de reator PWR
# ─────────────────────────────────────────────────────────────
#
# Parâmetros:
#   Enriquecimento: 3,2% U-235
#   TD: 95% da teórica
#   Dishing: 1%
#   Temperatura: 600 K (operação)

print("=" * 60)
print("Exemplo 2a: UO₂ para reator PWR (3,2% enriquecimento)")
print("=" * 60)

uo2_pwr = MaterialFactory.create(
    "uo2",
    temperature=600,
    enrichment_w_percent=3.2,
    theoretical_density_frac=0.95,
    dishing_percent=1.0
)

print(uo2_pwr.get_summary())

# ─────────────────────────────────────────────────────────────
# 2. Comparar diferentes enriquecimentos
# ─────────────────────────────────────────────────────────────
#
# O enriquecimento de U-234 é calculado automaticamente:
#   η = 0,007731 × ε^1,0837
#
# Para ε = 1,9%: η ≈ 0,0155%
# Para ε = 2,5%: η ≈ 0,0209%
# Para ε = 3,2%: η ≈ 0,0273%

print("\n" + "=" * 60)
print("Exemplo 2b: Comparação de enriquecimentos")
print("=" * 60)

print(f"{'Enrichment':>12} {'U-234 (at/b-cm)':>18} {'U-235 (at/b-cm)':>18} {'U-238 (at/b-cm)':>18}")
print("-" * 70)

for enr in [1.9, 2.5, 3.2]:
    uo2 = MaterialFactory.create(
        "uo2",
        temperature=600,
        enrichment_w_percent=enr,
        theoretical_density_frac=1.0,
        dishing_percent=0.0
    )
    u234 = next(n.atom_density for n in uo2.nuclides if n.A == 234)
    u235 = next(n.atom_density for n in uo2.nuclides if n.A == 235)
    u238 = next(n.atom_density for n in uo2.nuclides if n.A == 238)
    print(f"  {enr:>5.1f}%     {u234:>18.6e} {u235:>18.6e} {u238:>18.6e}")

# ─────────────────────────────────────────────────────────────
# 3. Efeito da temperatura na densidade
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("Exemplo 2c: Efeito da temperatura na densidade")
print("=" * 60)

for T in [300, 600, 900, 1200]:
    uo2 = MaterialFactory.create(
        "uo2",
        temperature=T,
        enrichment_w_percent=3.2,
        theoretical_density_frac=1.0,
        dishing_percent=0.0
    )
    print(f"  T = {T:>4d} K  →  ρ = {uo2.density:.4f} g/cm³")
