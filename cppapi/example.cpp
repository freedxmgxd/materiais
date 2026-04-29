#include <iostream>
#include <map>
#include "material_factory.hpp"

int main() {
    auto uo2 = materiais::MaterialFactory::create("uo2", {
        {"temperature", 600.0},
        {"enrichment_w_percent", 4.5},
        {"theoretical_density_frac", 0.95},
        {"dishing_percent", 0.0},
    });
    std::cout << uo2.get_summary() << "\n";

    auto json = uo2.to_json();
    std::cout << json << "\n";
    uo2.to_json_file("uo2_material.json");

    auto brass = materiais::Material::from_weight_fractions(
        "Brass",
        8.4,
        {"Cu", "Zn"},
        {0.7, 0.3}
    );
    brass.add_impurities({{"C", 100.0}}, "ppm_w", "Cu");
    std::cout << brass.get_summary() << "\n";

    auto ss316 = materiais::MaterialFactory::create("ss316", {
        {"temperature", 300.0},
    });
    std::cout << ss316.get_summary() << "\n";

    return 0;
}
