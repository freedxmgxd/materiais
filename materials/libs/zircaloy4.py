"""
Zircaloy-4 Material Plugin

This plugin provides Zircaloy-4 cladding material with temperature-dependent density.
"""
from materials.factory import MaterialFactory
from materials.material import Material
from materials.thermal import TemperatureDependentDensity


class Zircaloy4Density(TemperatureDependentDensity):
    """Zircaloy-4 density model with thermal expansion."""
    def get_density(self, T: float) -> float:
        super().get_density(T)
        # Linear expansion approximation: 6.56 at 300K
        rho0 = 6.56
        alpha = 6.7e-6 # linear expansion coeff
        return rho0 / (1 + alpha * (T - 300))**3


@MaterialFactory.register("zircaloy4")
def create_zircaloy4(temperature: float = 300) -> Material:
    """
    Create Zircaloy-4.
    """
    rho = Zircaloy4Density().get_density(temperature)
    elements = ['Zr', 'Sn', 'Fe', 'Cr']
    fractions = [0.9811, 0.0150, 0.0021, 0.0018]
    return Material.from_weight_fractions(f"Zry4_{temperature}K", rho, elements, fractions)
