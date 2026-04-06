"""
Beryllium Oxide (BeO) Material Plugin

This plugin provides Beryllium Oxide material with temperature-dependent density.
"""
from materials.factory import MaterialFactory
from materials.material import Material
from materials.thermal import TemperatureDependentDensity


class BeODensity(TemperatureDependentDensity):
    """Beryllium Oxide density model."""
    def get_density(self, T: float) -> float:
        super().get_density(T)
        # BeO linear expansion correlation: alpha = 5.133 + 4.65e-3*T - ...
        # Simplified version for now
        rho0 = 3.01
        return rho0 / (1 + 9e-6 * (T - 300))**3


@MaterialFactory.register("beo")
def create_beo(temperature: float = 300) -> Material:
    """
    Create Beryllium Oxide.
    """
    rho = BeODensity().get_density(temperature)
    return Material.from_atom_fractions(f"BeO_{temperature}K", rho, ['Be', 'O'], [0.5, 0.5])
