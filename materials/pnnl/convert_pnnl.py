import os
import json
import sys

# Add root to sys.path to allow importing materials
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from materials.material import Material
from materials.models import NuclideComponent

def convert_pnnl():
    data_path = os.path.join(root_dir, 'materials', 'pnnl', 'data')
    output_dir = os.path.join(root_dir, 'materials', 'pnnl', 'json')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    with open(data_path, 'r') as f:
        # Use a more robust split that handles potential trailing whitespace or different line endings
        content = f.read()
        blocks = content.split('\n-')

    count = 0
    mat_index = 0
    
    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            continue
            
        ptr = 0
        # Check if first line is a numeric ID
        if lines[ptr].isdigit():
            actual_id = int(lines[ptr])
            ptr += 1
            mat_index = actual_id
        else:
            mat_index += 1
            actual_id = mat_index
            
        if ptr >= len(lines): continue
        name = lines[ptr]
        ptr += 1
        
        if ptr >= len(lines): continue
        symbol = lines[ptr]
        ptr += 1
        
        if ptr >= len(lines): continue
        try:
            density = float(lines[ptr])
        except ValueError:
            print(f"Error parsing density for {name} at line {lines[ptr]}")
            continue
        ptr += 1
        
        elements = []
        fractions = []
        while ptr < len(lines):
            parts = lines[ptr].split()
            if len(parts) >= 2:
                # Handle cases like "AL 0.003747" (uppercase)
                sym = parts[0].capitalize()
                # Correct some common misspellings or variations if needed
                # For now, just Capitalize (e.g., Al -> Al, H -> H, O -> O)
                if sym == 'Al': sym = 'Al'
                
                try:
                    frac = float(parts[1])
                    elements.append(sym)
                    fractions.append(frac)
                except ValueError:
                    print(f"Error parsing fraction for element {parts[0]} in {name}")
            ptr += 1
            
        if not elements:
            continue

        # Normalization for floating point precision issues in source file
        total_frac = sum(fractions)
        if abs(total_frac - 1.0) < 1e-3:
            fractions = [f / total_frac for f in fractions]
        
        try:
            # Create Material object manually and add nuclides
            mat = Material(name=name, density=density)
            dm = mat._data_manager
            mat.nuclides = []
            
            for sym, a_frac in zip(elements, fractions):
                if '-' in sym:
                    # Isotope specified (e.g., U-235, Li-6, H-2)
                    base_sym, a_str = sym.split('-')
                    z = dm.get_z(base_sym)
                    if not z:
                        print(f"Unknown element in isotope: {sym} for {name}")
                        continue
                    try:
                        a_num = int(a_str)
                    except ValueError:
                        print(f"Invalid isotope mass number: {sym} for {name}")
                        continue
                    mat.nuclides.append(NuclideComponent(Z=z, A=a_num, element=base_sym, atom_frac=a_frac))
                    continue
                
                # Element expansion
                element_data = dm.get_element(sym)
                if not element_data:
                    # Fallback to pure element if possible
                    z = dm.get_z(sym)
                    if z:
                        # Assuming the most likely isotope if missing from abundances
                        # Just to keep it moving. For ZAID, we usually need Z000 or a specific A.
                        # But Material uses Z and A.
                        mat.nuclides.append(NuclideComponent(Z=z, A=0, element=sym, atom_frac=a_frac))
                    else:
                        print(f"Unknown element: {sym} for {name}")
                    continue
                
                total_abd = sum(iso.abundance for iso in element_data.isotopes)
                if total_abd > 0:
                    for iso in element_data.isotopes:
                        iso_a_frac = a_frac * (iso.abundance / total_abd)
                        if iso_a_frac > 0:
                            mat.nuclides.append(NuclideComponent(Z=element_data.Z, A=iso.A, element=sym, atom_frac=iso_a_frac))
                else:
                    # No natural abundance, use the first isotope in the database
                    if element_data.isotopes:
                        iso = element_data.isotopes[0]
                        mat.nuclides.append(NuclideComponent(Z=element_data.Z, A=iso.A, element=sym, atom_frac=a_frac))
                    else:
                        mat.nuclides.append(NuclideComponent(Z=element_data.Z, A=0, element=sym, atom_frac=a_frac))

            # Recalculate properties based on atom fractions we manually populated
            mat.calculate_properties(based_on_atom=True)
            
            # Slugify name for filename
            clean_name = "".join([c if c.isalnum() else "_" for c in name]).strip("_")
            filename = f"{actual_id:03d}_{clean_name}.json"
            filepath = os.path.join(output_dir, filename)
            
            mat.to_json(filepath)
            count += 1
        except Exception as e:
            print(f"Failed to process material {name}: {e}")

    print(f"Successfully converted {count} materials to JSON.")

if __name__ == "__main__":
    convert_pnnl()
