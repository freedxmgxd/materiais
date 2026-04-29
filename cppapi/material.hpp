#pragma once

import materiais.material;
    Material(std::string name, double density = 0.0);

    static Material from_weight_fractions(
        std::string name,
        double density,
        const std::vector<std::string>& elements,
        const std::vector<double>& fractions
    );

    static Material from_atom_fractions(
        std::string name,
        double density,
        const std::vector<std::string>& elements,
        const std::vector<double>& fractions
    );

    void add_nuclide(const NuclideComponent& nuclide);
    void expand_element_to_isotopes(const std::string& element, double weight_fraction);
    void calculate_properties(bool based_on_atom = false);
    void apply_substitution(int from_zaid, int to_zaid = -1);
    void apply_substitution_element(const std::string& element, int from_A, int to_A = -1);
    void set_substitutions(const std::vector<SubstitutionRule>& substitutions);
    void add_impurities(
        const std::map<std::string, double>& impurities,
        const std::string& unit = "ppm_w",
        const std::string& balance_element = "",
        const std::string& reference_element = ""
    );
    std::string to_json() const;
    void to_json_file(const std::string& filepath) const;
    static Material from_json_file(const std::string& filepath);
    std::string get_summary() const;
    std::string to_openmc_xml(int material_id = 1) const;

    const std::vector<NuclideComponent>& nuclides() const noexcept;
    double total_atom_density() const noexcept;
    double density() const noexcept;

private:
    std::string name_;
    double density_;
    double molecular_weight_;
    double total_atom_density_;
    std::vector<NuclideComponent> nuclides_;
    NuclearDataManager data_manager_;

    static constexpr double AVOGADRO = 6.02214076e23;
    int find_nuclide(int z, int a) const noexcept;
    std::string nuclide_name(const NuclideComponent& nuc) const;
};

} // namespace materiais
