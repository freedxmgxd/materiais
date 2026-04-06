"""
Exemplo 9: Material Personalizado — Zircaloy-4 Manual

Premissa:
    Nem todo material está disponível como plugin. Quando preciso
    criar um material com composição específica que não existe
    na biblioteca de plugins, usa-se a construção manual.

    Zircaloy-4 é a liga de zircônio usada como revestimento de
    combustível em reatores PWR/BWR.

Composição Zircaloy-4 (frações de peso):
    Zr: ~98,23%
    Sn: 1,2–1,7%  → usaremos 1,45%
    Fe: 0,18–0,24% → usaremos 0,21%
    Cr: 0,07–0,13% → usaremos 0,10%

Densidade: ~6,56 g/cm³ a 300 K

Conceitos:
    - Construção manual com Material() + expand_element_to_isotopes()
    - Ou via from_weight_fractions() (mais simples)
    - Comparação entre os dois métodos
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from materials.material import Material

# ─────────────────────────────────────────────────────────────
# 1. Via from_weight_fractions (recomendado)
# ─────────────────────────────────────────────────────────────

print("=" * 60)
print("Exemplo 9a: Zircaloy-4 via from_weight_fractions")
print("=" * 60)

# Composição Zircaloy-4 (frações de peso):
#   Zr: ~98,23%
#   Sn: 1,2–1,7%  → usaremos 1,45%
#   Fe: 0,18–0,24% → usaremos 0,21%
#   Cr: 0,07–0,13% → usaremos 0,10%
#   Ajuste: Zr = 1 - (0.0145 + 0.0021 + 0.0010) = 0.9824

zry4 = Material.from_weight_fractions(
    name="Zircaloy-4",
    density=6.56,
    elements=["Zr", "Sn", "Fe", "Cr"],
    fractions=[0.9824, 0.0145, 0.0021, 0.0010]  # soma = 1.0 exato
)

print(zry4.get_summary())

# ─────────────────────────────────────────────────────────────
# 2. Construção manual passo a passo
# ─────────────────────────────────────────────────────────────
#
# Mesmo resultado, mas construindo elemento por elemento.
# Útil quando se precisa de controle fino sobre cada adição.

print("\n" + "=" * 60)
print("Exemplo 9b: Zircaloy-4 construção manual")
print("=" * 60)

zry4_manual = Material("Zircaloy-4_manual", density=6.56)

# Adicionar cada elemento com sua fração de peso
for elem, w_frac in [("Zr", 0.9824), ("Sn", 0.0145), ("Fe", 0.0021), ("Cr", 0.0010)]:
    zry4_manual.expand_element_to_isotopes(elem, w_frac)

zry4_manual.calculate_properties()

print(zry4_manual.get_summary())

# ─────────────────────────────────────────────────────────────
# 3. Verificar que os dois métodos dão o mesmo resultado
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("Exemplo 9c: Comparação entre os métodos")
print("=" * 60)

diff_density = abs(zry4.density - zry4_manual.density)
diff_mw = abs(zry4.molecular_weight - zry4_manual.molecular_weight)
diff_ad = abs(zry4.total_atom_density - zry4_manual.total_atom_density)

print(f"  Densidade:       Δ = {diff_density:.2e} g/cm³")
print(f"  Peso molecular:  Δ = {diff_mw:.2e} g/mol")
print(f"  Dens. atômica:   Δ = {diff_ad:.2e} at/b-cm")

if diff_density < 1e-10 and diff_mw < 1e-6 and diff_ad < 1e-10:
    print("\n  ✓ Métodos equivalentes")
else:
    print("\n  ⚠ Métodos divergentes")
