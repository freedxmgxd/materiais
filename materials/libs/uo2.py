"""
UO2 Nuclear Fuel Material Plugin

This plugin provides UO2 fuel material with temperature-dependent density
and proper isotopic composition based on enrichment.
"""
from materials.factory import MaterialFactory
from materials.material import Material
from materials.models import NuclideComponent
from materials.thermal import TemperatureDependentDensity
from materials.constants import AVOGADRO, MASS_O


class UO2Density(TemperatureDependentDensity):
    """UO2 density model with theoretical density and dishing."""
    def __init__(self, theoretical_density_frac: float = 0.95, dishing_percent: float = 0.0):
        self.td_frac = theoretical_density_frac
        self.dishing = dishing_percent

    def _get_thermal_expansion(self, T: float) -> float:
        """Legacy UO2 thermal expansion (refs/mat.py:281-287)"""
        if T >= 273 and T <= 923:
            return (9.9734E-1 + 9.802E-6*T - 2.705E-10*T*T + 4.291E-13*T*T*T)
        elif T > 923 and T <= 3120:
            return (9.9672E-1 + 1.179E-5*T - 2.429E-9*T*T + 1.219E-12*T*T*T)
        else:
            return 1.0

    def get_density(self, T: float) -> float:
        super().get_density(T)
        # Base TD at 300K is ~10.963 g/cm3
        rho_td = 10.963
        expansion = self._get_thermal_expansion(T)
        return (rho_td / (expansion ** 3)) * self.td_frac * (1.0 - self.dishing/100.0)


def _rho_UO2(T: float, theoretical_density_frac: float = 1.0, dishing_percent: float = 0.0) -> float:
    """Helper for UO2 theoretical density at temperature T.

    Applies theoretical_density_frac and dishing_percent directly
    through the UO2Density class instead of hardcoding them.
    """
    return UO2Density(
        theoretical_density_frac=theoretical_density_frac,
        dishing_percent=dishing_percent
    ).get_density(T)


@MaterialFactory.register("uo2")
def create_uo2(
    temperature: float = 300,
    enrichment_w_percent: float = 0.711,
    theoretical_density_frac: float = 0.95,
    dishing_percent: float = 0.0
) -> Material:
    """
    Create UO2 with specified enrichment, temperature, and density.
    """
    # _rho_UO2 now applies theoretical_density_frac and dishing internally
    rho = _rho_UO2(temperature, theoretical_density_frac, dishing_percent)
    enr_frac = enrichment_w_percent / 100.0
    
    # Calculate U-234 fraction: η = 0.007731 * ε^1.0837 (in percent)
    eta_pct = 0.007731 * (enr_frac * 100) ** 1.0837
    eta = eta_pct / 100.0
    
    # Atomic masses (from tabn.md)
    M35 = 235.0439
    M34 = 234.0409
    M38 = 238.0508
    
    M_U = 1.0 / (eta/M34 + enr_frac/M35 + (1 - eta - enr_frac)/M38)
    MUO2 = M_U + 2 * MASS_O
    
    u_density = rho * M_U / MUO2
    
    # Atom densities (atoms/b-cm)
    N_U234 = eta * u_density * AVOGADRO / M34
    N_U235 = enr_frac * u_density * AVOGADRO / M35
    N_U238 = (1 - eta - enr_frac) * u_density * AVOGADRO / M38
    N_O = 2 * (N_U234 + N_U235 + N_U238)
    
    total_atoms = N_U234 + N_U235 + N_U238 + N_O
    total_mass = N_U234 * M34 + N_U235 * M35 + N_U238 * M38 + N_O * MASS_O
    
    mat = Material(f"UO2_{enrichment_w_percent}%_{temperature}K", rho)
    
    mat.nuclides.append(NuclideComponent(92, 235, 'U', weight_frac=N_U235*M35/total_mass, atom_frac=N_U235/total_atoms, atom_density=N_U235))
    mat.nuclides.append(NuclideComponent(92, 234, 'U', weight_frac=N_U234*M34/total_mass, atom_frac=N_U234/total_atoms, atom_density=N_U234))
    mat.nuclides.append(NuclideComponent(92, 238, 'U', weight_frac=N_U238*M38/total_mass, atom_frac=N_U238/total_atoms, atom_density=N_U238))
    mat.nuclides.append(NuclideComponent(8, 16, 'O', weight_frac=N_O*MASS_O/total_mass, atom_frac=N_O/total_atoms, atom_density=N_O))
    
    mat.molecular_weight = MUO2
    mat.total_atom_density = rho * AVOGADRO / MUO2
    
    return mat
