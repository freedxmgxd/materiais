from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass(frozen=True)
class IsotopeData:
    """Raw isotope data from nuclear database."""
    A: int
    mass: float
    abundance: float = 0.0

@dataclass(frozen=True)
class ElementData:
    """Elemental data including isotopes and cumulative probabilities."""
    Z: int
    symbol: str
    isotopes: List[IsotopeData]
    collprob: List[float] = field(default_factory=list)

@dataclass
class NuclideComponent:
    """Representation of a specific nuclide within a material."""
    Z: int
    A: int
    element: str
    weight_frac: float = 0.0
    atom_frac: float = 0.0
    atom_density: float = 0.0  # atoms/b-cm

@dataclass
class SubstitutionRule:
    """Rule for replacing one isotope with another or distributing it."""
    from_zaid: int
    to_zaid: Optional[int] = None  # None means distribute based on natural abundance
    reason: str = ""
