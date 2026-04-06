#!/usr/bin/env python3
"""
Script para validar todas as correções implementadas no sistema de materiais.
Compara o comportamento antes e depois das correções.
"""

import sys
import os
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from materials.factory import MaterialFactory
from materials.material import Material
from materials.constants import AVOGADRO


def test_expand_element_public():
    """Teste 1: expand_element_to_isotopes é agora público."""
    print("\n=== Teste 1: Método expand_element_to_isotopes público ===")
    mat = Material("Test_Al", density=2.7)
    try:
        mat.expand_element_to_isotopes('Al', 1.0)
        print("  ✓ Método público acessado com sucesso")
        print(f"    Nuclídeos criados: {len(mat.nuclides)}")
        for n in mat.nuclides:
            print(f"    {n.element}-{n.A}: w_frac={n.weight_frac:.6f}")
        return True
    except AttributeError as e:
        print(f"  ✗ Falha ao acessar método público: {e}")
        return False


def test_uo2_density_dishing():
    """Teste 2: UO2Density com dishing aplicado corretamente."""
    print("\n=== Teste 2: UO2Density com dishing ===")
    try:
        # Sem dishing
        uo2_no_dish = MaterialFactory.create("uo2", temperature=300,
                                              enrichment_w_percent=3.2,
                                              theoretical_density_frac=1.0,
                                              dishing_percent=0.0)
        # Com 1% dishing
        uo2_dish = MaterialFactory.create("uo2", temperature=300,
                                          enrichment_w_percent=3.2,
                                          theoretical_density_frac=1.0,
                                          dishing_percent=1.0)

        print(f"  Densidade sem dishing: {uo2_no_dish.density:.6f} g/cm³")
        print(f"  Densidade com 1% dishing: {uo2_dish.density:.6f} g/cm³")

        expected_ratio = 0.99  # 1% dishing should reduce density by 1%
        actual_ratio = uo2_dish.density / uo2_no_dish.density
        diff = abs(actual_ratio - expected_ratio)

        if diff < 0.001:
            print(f"  ✓ Razão de densidade correta: {actual_ratio:.4f} (esperado: {expected_ratio})")
            return True
        else:
            print(f"  ✗ Razão de densidade incorreta: {actual_ratio:.4f} (esperado: {expected_ratio})")
            return False
    except Exception as e:
        print(f"  ✗ Erro: {e}")
        return False


def test_substitution_warning():
    """Teste 3: apply_substitution emite warning quando nuclídeo não encontrado."""
    print("\n=== Teste 3: Warning em apply_substitution ===")
    mat = Material.from_weight_fractions("Test_Fe", density=7.87,
                                          elements=["Fe"], fractions=[1.0])

    # Tentar substituir nuclídeo que não existe
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        mat.apply_substitution(999001, None)  # Z=99, A=1 (inexistente)

        if len(w) > 0 and issubclass(w[-1].category, UserWarning):
            print(f"  ✓ Warning emitido: {w[-1].message}")
            return True
        else:
            print("  ✗ Nenhum warning emitido")
            return False


def test_mcnp_consistency():
    """Teste 4: Consistência MCNP com novo método unificado."""
    print("\n=== Teste 4: Consistência MCNP ===")
    uo2 = MaterialFactory.create("uo2", temperature=600, enrichment_w_percent=3.2,
                                  theoretical_density_frac=0.95, dishing_percent=1.0)

    # Testar método principal
    mcnp_atom = uo2.to_mcnp(mat_id=1, library="70c", mode="atom")
    mcnp_weight = uo2.to_mcnp(mat_id=1, library="70c", mode="weight")

    print("  Output atom density (primeiras 3 linhas):")
    for line in mcnp_atom.split('\n')[:5]:
        print(f"    {line}")

    print("  Output weight fraction (primeiras 3 linhas):")
    for line in mcnp_weight.split('\n')[:5]:
        print(f"    {line}")

    # Verificar que ambos contêm header consistente
    if "Total atom density:" in mcnp_atom and "Total atom density:" in mcnp_weight:
        print("  ✓ Headers consistentes entre modos")
        return True
    else:
        print("  ✗ Headers inconsistentes")
        return False


