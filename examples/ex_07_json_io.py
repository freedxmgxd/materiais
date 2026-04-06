"""
Exemplo 7: Persistência JSON

Premissa:
    Materiais podem ser salvos em JSON e recarregados
    posteriormente, permitindo reutilizar composições entre
    sessões e compartilhar configurações.

Conceitos:
    - to_json(filepath) — salva material em arquivo JSON
    - Material.from_json(filepath) — carrega material de JSON
    - O JSON preserva todas as propriedades calculadas:
      density, molecular_weight, total_atom_density, e todos
      os nuclídeos com weight_frac, atom_frac, atom_density
"""

import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from materials.factory import MaterialFactory
from materials.material import Material

# ─────────────────────────────────────────────────────────────
# 1. Salvar material em JSON
# ─────────────────────────────────────────────────────────────

print("=" * 60)
print("Exemplo 7a: Salvar UO₂ em JSON")
print("=" * 60)

uo2 = MaterialFactory.create(
    "uo2",
    temperature=600,
    enrichment_w_percent=3.2,
    theoretical_density_frac=0.95,
    dishing_percent=1.0
)

# Salvar em arquivo temporário
tmpdir = tempfile.mkdtemp()
filepath = os.path.join(tmpdir, "uo2_3p2.json")
uo2.to_json(filepath)

print(f"Material salvo em: {filepath}")
print()

# Mostrar conteúdo do JSON
with open(filepath) as f:
    print(f.read())

# ─────────────────────────────────────────────────────────────
# 2. Carregar material de JSON
# ─────────────────────────────────────────────────────────────

print("=" * 60)
print("Exemplo 7b: Carregar UO₂ de JSON")
print("=" * 60)

uo2_loaded = Material.from_json(filepath)

print(f"Material carregado: {uo2_loaded.name}")
print(f"Densidade: {uo2_loaded.density:.4f} g/cm³")
print(f"Peso molecular: {uo2_loaded.molecular_weight:.4f} g/mol")
print(f"Nº nuclídeos: {len(uo2_loaded.nuclides)}")

# Verificar que os dados batem
orig_density = uo2.total_atom_density
load_density = uo2_loaded.total_atom_density
print(f"\nConferência de densidade atômica:")
print(f"  Original:  {orig_density:.6e}")
print(f"  Carregado: {load_density:.6e}")
print(f"  Diferença: {abs(orig_density - load_density):.2e}")

# Limpar
os.remove(filepath)
os.rmdir(tmpdir)
