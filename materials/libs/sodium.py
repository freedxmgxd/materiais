"""
Sodium Coolant Material Plugin

This plugin provides liquid sodium coolant material with temperature-dependent density.
"""
from materials.factory import MaterialFactory
from materials.material import Material
from materials.thermal import TemperatureDependentDensity


class NaDensity(TemperatureDependentDensity):
    """Liquid Sodium coolant density model."""
    def get_density(self, T: float) -> float:
        super().get_density(T)
        # Sodium melts at 371K, use liquid correlation above melting point
        # Na density correlation (liquid): 951.5 - 0.2235 * T (kg/m3) / 1000 = g/cm3
        if T < 371:
            raise ValueError(f"Sodium is solid below 371K, got {T}K")
        return (951.5 - 0.2235 * T) / 1000.0


@MaterialFactory.register("sodium")
def create_sodium(temperature: float = 800) -> Material:
    """
    Create liquid sodium coolant.
    """
    rho = NaDensity().get_density(temperature)
    mat = Material(f"Na_{temperature}K", rho)
    # Pure sodium - natural isotopes
    mat.expand_element_to_isotopes('Na', 1.0)
    mat.calculate_properties()
    return mat
