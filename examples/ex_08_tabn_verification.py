"""
Exemplo 8: Verificação contra Memorial de Cálculo (tabn.md)

Premissa:
    Os cálculos analíticos do textbook (tabn.md, seção 4.2.1)
    fornecem valores exatos de densidade atômica para UO₂ com
    três enriquecimentos. Este exemplo verifica se o código
    reproduz esses valores.

Fórmulas do tabn.md:
    η = 0,007731 × ε^1,0837  (% U-234)
    M_U = 1 / (η/M_234 + ε/M_235 + (1-η-ε)/M_238)
    M_UO2 = M_U + 2 × M_O
    ρ_U = ρ × M_U / M_UO2
    N_i = w_i × ρ_U × N_A / M_i

Valores esperados (T=600 K, TD=100%, dishing=0%):
    ε=1,9%:  N_234=3,817e-6  N_235=4,659e-4  N_238=2,375e-2
    ε=2,5%:  N_234=5,139e-6  N_235=6,130e-4  N_238=2,360e-2
    ε=3,2%:  N_234=6,715e-6  N_235=7,847e-4  N_238=2,343e-2
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from materials.factory import MaterialFactory

test_cases = [
    {
        "enrichment": 1.9,
        "expected": {
            "92-234": 3.81712e-06,
            "92-235": 4.65920e-04,
            "92-238": 2.37486e-02,
            "8-16":   4.84366e-02,
        }
    },
    {
        "enrichment": 2.5,
        "expected": {
            "92-234": 5.13919e-06,
            "92-235": 6.13047e-04,
            "92-238": 2.36018e-02,
            "8-16":   4.84399e-02,
        }
    },
    {
        "enrichment": 3.2,
        "expected": {
            "92-234": 6.71542e-06,
            "92-235": 7.84692e-04,
            "92-238": 2.34305e-02,
            "8-16":   4.84438e-02,
        }
    },
]

print("=" * 60)
print("Verificação UO₂ contra tabn.md")
print("=" * 60)

all_pass = True
for tc in test_cases:
    enr = tc["enrichment"]
    uo2 = MaterialFactory.create(
        "uo2",
        temperature=600,
        enrichment_w_percent=enr,
        theoretical_density_frac=1.0,
        dishing_percent=0.0
    )

    print(f"\n  ε = {enr}% (ρ = {uo2.density:.4f} g/cm³)")
    print(f"  {'Nuclídeo':<12} {'Código':>14} {'tabn.md':>14} {'Erro%':>8}")
    print(f"  {'-' * 52}")

    for key, exp in sorted(tc["expected"].items()):
        z, a = key.split("-")
        act = next((n.atom_density for n in uo2.nuclides
                     if n.Z == int(z) and n.A == int(a)), 0.0)
        err = abs(act - exp) / exp * 100 if exp > 0 else 0
        status = "✓" if err < 1.0 else "✗"
        print(f"  {key:<12} {act:>14.6e} {exp:>14.6e} {err:>7.2f}% {status}")
        if err >= 1.0:
            all_pass = False

print("\n" + "=" * 60)
if all_pass:
    print("✓ Todos os casos passaram (erro < 1%)")
else:
    print("✗ Alguns casos falharam")
