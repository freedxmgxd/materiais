"""
Centralized abstract models for thermal properties.
Note: Concrete implementations should remain in their respective plugin files.
"""
from abc import ABC, abstractmethod

class TemperatureDependentDensity(ABC):
    """
    Base class for temperature-dependent density models.
    
    Subclasses should implement get_density for specific materials.
    """
    
    @abstractmethod
    def get_density(self, T: float) -> float:
        """
        Return density in g/cm3 at temperature T (Kelvin).
        
        Args:
            T: Temperature in Kelvin. Must be > 0.
        """
        if T <= 0:
            raise ValueError("Temperature must be greater than 0 Kelvin.")
        pass
