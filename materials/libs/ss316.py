"""
SS316 Stainless Steel Material Plugin

This plugin provides SS316 stainless steel material with temperature-dependent density.
"""
import warnings
from materials.factory import MaterialFactory
from materials.material import Material
from materials.thermal import TemperatureDependentDensity


class SS316Density(TemperatureDependentDensity):
    """Stainless Steel 316 density model."""
    def get_density(self, T: float) -> float:
        super().get_density(T)
        # Legacy: (8084 - 0.4209*T - 3.894E-5*T*T) / 1000
        return (8084 - 0.4209 * T - 3.894e-5 * T * T) / 1000.0


@MaterialFactory.register("ss316")
def create_ss316(temperature: float = 300) -> Material:
    """
    Create SS316 based on standard weight fractions.
    """
    rho = SS316Density().get_density(temperature)
    elements = ['Fe', 'Cr', 'Ni', 'Mo', 'Mn', 'Si', 'C']
    fractions = [0.655, 0.170, 0.120, 0.025, 0.020, 0.010, 0.0003] # Simplified sum adjustment
    # Adjust sum to exactly 1.0 for Fe
    rem = 1.0 - sum(fractions[1:])
    fractions[0] = rem

    mat = Material.from_weight_fractions(f"SS316_{temperature}K", rho, elements, fractions)

    # Apply typical substitutions for SS316 XS
    # Verify carbon exists before attempting substitution
    carbon_zaid = 6013  # C-13
    carbon_exists = any(n.Z == 6 and n.A == 13 for n in mat.nuclides)
    if carbon_exists:
        mat.apply_substitution(carbon_zaid, 6012)
    else:
        warnings.warn(
            f"C-13 not found in SS316 material. Carbon substitution skipped.",
            UserWarning,
            stacklevel=2
        )

    return mat
