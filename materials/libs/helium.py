"""
Helium Gas Coolant Material Plugin

This plugin provides helium gas coolant material with temperature and pressure dependent density.
"""
from materials.factory import MaterialFactory
from materials.material import Material
from materials.thermal import TemperatureDependentDensity


class HeDensity(TemperatureDependentDensity):
    """Helium gas density model (ideal gas approximation)."""
    def __init__(self, pressure: float = 8.0):
        """Initialize with pressure in MPa."""
        if pressure <= 0:
            raise ValueError("Pressure must be positive.")
        self.pressure = pressure  # MPa

    def get_density(self, T: float) -> float:
        super().get_density(T)
        # Ideal gas: PV = nRT
        if T <= 0:
            raise ValueError("Temperature must be positive.")
        return 4.0 * self.pressure / (8.314 * T)


@MaterialFactory.register("helium")
def create_helium(temperature: float = 600, pressure: float = 8.0) -> Material:
    """
    Create helium gas coolant.
    """
    rho = HeDensity(pressure).get_density(temperature)
    mat = Material(f"He_{temperature}K_{pressure}MPa", rho)
    # Pure helium
    mat.expand_element_to_isotopes('He', 1.0)
    mat.calculate_properties()
    return mat