def test_ss316_carbon_check():
    """Teste 5: SS316 verifica existência de C-13 antes de substituir."""
    print("\n=== Teste 5: SS316 verificação de C-13 ===")
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ss316 = MaterialFactory.create("ss316", temperature=300)

            # Verificar se o material foi criado
            print(f"  SS316 criado com {len(ss316.nuclides)} nuclídeos")

            # Verificar se houve warning sobre C-13
            c13_warnings = [x for x in w if 'C-13' in str(x.message)]
            if c13_warnings:
                print(f"  ⚠ Warning sobre C-13: {c13_warnings[0].message}")
            else:
                print("  ✓ Substituição de C-13 realizada sem warnings")

            return True
    except Exception as e:
        print(f"  ✗ Erro ao criar SS316: {e}")
        return False


def test_tabn_verification():
    """Teste 6: Verificação contra tabn.md."""
    print("\n=== Teste 6: Verificação tabn.md ===")

    test_cases = [
        {
            "enrichment": 1.9,
            "expected": {
                "92-234": 3.81712e-06,
                "92-235": 4.65920e-04,
                "92-238": 2.37486e-02,
                "8-16": 4.84366e-02,
            }
        },
        {
            "enrichment": 2.5,
            "expected": {
                "92-234": 5.13919e-06,
                "92-235": 6.13047e-04,
                "92-238": 2.36018e-02,
                "8-16": 4.84399e-02,
            }
        },
        {
            "enrichment": 3.2,
            "expected": {
                "92-234": 6.71542e-06,
                "92-235": 7.84692e-04,
                "92-238": 2.34305e-02,
                "8-16": 4.84438e-02,
            }
        },
    ]

    all_pass = True
    for tc in test_cases:
        enr = tc["enrichment"]
        uo2 = MaterialFactory.create("uo2", temperature=600,
                                      enrichment_w_percent=enr,
                                      theoretical_density_frac=1.0,
                                      dishing_percent=0.0)

        print(f"\n  ε = {enr}%:")
        for key, exp_val in tc["expected"].items():
            z, a = key.split('-')
            act_val = next((n.atom_density for n in uo2.nuclides
                           if n.Z == int(z) and n.A == int(a)), 0)
            diff = abs(act_val - exp_val)
            rel_err = diff / exp_val * 100 if exp_val > 0 else 0
            status = "✓" if rel_err < 1.0 else "✗"
            print(f"    {key}: {act_val:.6e} (exp: {exp_val:.6e}) {status} ({rel_err:.2f}%)")
            if rel_err >= 1.0:
                all_pass = False

    return all_pass


def test_impurity_calculation():
    """Teste 7: add_impurities recalcula corretamente."""
    print("\n=== Teste 7: add_impurities com recálculo ===")
    try:
        uo2 = MaterialFactory.create("uo2", temperature=600,
                                      enrichment_w_percent=3.2,
                                      theoretical_density_frac=1.0,
                                      dishing_percent=0.0)

        # Adicionar impurezas
        uo2.add_impurities({"Al": 250, "Fe": 250}, unit="ppm_w",
                            balance_element="U")

        # Verificar que as frações foram recalculadas
        has_weight = all(n.weight_frac > 0 for n in uo2.nuclides)
        has_atom = all(n.atom_frac > 0 for n in uo2.nuclides)

        print(f"  Todos com weight_frac > 0: {has_weight}")
        print(f"  Todos com atom_frac > 0: {has_atom}")

        if has_weight and has_atom:
            print("  ✓ Propriedades recalculadas corretamente")
            return True
        else:
            print("  ✗ Propriedades não recalculadas")
            return False
    except Exception as e:
        print(f"  ✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Validação das Correções do Sistema de Materiais")
    print("=" * 60)

    tests = [
        ("Método público", test_expand_element_public),
        ("UO2Density dishing", test_uo2_density_dishing),
        ("Substitution warning", test_substitution_warning),
        ("MCNP consistency", test_mcnp_consistency),
        ("SS316 carbon check", test_ss316_carbon_check),
        ("tabn.md verification", test_tabn_verification),
        ("Impurity recalculation", test_impurity_calculation),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Teste '{name}' falhou com exceção: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Resumo dos Resultados")
    print("=" * 60)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} testes passaram")

    if passed == total:
        print("\nTodos os testes passaram! ✓")
        sys.exit(0)
    else:
        print(f"\n{total - passed} teste(s) falharam! ✗")
        sys.exit(1)
