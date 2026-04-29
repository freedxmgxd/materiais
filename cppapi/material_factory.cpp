#include "material_factory.hpp"
#include "material.hpp"

#include <cmath>
#include <filesystem>
#include <stdexcept>
#include <algorithm>
#include <functional>
#include <map>
#include <string>
#include <vector>

namespace materiais {

namespace {

std::string to_lower(std::string value) {
    for (char& c : value) {
        c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    }
    return value;
}

double get_param(const std::map<std::string, double>& params, const std::string& name, double default_value) {
    auto it = params.find(name);
    if (it != params.end()) {
        return it->second;
    }
    return default_value;
}

Material create_uo2(const std::map<std::string, double>& params) {
    double temperature = get_param(params, "temperature", 300.0);
    double enrichment_w_percent = get_param(params, "enrichment_w_percent", 0.711);
    double theoretical_density_frac = get_param(params, "theoretical_density_frac", 1.0);
    double dishing_percent = get_param(params, "dishing_percent", 0.0);

    const double MASS_O = 15.999;
    const double M35 = 235.0439;
    const double M34 = 234.0409;
    const double M38 = 238.0508;
    const double AVOGADRO = 6.02214076e23;

    auto get_density = [&](double T) {
        double expansion;
        if (T >= 273 && T <= 923) {
            expansion = 9.9734E-1 + 9.802E-6 * T - 2.705E-10 * T * T + 4.291E-13 * T * T * T;
        } else if (T > 923 && T <= 3120) {
            expansion = 9.9672E-1 + 1.179E-5 * T - 2.429E-9 * T * T + 1.219E-12 * T * T * T;
        } else {
            expansion = 1.0;
        }
        return (10.963 / (expansion * expansion * expansion)) * theoretical_density_frac * (1.0 - dishing_percent / 100.0);
    };

    double rho = get_density(temperature);
    double enr_frac = enrichment_w_percent / 100.0;
    double eta_pct = 0.007731 * std::pow(enr_frac * 100.0, 1.0837);
    double eta = eta_pct / 100.0;

    double M_U = 1.0 / (eta / M34 + enr_frac / M35 + (1.0 - eta - enr_frac) / M38);
    double MUO2 = M_U + 2.0 * MASS_O;
    double u_density = rho * M_U / MUO2;

    double N_U234 = eta * u_density * AVOGADRO / M34;
    double N_U235 = enr_frac * u_density * AVOGADRO / M35;
    double N_U238 = (1.0 - eta - enr_frac) * u_density * AVOGADRO / M38;
    double N_O = 2.0 * (N_U234 + N_U235 + N_U238);

    double total_atoms = N_U234 + N_U235 + N_U238 + N_O;
    double total_mass = N_U234 * M34 + N_U235 * M35 + N_U238 * M38 + N_O * MASS_O;

    Material material("UO2_" + std::to_string(enrichment_w_percent) + "%_" + std::to_string(static_cast<int>(temperature)) + "K", rho);
    material.add_nuclide({92, 235, "U", N_U235 * M35 / total_mass, N_U235 / total_atoms, N_U235, M35});
    material.add_nuclide({92, 234, "U", N_U234 * M34 / total_mass, N_U234 / total_atoms, N_U234, M34});
    material.add_nuclide({92, 238, "U", N_U238 * M38 / total_mass, N_U238 / total_atoms, N_U238, M38});
    material.add_nuclide({8, 16, "O", N_O * MASS_O / total_mass, N_O / total_atoms, N_O, MASS_O});
    material.calculate_properties(true);
    return material;
}

Material create_helium(const std::map<std::string, double>& params) {
    double temperature = get_param(params, "temperature", 600.0);
    double pressure = get_param(params, "pressure", 8.0);
    if (temperature <= 0.0) {
        throw std::invalid_argument("Temperature must be positive.");
    }
    if (pressure <= 0.0) {
        throw std::invalid_argument("Pressure must be positive.");
    }
    double rho = 4.0 * pressure / (8.314 * temperature);
    Material material("He_" + std::to_string(static_cast<int>(temperature)) + "K_" + std::to_string(static_cast<int>(pressure)) + "MPa", rho);
    material.expand_element_to_isotopes("He", 1.0);
    material.calculate_properties();
    return material;
}

Material create_sodium(const std::map<std::string, double>& params) {
    double temperature = get_param(params, "temperature", 800.0);
    if (temperature < 371.0) {
        throw std::invalid_argument("Sodium is solid below 371K.");
    }
    double rho = (951.5 - 0.2235 * temperature) / 1000.0;
    Material material("Na_" + std::to_string(static_cast<int>(temperature)) + "K", rho);
    material.expand_element_to_isotopes("Na", 1.0);
    material.calculate_properties();
    return material;
}

Material create_lead(const std::map<std::string, double>& params) {
    double temperature = get_param(params, "temperature", 700.0);
    if (temperature < 600.0) {
        throw std::invalid_argument("Lead is solid below 600K.");
    }
    double rho = (11342.0 - 1.194 * temperature) / 1000.0;
    Material material("Pb_" + std::to_string(static_cast<int>(temperature)) + "K", rho);
    material.expand_element_to_isotopes("Pb", 1.0);
    material.calculate_properties();
    return material;
}

Material create_lbe(const std::map<std::string, double>& params) {
    double temperature = get_param(params, "temperature", 700.0);
    if (temperature < 400.0) {
        throw std::invalid_argument("LBE is solid below approximately 400K.");
    }
    double rho = (11070.0 - 1.17 * temperature) / 1000.0;
    return Material::from_weight_fractions("LBE_" + std::to_string(static_cast<int>(temperature)) + "K", rho, {"Pb", "Bi"}, {0.445, 0.555});
}

Material create_ss316(const std::map<std::string, double>& params) {
    double temperature = get_param(params, "temperature", 300.0);
    double rho = (8084.0 - 0.4209 * temperature - 3.894e-5 * temperature * temperature) / 1000.0;
    std::vector<std::string> elements = {"Fe", "Cr", "Ni", "Mo", "Mn", "Si", "C"};
    std::vector<double> fractions = {0.655, 0.170, 0.120, 0.025, 0.020, 0.010, 0.0003};
    double rem = 1.0;
    for (size_t i = 1; i < fractions.size(); ++i) {
        rem -= fractions[i];
    }
    fractions[0] = rem;
    Material material = Material::from_weight_fractions("SS316_" + std::to_string(static_cast<int>(temperature)) + "K", rho, elements, fractions);
    bool carbon_exists = std::any_of(material.nuclides().begin(), material.nuclides().end(), [](const NuclideComponent& n) {
        return n.Z == 6 && n.A == 13;
    });
    if (carbon_exists) {
        material.apply_substitution(6013, 6012);
    }
    return material;
}

Material create_zircaloy4(const std::map<std::string, double>& params) {
    double temperature = get_param(params, "temperature", 300.0);
    double alpha = 6.7e-6;
    double rho = 6.56 / std::pow(1.0 + alpha * (temperature - 300.0), 3);
    return Material::from_weight_fractions("Zry4_" + std::to_string(static_cast<int>(temperature)) + "K", rho, {"Zr", "Sn", "Fe", "Cr"}, {0.9811, 0.0150, 0.0021, 0.0018});
}

Material create_beo(const std::map<std::string, double>& params) {
    double temperature = get_param(params, "temperature", 300.0);
    double rho = 3.01 / std::pow(1.0 + 9e-6 * (temperature - 300.0), 3);
    return Material::from_atom_fractions("BeO_" + std::to_string(static_cast<int>(temperature)) + "K", rho, {"Be", "O"}, {0.5, 0.5});
}

std::map<std::string, MaterialFactory::MaterialCreator>& registry() {
    static std::map<std::string, MaterialFactory::MaterialCreator> instance;
    return instance;
}

bool plugins_loaded = false;

void load_plugins() {
    if (plugins_loaded) {
        return;
    }
    registry().emplace("uo2", create_uo2);
    registry().emplace("helium", create_helium);
    registry().emplace("sodium", create_sodium);
    registry().emplace("lead", create_lead);
    registry().emplace("lbe", create_lbe);
    registry().emplace("ss316", create_ss316);
    registry().emplace("zircaloy4", create_zircaloy4);
    registry().emplace("beo", create_beo);
    plugins_loaded = true;
}

} // namespace

Material MaterialFactory::create(const std::string& material_name, const std::map<std::string, double>& params) {
    load_plugins();
    std::string key = to_lower(material_name);
    auto it = registry().find(key);
    if (it != registry().end()) {
        return it->second(params);
    }

    std::filesystem::path base_path(__FILE__);
    base_path = base_path.parent_path().parent_path() / "materials" / "pnnl" / "json";

    if (key.rfind("pnnl:", 0) == 0) {
        std::string pnnl_id = key.substr(5);
        for (auto& entry : std::filesystem::directory_iterator(base_path)) {
            auto filename = entry.path().filename().string();
            if (filename.rfind(pnnl_id, 0) == 0 || filename.find(pnnl_id) != std::string::npos) {
                return Material::from_json_file(entry.path().string());
            }
        }
        throw std::invalid_argument("PNNL material '" + material_name + "' not found");
    }

    for (auto& entry : std::filesystem::directory_iterator(base_path)) {
        std::string filename = entry.path().filename().string();
        std::string lower_filename = to_lower(filename);
        if (lower_filename.find(key) != std::string::npos) {
            return Material::from_json_file(entry.path().string());
        }
    }

    throw std::invalid_argument("Material '" + material_name + "' not found");
}

std::vector<std::string> MaterialFactory::list_materials() {
    load_plugins();
    std::vector<std::string> result;
    for (const auto& pair : registry()) {
        result.push_back(pair.first);
    }

    std::filesystem::path base_path(__FILE__);
    base_path = base_path.parent_path().parent_path() / "materials" / "pnnl" / "json";
    if (std::filesystem::exists(base_path) && std::filesystem::is_directory(base_path)) {
        for (const auto& entry : std::filesystem::directory_iterator(base_path)) {
            if (!entry.path().has_extension()) {
                continue;
            }
            if (entry.path().extension() != ".json") {
                continue;
            }
            std::string name = entry.path().stem().string();
            std::string lowered = to_lower(name);
            result.push_back(lowered);
        }
    }

    std::sort(result.begin(), result.end());
    result.erase(std::unique(result.begin(), result.end()), result.end());
    return result;
}

void MaterialFactory::register_material(const std::string& name, MaterialCreator creator) {
    load_plugins();
    registry().emplace(to_lower(name), std::move(creator));
}

bool MaterialFactory::unregister_material(const std::string& name) {
    load_plugins();
    return registry().erase(to_lower(name)) > 0;
}

} // namespace materiais
