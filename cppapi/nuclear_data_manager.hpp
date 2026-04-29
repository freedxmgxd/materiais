#pragma once

import materiais.nuclear_data_manager;
    explicit NuclearDataManager(std::string data_dir = {});

    const ElementData* get_element(const std::string& symbol) const noexcept;
    double get_mass(int z, int a) const noexcept;
    std::string get_symbol(int z) const noexcept;
    int get_z(const std::string& symbol) const noexcept;
    const SubstitutionRule* get_substitution(int from_zaid) const noexcept;

private:
    std::string data_dir_;
    std::map<std::string, ElementData> elements_;
    std::array<std::string, 119> periodic_table_;
    std::map<int, double> atomic_masses_;
    std::map<int, SubstitutionRule> substitutions_;

    void load_all();
    void load_periodic_table();
    void load_natural_abundances();
    void load_atomic_masses();
    void load_substitutions();
    int parse_zaid(const std::string& zaid_str) const;
};

} // namespace materiais
