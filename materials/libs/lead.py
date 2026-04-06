"""
Lead Coolant Material Plugin

This plugin provides liquid lead coolant material with temperature-dependent density.
"""
from materials.factory import MaterialFactory
from materials.material import Material
from materials.thermal import TemperatureDependentDensity


class PbDensity(TemperatureDependentDensity):
    """Lead coolant density model."""
    def get_density(self, T: float) -> float:
        super().get_density(T)
        # Lead density correlation: 11342 - 1.194 * T (kg/m3) / 1000 = g/cm3
        # Valid above melting point 600K
        if T < 600:
            raise ValueError(f"Lead is solid below 600K, got {T}K")
        return (11342 - 1.194 * T) / 1000.0


@MaterialFactory.register("lead")
def create_lead(temperature: float = 700) -> Material:
    """
    Create liquid lead coolant.
    """
    rho = PbDensity().get_density(temperature)
    mat = Material(f"Pb_{temperature}K", rho)
    # Pure lead - natural isotopes
    mat.expand_element_to_isotopes('Pb', 1.0)
    mat.calculate_properties()
    return mat
