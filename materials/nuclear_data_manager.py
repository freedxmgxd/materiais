import json
import os
from typing import Dict, List, Optional, Tuple
from .models import ElementData, IsotopeData, SubstitutionRule

class NuclearDataManager:
    """
    Singleton for managing nuclear data (atomic masses, abundances, substitutions).
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(NuclearDataManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, data_dir: str = None):
        if self._initialized:
            return
            
        if data_dir is None:
            # 1. Try environment variable
            data_dir = os.environ.get("NUCLEAR_DATA_PATH")
            
        if data_dir is None:
            # 2. Try package installation path
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # If installed as package, nuclear_data is likely at base_dir/nuclear_data
            data_dir = os.path.join(base_dir, "nuclear_data")
            
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Nuclear data directory not found at: {data_dir}")
            
        self.data_dir = data_dir
        self.elements: Dict[str, ElementData] = {}
        self.periodic_table: Dict[str, int] = {}
        self.z_to_symbol: Dict[int, str] = {}
        self.substitutions: Dict[int, SubstitutionRule] = {}
        self.atomic_masses: Dict[Tuple[int, int], float] = {}
        
        self.load_all()
        self._initialized = True

    def load_all(self):
        """Load all JSON data files."""
        self._load_periodic_table()
        self._load_natural_abundances()
        self._load_atomic_masses()
        self._load_substitutions()

    def _load_periodic_table(self):
        path = os.path.join(self.data_dir, "periodic_table.json")
        with open(path, 'r') as f:
            self.periodic_table = json.load(f)
            self.z_to_symbol = {v: k for k, v in self.periodic_table.items()}

    def _load_natural_abundances(self):
        path = os.path.join(self.data_dir, "natural_abundances.json")
        with open(path, 'r') as f:
            data = json.load(f)
            for sym, info in data.items():
                isotopes = [IsotopeData(**iso) for iso in info['isotopes']]
                self.elements[sym] = ElementData(
                    Z=info['Z'],
                    symbol=sym,
                    isotopes=isotopes,
                    collprob=info['collprob']
                )

    def _load_atomic_masses(self):
        path = os.path.join(self.data_dir, "atomic_masses.json")
        with open(path, 'r') as f:
            data = json.load(f)
            for sym, info in data.items():
                Z = info['Z']
                for iso in info['isotopes']:
                    self.atomic_masses[(Z, iso['A'])] = iso['mass']

    def _load_substitutions(self):
        path = os.path.join(self.data_dir, "xs_substitutions.json")
        with open(path, 'r') as f:
            data = json.load(f)
            for sub in data.get("substitutions", []):
                from_zaid = self.parse_zaid(sub["from"])
                to_zaid = self.parse_zaid(sub["to"]) if sub.get("to") else None
                rule = SubstitutionRule(from_zaid=from_zaid, to_zaid=to_zaid, reason=sub.get("reason", ""))
                self.substitutions[from_zaid] = rule

    def parse_zaid(self, zaid_str: str) -> int:
        """Parse 'O-18' or '8018' to integer ZAID."""
        if '-' in zaid_str:
            sym, a_str = zaid_str.split('-')
            z = self.periodic_table.get(sym)
            if z is None:
                raise ValueError(f"Unknown element symbol: {sym}")
            return z * 1000 + int(a_str)
        return int(zaid_str)

    def get_element(self, symbol: str) -> ElementData:
        return self.elements.get(symbol)

    def get_mass(self, z: int, a: int) -> float:
        return self.atomic_masses.get((z, a))

    def get_symbol(self, z: int) -> str:
        return self.z_to_symbol.get(z)

    def get_z(self, symbol: str) -> int:
        return self.periodic_table.get(symbol)
