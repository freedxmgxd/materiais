# Nuclear Data References

This directory contains the foundational nuclear data used for material reconstruction.

## Data Sources

### 1. Atomic Masses (`atomic_masses.json`)
- **Source**: Atomic Mass Evaluation (AME2020).
- **Reference**: Wang, M., et al. "The AME2020 atomic mass evaluation (II). Tables, graphs and references." Chinese Physics C 45.3 (2021): 030003.
- **Units**: Atomic mass units (u).

### 2. Natural Abundances (`natural_abundances.json`)
- **Source**: IUPAC Periodic Table of the Isotopes.
- **Reference**: Meija, J., et al. "Isotopic compositions of the elements 2013 (IUPAC Technical Report)." Pure and Applied Chemistry 88.3 (2016): 293-306.
- **Updates**: Partially updated with 2021 IUPAC recommendations where applicable.

### 3. Periodic Table (`periodic_table.json`)
- **Source**: Standard chemical nomenclature.
- **Reference**: IUPAC Red Book (Nomenclature of Inorganic Chemistry).

### 4. Cross-Section Substitutions (`xs_substitutions.json`)
- **Source**: MCNP6 Data Collection.
- **Description**: Mapping of isotopes to available cross-section libraries (e.g., substituting O-18 with O-16 when specific O-18 data is unavailable).

## Maintenance

These files are intended to be read-only by the framework. Any updates to the nuclear data should be performed by replacing the JSON files and updating these references.
