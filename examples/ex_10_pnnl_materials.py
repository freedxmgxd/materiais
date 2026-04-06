"""
Exemplo 10: Materiais PNNL — Banco de Dados com 372 Materiais

Premissa:
    O sistema inclui a base de dados do Pacific Northwest National
    Laboratory (PNNL), com 372 materiais pré-calculados prontos
    para uso. São materiais comuns em blindagem e detecção:
    tecidos biológicos, ligas, concreto, água, ar, etc.

Conceitos:
    - MaterialFactory.create("pnnl:006") — acesso por ID numérico
    - MaterialFactory.create("aluminum") — acesso por nome (busca
      automática nos arquivos JSON)
    - Os materiais PNNL já vêm com todas as propriedades calculadas
      (weight_frac, atom_frac, atom_density)
    - Podem ser modificados após carregamento (substituições,
      impurezas, etc.)
    - to_mcnp() funciona normalmente

Os 372 materiais estão em materials/pnnl/json/
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from materials.factory import MaterialFactory

# ─────────────────────────────────────────────────────────────
# 1. Acessar material PNNL por ID
# ─────────────────────────────────────────────────────────────
#
# ID formato: "pnnl:NNN" onde NNN é o número de 3 dígitos.
# Lista parcial de materiais disponíveis:
#   006  Aluminum
#   013  Aluminum Alloy 6061
#   026  Borated Polyethylene (5% B)
#   034  Concrete, Ordinary
#   035  Concrete, Barite
#   044  Lead
#   053  Polyethylene
#   063  Stainless Steel 304
#   070  Water, Light (H2O)
#   076  Zirconium

print("=" * 60)
print("Exemplo 10a: Materiais PNNL por ID")
print("=" * 60)

# Alumínio puro
al = MaterialFactory.create("pnnl:006")
print(f"PNNL 006: {al.name}  ρ = {al.density:.4f} g/cm³")
print(f"  N = {al.total_atom_density:.6e} at/b-cm")

# Concreto ordinário
conc = MaterialFactory.create("pnnl:034")
print(f"PNNL 034: {conc.name}  ρ = {conc.density:.4f} g/cm³")
print(f"  Nº nuclídeos: {len(conc.nuclides)}")

# ─────────────────────────────────────────────────────────────
# 2. Acessar material PNNL por nome
# ─────────────────────────────────────────────────────────────
#
# A busca é case-insensitive e busca parcial no nome do arquivo.

print("\n" + "=" * 60)
print("Exemplo 10b: Materiais PNNL por ID explícito")
print("=" * 60)

# Busca por nome é ambígua (ex: "water" pode bater em vários arquivos).
# O mais seguro é usar o ID direto. Alguns materiais úteis:
#   pnnl:006 — Aluminum
#   pnnl:034 — Boral
#   pnnl:044 — Lead
#   pnnl:053 — Polyethylene
#   pnnl:354 — Water, Liquid (H2O)

water = MaterialFactory.create("pnnl:354")  # Water, Liquid
print(f"PNNL 354: {water.name}  ρ = {water.density:.4f} g/cm³")

poly = MaterialFactory.create("pnnl:053")  # Polyethylene
print(f"PNNL 053: {poly.name}  ρ = {poly.density:.4f} g/cm³")

# Chumbo via plugin (requer T >= 600 K)
pb = MaterialFactory.create("lead", temperature=700)
print(f"Plugin:  {pb.name}  ρ = {pb.density:.4f} g/cm³")

# ─────────────────────────────────────────────────────────────
# 3. Listar todos os materiais disponíveis
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("Exemplo 10c: Plugins registrados no sistema")
print("=" * 60)

all_materials = MaterialFactory.list_materials()
print(f"Materiais via plugin: {len(all_materials)}")
print(f"  {all_materials}")
print()
print("Materiais PNNL: 372 materiais em materials/pnnl/json/")
print("  Acesse via MaterialFactory.create('pnnl:NNN')")
print("  Ex: 'pnnl:006' (Al), 'pnnl:034' (Boral), 'pnnl:070' (H2O)")

# ─────────────────────────────────────────────────────────────
# 4. Gerar carta MCNP de material PNNL
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("Exemplo 10d: Carta MCNP de concreto ordinário")
print("=" * 60)

conc = MaterialFactory.create("pnnl:034")
print(conc.to_mcnp(mat_id=10, library="70c", mode="atom"))

# ─────────────────────────────────────────────────────────────
# 5. Modificar material PNNL
# ─────────────────────────────────────────────────────────────
#
# Materiais PNNL podem ser modificados como qualquer outro.
# Exemplo: adicionar 100 ppm de Boro natural ao concreto
# para simular concreto baritado.

print("\n" + "=" * 60)
print("Exemplo 10e: Adicionar boro à água PNNL")
print("=" * 60)

water_b = MaterialFactory.create("pnnl:354")  # Water, Liquid
water_b.name = "Water_Borated"
water_b.add_impurities({"B": 1000}, unit="ppm_w", balance_element="H")

print(f"Água original:   {len(water.nuclides)} nuclídeos")
print(f"Água borada:     {len(water_b.nuclides)} nuclídeos")
b_total = sum(n.atom_density for n in water_b.nuclides if n.element == "B")
print(f"  Boro adicionado: {b_total:.6e} at/b-cm")
