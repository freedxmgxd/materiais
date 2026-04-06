"""
Material Factory with Plugin Support

This module provides a factory pattern for creating nuclear materials with support
for dynamic plugin loading from the ./libs/ directory.
"""
from typing import List, Optional, Callable, Any
import importlib
import os
import inspect

from .material import Material
from .models import NuclideComponent


class MaterialFactory:
    """
    Factory for creating common nuclear materials with plugin support.
    
    Usage:
        # Direct creation
        material = MaterialFactory.create("uo2", temperature=600, enrichment_w_percent=3.0)
        
        # Register custom material
        @MaterialFactory.register("custom_fuel")
        def create_custom_fuel(**kwargs):
            return Material("CustomFuel", density=10.0)
    """
    
    _registry: dict[str, Callable[..., Material]] = {}
    _plugins_loaded: bool = False
    _pnnl_dir: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pnnl', 'json')

    @classmethod
    def register(cls, name: str) -> Callable[[Callable[..., Material]], Callable[..., Material]]:
        """
        Decorator to register a material constructor function.
        
        Args:
            name: Material name (case-insensitive) to register
            
        Returns:
            Decorator function that registers the constructor
            
        Example:
            @MaterialFactory.register("uo2")
            def create_uo2(**kwargs):
                # ... implementation
                return material
        """
        def decorator(func: Callable[..., Material]) -> Callable[..., Material]:
            # Store with lowercase key for case-insensitive lookup
            cls._registry[name.lower()] = func
            return func
        return decorator

    @classmethod
    def _load_plugins(cls) -> None:
        """
        Dynamically load all plugin files from the ./libs/ directory.
        
        This method scans the libs/ folder for Python files (.py)
        and imports them to trigger any @MaterialFactory.register decorators.
        Files starting with '__' are ignored.
        """
        if cls._plugins_loaded:
            return
            
        # Get the path to the libs directory (relative to this file)
        # The libs folder is at materials/libs/
        base_dir = os.path.dirname(os.path.abspath(__file__))
        libs_dir = os.path.join(base_dir, 'libs')
        
        if not os.path.isdir(libs_dir):
            # Create directory if it doesn't exist
            os.makedirs(libs_dir, exist_ok=True)
            cls._plugins_loaded = True
            return
        
        # Import all .py files except __init__.py
        for filename in os.listdir(libs_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]  # Remove .py extension
                try:
                    # Import the module to trigger decorators
                    importlib.import_module(f'materials.libs.{module_name}')
                except ImportError as e:
                    print(f"Warning: Could not load plugin {module_name}: {e}")
                except Exception as e:
                    print(f"Warning: Error loading plugin {module_name}: {e}")
        
        cls._plugins_loaded = True

    @classmethod
    def create(cls, material_name: str, **kwargs) -> Material:
        """
        Create a material by name using the registered constructors.
        
        Args:
            material_name: Name of the material to create (case-insensitive)
            **kwargs: Additional arguments passed to the material constructor
            
        Returns:
            Material instance
            
        Raises:
            ValueError: If the material is not found in the registry or PNNL database
        """
        # Load plugins if they haven't been loaded yet
        if not cls._plugins_loaded:
            cls._load_plugins()
        
        # Normalize material name to lowercase for case-insensitive lookup
        key = material_name.lower()
        
        # 1. Check registry (plugins)
        if key in cls._registry:
            constructor = cls._registry[key]
            return constructor(**kwargs)

        # 2. Check PNNL database
        pnnl_id = None
        if key.startswith("pnnl:"):
            pnnl_id = key.split(":")[1]
        
        if pnnl_id:
            # Try to find file starting with ID or containing name
            if os.path.isdir(cls._pnnl_dir):
                for filename in os.listdir(cls._pnnl_dir):
                    if filename.startswith(pnnl_id) or pnnl_id.lower() in filename.lower():
                        return Material.from_json(os.path.join(cls._pnnl_dir, filename))
            raise ValueError(f"PNNL material '{pnnl_id}' not found in {cls._pnnl_dir}")

        # Fallback: check if the name exists in PNNL directory
        if os.path.isdir(cls._pnnl_dir):
            for filename in os.listdir(cls._pnnl_dir):
                if key in filename.lower():
                     return Material.from_json(os.path.join(cls._pnnl_dir, filename))
        
        available = list(cls._registry.keys())
        raise ValueError(
            f"Material '{material_name}' not found in registry or PNNL database. "
            f"Available plugins: {available}"
        )

    @classmethod
    def list_materials(cls) -> List[str]:
        """
        List all registered material names.
        
        Returns:
            List of registered material names (lowercase)
        """
        if not cls._plugins_loaded:
            cls._load_plugins()
        return list(cls._registry.keys())

    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        Unregister a material from the registry.
        
        Args:
            name: Material name to unregister
            
        Returns:
            True if material was unregistered, False if not found
        """
        key = name.lower()
        if key in cls._registry:
            del cls._registry[key]
            return True
        return False


# ============================================================================
# NOTE: Material plugins are now loaded from materials/libs/
# Use @MaterialFactory.register() decorator to register new materials
# ============================================================================
