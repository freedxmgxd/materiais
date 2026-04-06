import json
import math
import warnings
from typing import List, Dict, Optional, Tuple, Union
from .models import NuclideComponent
from .nuclear_data_manager import NuclearDataManager
from .constants import AVOGADRO

class Material:
    """
    Main material class for nuclear data processing and MCNP input generation.
    """
    # AVOGADRO removed, now imported from .constants

    def __init__(self, name: str, density: float = None):
        self.name = name
        self.density = density  # g/cm3
        self.molecular_weight = 0.0  # g/mol
        self.total_atom_density = 0.0  # atoms/b-cm
        self.nuclides: List[NuclideComponent] = []
        self._data_manager = NuclearDataManager()

    def expand_element_to_isotopes(self, symbol: str, weight_fraction: float):
        """Helper to expand an element and add its isotopes to the material."""
        element_data = self._data_manager.get_element(symbol)
        if not element_data:
            raise ValueError(f"Unknown element: {symbol}")

        avg_mass = sum(i.abundance * i.mass for i in element_data.isotopes)
        for iso in element_data.isotopes:
            iso_w_frac = weight_fraction * (iso.abundance * iso.mass / avg_mass)
            if iso_w_frac > 0:
                self.nuclides.append(NuclideComponent(
                    Z=element_data.Z,
                    A=iso.A,
                    element=symbol,
                    weight_frac=iso_w_frac
                ))

    @classmethod
    def from_weight_fractions(cls, name: str, density: float, 
                               elements: List[str], 
                               fractions: List[float]) -> 'Material':
        """Create material from element symbols and weight fractions."""
        if abs(sum(fractions) - 1.0) > 1e-6:
            raise ValueError(f"Weight fractions must sum to 1.0 (sum={sum(fractions)})")
            
        mat = cls(name, density)
        dm = mat._data_manager
        
        # 1. Expand elements to natural isotopes
        for sym, w_frac in zip(elements, fractions):
            element_data = dm.get_element(sym)
            if not element_data:
                raise ValueError(f"Unknown element: {sym}")
                
            for iso in element_data.isotopes:
                # Isotope weight fraction = element_weight_frac * isotope_abundance
                # Note: This is a simplification. To be precise, we'd need 
                # (abd * mass_iso) / sum(abd_i * mass_i)
                # But usually weight fractions are given for the element as found in nature.
                
                # Correct way for weight fraction distribution:
                # element_avg_mass = sum(abd_i * mass_i)
                # iso_w_frac = element_w_frac * (iso_abd * iso_mass / element_avg_mass)
                
                avg_mass = sum(i.abundance * i.mass for i in element_data.isotopes)
                iso_w_frac = w_frac * (iso.abundance * iso.mass / avg_mass)
                
                if iso_w_frac > 0:
                    mat.nuclides.append(NuclideComponent(
                        Z=element_data.Z,
                        A=iso.A,
                        element=sym,
                        weight_frac=iso_w_frac
                    ))
        
        mat.calculate_properties()
        return mat

    @classmethod
    def from_atom_fractions(cls, name: str, density: float,
                             elements: List[str],
                             fractions: List[float]) -> 'Material':
        """Create material from element symbols and atom fractions."""
        if abs(sum(fractions) - 1.0) > 1e-6:
            raise ValueError(f"Atom fractions must sum to 1.0 (sum={sum(fractions)})")
            
        mat = cls(name, density)
        dm = mat._data_manager
        
        for sym, a_frac in zip(elements, fractions):
            element_data = dm.get_element(sym)
            # Normalize by total abundance of isotopes available in data
            total_abd = sum(iso.abundance for iso in element_data.isotopes)
            for iso in element_data.isotopes:
                # Isotope atom fraction = element_atom_frac * (iso_abundance / total_abundance)
                iso_a_frac = a_frac * (iso.abundance / total_abd)
                if iso_a_frac > 0:
                    mat.nuclides.append(NuclideComponent(
                        Z=element_data.Z,
                        A=iso.A,
                        element=sym,
                        atom_frac=iso_a_frac
                    ))
        
        mat.calculate_properties(based_on_atom=True)
        return mat

    def calculate_properties(self, based_on_atom: bool = False):
        """Calculate MW, missing fractions, and atom densities."""
        if not self.nuclides:
            return

        dm = self._data_manager
        
        if based_on_atom:
            # MW = sum(atom_frac_i * mass_i)
            self.molecular_weight = sum(n.atom_frac * (dm.get_mass(n.Z, n.A) or 0) for n in self.nuclides)
            # Update weight fractions: w_i = (a_i * mass_i) / MW
            for n in self.nuclides:
                n.weight_frac = (n.atom_frac * (dm.get_mass(n.Z, n.A) or 0)) / (self.molecular_weight or 1)
        else:
            # 1/MW = sum(weight_frac_i / mass_i)
            inv_mw = sum(n.weight_frac / (dm.get_mass(n.Z, n.A) or 1) for n in self.nuclides)
            self.molecular_weight = 1.0 / inv_mw if inv_mw > 0 else 0
            # Update atom fractions: a_i = (w_i / mass_i) * MW
            for n in self.nuclides:
                n.atom_frac = (n.weight_frac / (dm.get_mass(n.Z, n.A) or 1)) * self.molecular_weight

        # Total Atom Density (atoms/b-cm) = (rho * Na) / MW
        if self.density:
            self.total_atom_density = (self.density * AVOGADRO) / (self.molecular_weight or 1)
            for n in self.nuclides:
                n.atom_density = n.atom_frac * self.total_atom_density

    def apply_substitution(self, from_zaid: int, to_zaid: Optional[int] = None):
        """
        Apply isotope substitution. If to_zaid is None, distribute fraction
        to other isotopes of the same element using natural abundances (collprob).
        """
        Z = from_zaid // 1000
        A_from = from_zaid % 1000

        # Find the nuclide to be replaced
        source_idx = next((i for i, n in enumerate(self.nuclides) if n.Z == Z and n.A == A_from), None)
        if source_idx is None:
            warnings.warn(
                f"Nuclide {Z}-{A_from} not found in material '{self.name}'. "
                f"Substitution skipped.",
                UserWarning,
                stacklevel=2
            )
            return  # Not present in material
            
        source_nuc = self.nuclides.pop(source_idx)
        fraction_to_move = source_nuc.atom_frac
        
        if to_zaid is not None:
            # Transfer all to specific target
            A_to = to_zaid % 1000
            target = next((n for n in self.nuclides if n.Z == Z and n.A == A_to), None)
            if target:
                target.atom_frac += fraction_to_move
            else:
                self.nuclides.append(NuclideComponent(
                    Z=Z, A=A_to, element=source_nuc.element, atom_frac=fraction_to_move
                ))
        else:
            # Distribute to remaining isotopes of the same element
            element_data = self._data_manager.get_element(source_nuc.element)
            remaining_isotopes = [iso for iso in element_data.isotopes if iso.A != A_from]
            total_rem_abd = sum(iso.abundance for iso in remaining_isotopes)
            
            if total_rem_abd <= 0:
                return  # No remaining isotopes to distribute to
            
            for iso in remaining_isotopes:
                iso_phi = fraction_to_move * (iso.abundance / total_rem_abd)
                if iso_phi > 0:
                    target = next((n for n in self.nuclides if n.Z == Z and n.A == iso.A), None)
                    if target:
                        target.atom_frac += iso_phi
                    else:
                        self.nuclides.append(NuclideComponent(
                            Z=Z, A=iso.A, element=source_nuc.element, atom_frac=iso_phi
                        ))
        
        # Recalculate properties based on new atom fractions
        self.calculate_properties(based_on_atom=True)

    def apply_substitution_element(self, element: str, from_A: int, to_A: Optional[int] = None):
        """Apply substitution for a specific isotope of an element."""
        Z = self._data_manager.get_z(element)
        to_zaid = Z * 1000 + to_A if to_A else None
        self.apply_substitution(Z * 1000 + from_A, to_zaid)

    def set_substitutions(self, substitutions: List[Tuple[int, Optional[int]]]):
        """
        Apply multiple substitutions at once.
        
        Args:
            substitutions: List of (from_zaid, to_zaid) tuples.
                         to_zaid can be None for collprob distribution.
        """
        for from_zaid, to_zaid in substitutions:
            self.apply_substitution(from_zaid, to_zaid)

    def to_mcnp(self, mat_id: int, library: str = "70c",
                mode: str = "atom") -> str:
        """
        Generate MCNP material card string.

        Args:
            mat_id: Material ID number (1-999)
            library: Cross-section library suffix (e.g., "70c")
            mode: "atom" for atom density (at/b-cm, default),
                  "weight" for weight fraction

        Returns:
            MCNP material card string
        """
        if mode not in ("atom", "weight"):
            raise ValueError(f"Invalid mode: {mode}. Use 'atom' or 'weight'.")

        lines = [
            f"c {self.name}",
            f"c Total atom density: {self.total_atom_density:.6e} atoms/b-cm",
            f"c Molecular weight: {self.molecular_weight:.4f} g/mol",
            f"c Density: {self.density:.6f} g/cm3",
            f"m{mat_id}"
        ]

        if mode == "atom":
            for nuc in sorted(self.nuclides, key=lambda x: x.Z * 1000 + x.A):
                zaid = f"{nuc.Z * 1000 + nuc.A}.{library}"
                lines.append(f"      {zaid} {nuc.atom_density:.6e}")
        else:
            for nuc in sorted(self.nuclides, key=lambda x: x.Z * 1000 + x.A):
                zaid = nuc.Z * 1000 + nuc.A
                lines.append(f"      {zaid} {library} -{nuc.weight_frac:.6f}")

        return "\n".join(lines)

    def to_mcnp_string(self, mat_id: int, library: str = "70c") -> str:
        """
        Generate MCNP material card string using weight fractions (legacy).
        Prefer to_mcnp(..., mode="atom") for atom density output.

        Args:
            mat_id: Material ID number (1-999)
            library: Cross-section library suffix (default: 70c)

        Returns:
            MCNP material card string
        """
        return self.to_mcnp(mat_id, library, mode="weight")

    def to_mcnp_atom_density(self, mat_id: int, library: str = "70c") -> str:
        """
        Generate MCNP material card using atom densities (at/b-cm).
        This is the recommended method for MCNP input.

        Args:
            mat_id: Material ID number (1-999)
            library: Cross-section library suffix (e.g., "70c")

        Returns:
            MCNP material card string with atom densities
        """
        return self.to_mcnp(mat_id, library, mode="atom")

    def add_impurities(self, impurities: Dict[str, float], unit: str = "ppm_w", 
                       balance_element: str = None, reference_element: str = None):
        """
        Add impurities to the material and adjust composition.
        
        Args:
            impurities: Dict mapping element symbols to values.
            unit: 'ppm_w' (ppm weight), 'ppm_a' (ppm atom), 
                  'ug/g_ref' (micrograms per gram of reference element),
                  'w_frac' (weight fraction), 'a_frac' (atom fraction).
            balance_element: Symbol of element to reduce to maintain balance.
            reference_element: Symbol of element for 'ug/g_ref' unit.
        """
        dm = self._data_manager
        
        # Ensure we have current properties
        if not self.nuclides:
            raise ValueError("Cannot add impurities to an empty material")
        self.calculate_properties()

        # Step 1: Normalize all inputs to target w_frac or a_frac
        if unit == "ug/g_ref":
            if not reference_element:
                raise ValueError("reference_element required for 'ug/g_ref' unit")
            ref_w = sum(n.weight_frac for n in self.nuclides if n.element == reference_element)
            target_impurities = {k: v * 1e-6 * ref_w for k, v in impurities.items()}
            is_atom = False
        elif unit == "ppm_w":
            target_impurities = {k: v * 1e-6 for k, v in impurities.items()}
            is_atom = False
        elif unit == "ppm_a":
            target_impurities = {k: v * 1e-6 for k, v in impurities.items()}
            is_atom = True
        elif unit == "w_frac":
            target_impurities = impurities
            is_atom = False
        elif unit == "a_frac":
            target_impurities = impurities
            is_atom = True
        else:
            raise ValueError(f"Unknown unit: {unit}")

        # Step 2: Accumulate elements and capture current isotopic distributions
        # We work with a flat element: fraction mapping
        elements_frac = {}
        iso_distributions = {} # symbol -> {A: ratio}
        
        for n in self.nuclides:
            if is_atom:
                elements_frac[n.element] = elements_frac.get(n.element, 0.0) + n.atom_frac
            else:
                elements_frac[n.element] = elements_frac.get(n.element, 0.0) + n.weight_frac
            
            if n.element not in iso_distributions:
                iso_distributions[n.element] = {}
            iso_distributions[n.element][n.A] = n.atom_frac if is_atom else n.weight_frac
            
        # Normalize distributions to ratios
        for sym in iso_distributions:
            total = sum(iso_distributions[sym].values())
            if total > 0:
                for a in iso_distributions[sym]:
                    iso_distributions[sym][a] /= total

        total_added = sum(target_impurities.values())
        
        # Step 3: Apply impurities
        for sym, val in target_impurities.items():
            elements_frac[sym] = elements_frac.get(sym, 0.0) + val
            
        # Step 4: Balance
        if balance_element:
            if balance_element not in elements_frac:
                raise ValueError(f"Balance element {balance_element} not found in material")
            elements_frac[balance_element] -= total_added
            if elements_frac[balance_element] < 0:
                raise ValueError(f"Impurity level too high: balance element {balance_element} would become negative")
        else:
            # Re-normalize automatically
            total = sum(elements_frac.values())
            if total > 0:
                elements_frac = {k: v / total for k, v in elements_frac.items()}

        # Step 5: Rebuild material
        new_nuclides = []
        for sym, frac in elements_frac.items():
            if frac <= 0:
                continue

            # Case A: Element already exists - Preserve its isotopic distribution
            if sym in iso_distributions:
                for a, ratio in iso_distributions[sym].items():
                    val = frac * ratio
                    if val > 0:
                        z = dm.get_z(sym)
                        new_nuclides.append(NuclideComponent(
                            Z=z, A=a, element=sym,
                            atom_frac=val if is_atom else 0.0,
                            weight_frac=0.0 if is_atom else val
                        ))
                continue

            # Case B: New element - Use natural abundances
            element_data = dm.get_element(sym)
            if not element_data:
                # Fallback if not in database
                z = dm.get_z(sym)
                if z:
                    new_nuclides.append(NuclideComponent(
                        Z=z, A=0, element=sym,
                        atom_frac=frac if is_atom else 0.0,
                        weight_frac=0.0 if is_atom else frac
                    ))
                continue

            if is_atom:
                total_abd = sum(iso.abundance for iso in element_data.isotopes)
                for iso in element_data.isotopes:
                    iso_a = frac * (iso.abundance / total_abd)
                    if iso_a > 0:
                        new_nuclides.append(NuclideComponent(
                            Z=element_data.Z, A=iso.A, element=sym,
                            atom_frac=iso_a, weight_frac=0.0
                        ))
            else:
                avg_mass = sum(i.abundance * i.mass for i in element_data.isotopes)
                for iso in element_data.isotopes:
                    iso_w = frac * (iso.abundance * iso.mass / avg_mass)
                    if iso_w > 0:
                        new_nuclides.append(NuclideComponent(
                            Z=element_data.Z, A=iso.A, element=sym,
                            atom_frac=0.0, weight_frac=iso_w
                        ))

        self.nuclides = new_nuclides
        # Recalculate: if is_atom=True, recompute weight_frac from atom_frac
        #              if is_atom=False, recompute atom_frac from weight_frac
        self.calculate_properties(based_on_atom=is_atom)

    def to_json(self, filepath: str = None) -> str:
        """
        Serialize material to JSON.
        
        Args:
            filepath: Optional path to save JSON file. If None, returns JSON string.
        
        Returns:
            JSON string if filepath is None, otherwise None.
        """
        data = {
            "name": self.name,
            "density": self.density,
            "molecular_weight": self.molecular_weight,
            "total_atom_density": self.total_atom_density,
            "nuclides": [
                {
                    "Z": n.Z,
                    "A": n.A,
                    "element": n.element,
                    "weight_frac": n.weight_frac,
                    "atom_frac": n.atom_frac,
                    "atom_density": n.atom_density
                }
                for n in self.nuclides
            ]
        }
        
        json_str = json.dumps(data, indent=2)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
            return None
        
        return json_str

    @classmethod
    def from_json(cls, filepath: str) -> 'Material':
        """
        Deserialize material from JSON file.
        
        Args:
            filepath: Path to JSON file.
        
        Returns:
            Material instance.
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        mat = cls(name=data["name"], density=data.get("density"))
        mat.molecular_weight = data.get("molecular_weight", 0.0)
        mat.total_atom_density = data.get("total_atom_density", 0.0)
        
        for n in data.get("nuclides", []):
            mat.nuclides.append(NuclideComponent(
                Z=n["Z"],
                A=n["A"],
                element=n["element"],
                weight_frac=n.get("weight_frac", 0.0),
                atom_frac=n.get("atom_frac", 0.0),
                atom_density=n.get("atom_density", 0.0)
            ))
        
        return mat

    def get_summary(self) -> str:
        """Get formatted summary table of material properties."""
        lines = [
            f"Material: {self.name}",
            f"Density (g/cm3) = {self.density:.6f}" if self.density else "Density: Not defined",
            f"Molecular weight (g/mole) = {self.molecular_weight:.4f}",
            f"Total atom density (atoms/b-cm) = {self.total_atom_density:.4e}",
            "",
            "Nuclide     | Weight Frac  | Atom Frac  | Atom Density",
            "-" * 60
        ]
        
        for n in sorted(self.nuclides, key=lambda x: x.Z * 1000 + x.A):
            lines.append(
                f"{n.element:2s}-{n.A:<3d}    | {n.weight_frac:.6f}    | {n.atom_frac:.6f}    | {n.atom_density:.4e}"
            )
        
        return "\n".join(lines)

    def __repr__(self):
        return self.get_summary()
