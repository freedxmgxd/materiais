"""
Lead-Bismuth Eutectic (LBE) Coolant Material Plugin

This plugin provides LBE coolant material with temperature-dependent density.
"""
from materials.factory import MaterialFactory
from materials.material import Material
from materials.thermal import TemperatureDependentDensity


class LBEDensity(TemperatureDependentDensity):
    """Lead-Bismuth Eutectic (LBE) coolant density model."""
    def get_density(self, T: float) -> float:
        super().get_density(T)
        # LBE density: approximately 11070 - 1.17 * T (kg/m3) / 1000 = g/cm3
        if T < 400:
            raise ValueError(f"LBE is solid below ~400K, got {T}K")
        return (11070 - 1.17 * T) / 1000.0


@MaterialFactory.register("lbe")
def create_lbe(temperature: float = 700) -> Material:
    """
    Create Lead-Bismuth Eutectic (LBE) coolant.
    """
    rho = LBEDensity().get_density(temperature)
    # LBE typical composition: 44.5% Pb, 55.5% Bi (by weight)
    elements = ['Pb', 'Bi']
    fractions = [0.445, 0.555]
    return Material.from_weight_fractions(f"LBE_{temperature}K", rho, elements, fractions)
