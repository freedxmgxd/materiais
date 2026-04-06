#!/usr/bin/env python3
"""
Verificação do cálculo de impurezas contra o memorial de cálculo (impurezas 1.md).

O memorial usa:
  - Densidade da pastilha: 10,292 g/cm³
  - Enriquecimento: U-235 = 4,25%, U-234 = 0,03709%, U-238 = 95,71291%
  - Impurezas em µg/g U (relativo ao Urânio, NÃO à pastilha)
  - Cálculo: f_U = 1 / (1 + 2*M_O/M_U + ΣC_imp)
  - f_O = f_U × (2*M_O/M_U)
  - m_imp = ρ × f_U × C_imp(µg/g) × 1e-6
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from materials.factory import MaterialFactory
from materials.material import Material
from materials.constants import AVOGADRO

# Dados do memorial
RHO_PASTILHA = 10.292  # g/cm³
ENRICHMENT = 4.25  # % U-235
U234_FRAC = 0.0003709  # fração mássica no U
U235_FRAC = 0.0425
U238_FRAC = 0.9571291

M_U234 = 234.04095
M_U235 = 235.04393
M_U238 = 238.05079
M_O = 15.99940

# Impurezas do memorial (µg/g U)
IMPURITIES_UG_PER_G_U = {
    "Al": 250,
    "Cl": 15,
    "F": 10,
    "N": 30,
    "C": 100,
    "Gd": 3,
    "Ca": 100,
    "Fe": 250,
    "Ni": 100,
    "Si": 100,
    "Zn": 200,
}

# Valores esperados corrigidos (at/barn·cm)
# Aplicada correção do memorial (impurezas 1.md revisado 2026-04-05)
EXPECTED_ATOM_DENSITIES = {
    "O": 4.58800e-02,
    "U-238": 2.19500e-02,
    "U-235": 9.86900e-04,
    "C": 4.54400e-05,    # corrigido: era 5.355e-5
    "Al": 5.05700e-05,   # corrigido: era 5.059e-5
    "Fe": 2.44300e-05,
    "Si": 1.94300e-05,   # corrigido: era 2.163e-5
    "Zn": 1.66900e-05,   # corrigido: era 1.855e-5
    "Ca": 1.36200e-05,   # corrigido: era 1.516e-5
    "N": 1.16900e-05,    # corrigido: era 1.300e-5
    "Ni": 9.29800e-06,   # corrigido: era 1.029e-5
    "U-234": 8.64800e-06,
    "F": 2.87200e-06,    # corrigido: era 3.183e-6
    "Cl": 2.30900e-06,   # corrigido: era 2.560e-6
    "Gd": 1.04100e-07,   # corrigido: era 1.155e-07
}


def verify_impurities():
    """Verifica se o cálculo de impurezas está correto."""
    print("=" * 60)
    print("Verificação de Impurezas (impurezas 1.md)")
    print("=" * 60)

    # Criar UO2 base com enriquecimento 4,25%
    # Usar TD_frac e dishing para obter densidade ~10,292 g/cm³
    uo2 = MaterialFactory.create(
        "uo2",
        temperature=300,
        enrichment_w_percent=ENRICHMENT,
        theoretical_density_frac=1.0,
        dishing_percent=0.0,
    )

    # Ajustar densidade para o valor do memorial
    # O UO2 factory calcula a densidade termicamente; vamos sobrescrever
    # para comparar com o memorial que usa 10,292 g/cm³ fixo
    uo2.density = RHO_PASTILHA
    uo2.calculate_properties(based_on_atom=False)

    print(f"\nUO2 base (ε={ENRICHMENT}%):")
    print(f"  Densidade: {uo2.density:.4f} g/cm³")
    print(f"  Peso molecular U: {uo2.molecular_weight - 2 * M_O:.4f} g/mol")
    print(f"  Peso molecular UO2: {uo2.molecular_weight:.4f} g/mol")

    # Adicionar impurezas
    # O memorial usa unit="ug/g_ref" com reference_element="U"
    uo2.add_impurities(
        IMPURITIES_UG_PER_G_U,
        unit="ug/g_ref",
        reference_element="U",
        balance_element=None,
    )

    print(f"\nApós adicionar impurezas:")
    print(f"  Densidade: {uo2.density:.4f} g/cm³")
    print(f"  Peso molecular: {uo2.molecular_weight:.4f} g/mol")
    print(f"  Densidade atômica total: {uo2.total_atom_density:.6e} at/b-cm")

    print("\n" + "-" * 60)
    print("Comparação de Densidades Atômicas (at/b-cm)")
    print("-" * 60)
    print(f"  {'Nuclídeo':<12} {'Código':>14} {'Memorial':>14} {'Erro %':>10}")
    print("-" * 60)

    all_pass = True
    for key, expected in sorted(EXPECTED_ATOM_DENSITIES.items()):
        # Buscar no material
        if "-" in key:
            elem, mass = key.split("-")
            mass = int(mass)
            actual = next(
                (n.atom_density for n in uo2.nuclides if n.element == elem and n.A == mass),
                0.0,
            )
        else:
            elem = key
            actual = sum(n.atom_density for n in uo2.nuclides if n.element == elem)

        err = abs(actual - expected) / expected * 100 if expected > 0 else float("inf")
        status = "✓" if err < 1.0 else "✗"
        print(f"  {key:<12} {actual:>14.6e} {expected:>14.6e} {err:>9.2f}% {status}")

        if err >= 1.0:
            all_pass = False

    print("-" * 60)
    return all_pass


if __name__ == "__main__":
    result = verify_impurities()
    print()
    if result:
        print("✓ Todas as impurezas conferem com o memorial (< 1% erro)")
        sys.exit(0)
    else:
        print("✗ Algumas impurezas NÃO conferem com o memorial")
        sys.exit(1)
