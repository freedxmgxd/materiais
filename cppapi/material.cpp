export module materiais.material;

#include <cmath>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>
#include <map>

import materiais.models;
import materiais.nuclear_data_manager;
import materiais.json;

export namespace materiais {

Material::Material(std::string name, double density)
    : name_(std::move(name)),
      density_(density),
      molecular_weight_(0.0),
      total_atom_density_(0.0) {}

Material Material::from_weight_fractions(
    std::string name,
    double density,
    const std::vector<std::string>& elements,
    const std::vector<double>& fractions
) {
    if (elements.size() != fractions.size()) {
        throw std::invalid_argument("Elements and fractions must have the same size");
    }
    double total = 0.0;
    for (double value : fractions) {
        total += value;
    }
    if (std::abs(total - 1.0) > 1e-6) {
        throw std::invalid_argument("Weight fractions must sum to 1.0");
    }

    Material material(std::move(name), density);
    for (size_t i = 0; i < elements.size(); ++i) {
        const std::string& symbol = elements[i];
        double weight_frac = fractions[i];
        const ElementData* element_data = material.data_manager_.get_element(symbol);
        if (!element_data) {
            throw std::invalid_argument("Unknown element: " + symbol);
        }
        double avg_mass = 0.0;
        for (const auto& isotope : element_data->isotopes) {
            avg_mass += isotope.abundance * isotope.mass;
        }
        for (const auto& isotope : element_data->isotopes) {
            double iso_weight = 0.0;
            if (avg_mass > 0.0) {
                iso_weight = weight_frac * (isotope.abundance * isotope.mass / avg_mass);
            }
            if (iso_weight > 0.0) {
                material.add_nuclide({
                    element_data->Z,
                    isotope.A,
                    symbol,
                    iso_weight,
                    0.0,
                    0.0,
                    isotope.mass,
                });
            }
        }
    }
    material.calculate_properties(false);
    return material;
}

Material Material::from_atom_fractions(
    std::string name,
    double density,
    const std::vector<std::string>& elements,
    const std::vector<double>& fractions
) {
    if (elements.size() != fractions.size()) {
        throw std::invalid_argument("Elements and fractions must have the same size");
    }
    double total = 0.0;
    for (double value : fractions) {
        total += value;
    }
    if (std::abs(total - 1.0) > 1e-6) {
        throw std::invalid_argument("Atom fractions must sum to 1.0");
    }

    Material material(std::move(name), density);
    for (size_t i = 0; i < elements.size(); ++i) {
        const std::string& symbol = elements[i];
        double atom_frac = fractions[i];
        const ElementData* element_data = material.data_manager_.get_element(symbol);
        if (!element_data) {
            throw std::invalid_argument("Unknown element: " + symbol);
        }
        double total_abundance = 0.0;
        for (const auto& isotope : element_data->isotopes) {
            total_abundance += isotope.abundance;
        }
        for (const auto& isotope : element_data->isotopes) {
            double iso_atom = 0.0;
            if (total_abundance > 0.0) {
                iso_atom = atom_frac * (isotope.abundance / total_abundance);
            }
            if (iso_atom > 0.0) {
                material.add_nuclide({
                    element_data->Z,
                    isotope.A,
                    symbol,
                    0.0,
                    iso_atom,
                    0.0,
                    isotope.mass,
                });
            }
        }
    }
    material.calculate_properties(true);
    return material;
}

void Material::add_nuclide(const NuclideComponent& nuclide) {
    nuclides_.push_back(nuclide);
}

void Material::expand_element_to_isotopes(const std::string& element, double weight_fraction) {
    const ElementData* element_data = data_manager_.get_element(element);
    if (!element_data) {
        return;
    }
    double avg_mass = 0.0;
    for (const auto& isotope : element_data->isotopes) {
        avg_mass += isotope.abundance * isotope.mass;
    }
    for (const auto& isotope : element_data->isotopes) {
        double iso_weight = 0.0;
        if (avg_mass > 0.0) {
            iso_weight = weight_fraction * (isotope.abundance * isotope.mass / avg_mass);
        }
        if (iso_weight > 0.0) {
            add_nuclide({
                element_data->Z,
                isotope.A,
                element,
                iso_weight,
                0.0,
                0.0,
                isotope.mass,
            });
        }
    }
}

void Material::calculate_properties(bool based_on_atom) {
    if (nuclides_.empty()) {
        return;
    }

    if (based_on_atom) {
        molecular_weight_ = 0.0;
        for (const auto& nuclide : nuclides_) {
            double mass = nuclide.mass;
            if (mass <= 0.0) {
                mass = data_manager_.get_mass(nuclide.Z, nuclide.A);
            }
            molecular_weight_ += nuclide.atom_frac * mass;
        }
        for (auto& nuclide : nuclides_) {
            double mass = nuclide.mass;
            if (mass <= 0.0) {
                mass = data_manager_.get_mass(nuclide.Z, nuclide.A);
            }
            nuclide.weight_frac = (molecular_weight_ > 0.0) ? (nuclide.atom_frac * mass / molecular_weight_) : 0.0;
        }
    } else {
        double inv_mw = 0.0;
        for (const auto& nuclide : nuclides_) {
            double mass = nuclide.mass;
            if (mass <= 0.0) {
                mass = data_manager_.get_mass(nuclide.Z, nuclide.A);
            }
            if (mass > 0.0) {
                inv_mw += nuclide.weight_frac / mass;
            }
        }
        molecular_weight_ = (inv_mw > 0.0) ? (1.0 / inv_mw) : 0.0;
        for (auto& nuclide : nuclides_) {
            double mass = nuclide.mass;
            if (mass <= 0.0) {
                mass = data_manager_.get_mass(nuclide.Z, nuclide.A);
            }
            nuclide.atom_frac = (mass > 0.0) ? ((nuclide.weight_frac / mass) * molecular_weight_) : 0.0;
        }
    }

    if (density_ > 0.0 && molecular_weight_ > 0.0) {
        total_atom_density_ = (density_ * AVOGADRO) / molecular_weight_;
        for (auto& nuclide : nuclides_) {
            nuclide.atom_density = nuclide.atom_frac * total_atom_density_;
        }
    }
}

int Material::find_nuclide(int z, int a) const noexcept {
    for (size_t i = 0; i < nuclides_.size(); ++i) {
        if (nuclides_[i].Z == z && nuclides_[i].A == a) {
            return static_cast<int>(i);
        }
    }
    return -1;
}

void Material::apply_substitution(int from_zaid, int to_zaid) {
    int z = from_zaid / 1000;
    int a_from = from_zaid % 1000;
    int index = find_nuclide(z, a_from);
    if (index < 0) {
        return;
    }
    NuclideComponent source = nuclides_[index];
    nuclides_.erase(nuclides_.begin() + index);
    double fraction = source.atom_frac;
    if (fraction <= 0.0) {
        calculate_properties(true);
        return;
    }

    if (to_zaid >= 0) {
        int a_to = to_zaid % 1000;
        int target = find_nuclide(z, a_to);
        if (target >= 0) {
            nuclides_[target].atom_frac += fraction;
        } else {
            nuclides_.push_back({z, a_to, source.element, 0.0, fraction, 0.0, source.mass});
        }
    } else {
        const ElementData* element_data = data_manager_.get_element(source.element);
        if (!element_data) {
            return;
        }
        double total_abd = 0.0;
        for (const auto& iso : element_data->isotopes) {
            if (iso.A == a_from) {
                continue;
            }
            total_abd += iso.abundance;
        }
        if (total_abd <= 0.0) {
            return;
        }
        for (const auto& iso : element_data->isotopes) {
            if (iso.A == a_from) {
                continue;
            }
            double share = fraction * (iso.abundance / total_abd);
            if (share <= 0.0) {
                continue;
            }
            int target = find_nuclide(z, iso.A);
            if (target >= 0) {
                nuclides_[target].atom_frac += share;
            } else {
                nuclides_.push_back({z, iso.A, source.element, 0.0, share, 0.0, iso.mass});
            }
        }
    }
    calculate_properties(true);
}

void Material::apply_substitution_element(const std::string& element, int from_A, int to_A) {
    int z = data_manager_.get_z(element);
    if (z <= 0) {
        return;
    }
    int to_zaid = (to_A > 0) ? (z * 1000 + to_A) : -1;
    apply_substitution(z * 1000 + from_A, to_zaid);
}

void Material::set_substitutions(const std::vector<SubstitutionRule>& substitutions) {
    for (const auto& rule : substitutions) {
        apply_substitution(rule.from_zaid, rule.to_zaid);
    }
}

void Material::add_impurities(
    const std::map<std::string, double>& impurities,
    const std::string& unit,
    const std::string& balance_element,
    const std::string& reference_element
) {
    if (nuclides_.empty()) {
        throw std::invalid_argument("Cannot add impurities to an empty material");
    }

    calculate_properties();

    bool is_atom = false;
    std::map<std::string, double> target_impurities;

    if (unit == "ug/g_ref") {
        if (reference_element.empty()) {
            throw std::invalid_argument("reference_element required for 'ug/g_ref' unit");
        }
        double ref_w = 0.0;
        for (const auto& n : nuclides_) {
            if (n.element == reference_element) {
                ref_w += n.weight_frac;
            }
        }
        for (const auto& item : impurities) {
            target_impurities[item.first] = item.second * 1e-6 * ref_w;
        }
        is_atom = false;
    } else if (unit == "ppm_w") {
        for (const auto& item : impurities) {
            target_impurities[item.first] = item.second * 1e-6;
        }
        is_atom = false;
    } else if (unit == "ppm_a") {
        for (const auto& item : impurities) {
            target_impurities[item.first] = item.second * 1e-6;
        }
        is_atom = true;
    } else if (unit == "w_frac") {
        target_impurities = impurities;
        is_atom = false;
    } else if (unit == "a_frac") {
        target_impurities = impurities;
        is_atom = true;
    } else {
        throw std::invalid_argument("Unknown unit: " + unit);
    }

    std::map<std::string, double> elements_frac;
    std::map<std::string, std::map<int, double>> iso_distributions;

    for (const auto& n : nuclides_) {
        double value = is_atom ? n.atom_frac : n.weight_frac;
        elements_frac[n.element] += value;
        iso_distributions[n.element][n.A] = value;
    }

    for (auto& entry : iso_distributions) {
        double total = 0.0;
        for (const auto& pair : entry.second) {
            total += pair.second;
        }
        if (total > 0.0) {
            for (auto& pair : entry.second) {
                pair.second /= total;
            }
        }
    }

    double total_added = 0.0;
    for (const auto& item : target_impurities) {
        elements_frac[item.first] += item.second;
        total_added += item.second;
    }

    if (!balance_element.empty()) {
        auto it = elements_frac.find(balance_element);
        if (it == elements_frac.end()) {
            throw std::invalid_argument("Balance element " + balance_element + " not found in material");
        }
        it->second -= total_added;
        if (it->second < 0.0) {
            throw std::invalid_argument("Impurity level too high: balance element " + balance_element + " would become negative");
        }
    } else {
        double total = 0.0;
        for (const auto& item : elements_frac) {
            total += item.second;
        }
        if (total > 0.0) {
            for (auto& item : elements_frac) {
                item.second /= total;
            }
        }
    }

    std::vector<NuclideComponent> new_nuclides;
    for (const auto& item : elements_frac) {
        const std::string& sym = item.first;
        double frac = item.second;
        if (frac <= 0.0) {
            continue;
        }

        auto existing = iso_distributions.find(sym);
        if (existing != iso_distributions.end()) {
            int z = data_manager_.get_z(sym);
            for (const auto& pair : existing->second) {
                double ratio = pair.second;
                if (ratio <= 0.0) {
                    continue;
                }
                if (is_atom) {
                    new_nuclides.push_back({z, pair.first, sym, 0.0, frac * ratio, 0.0, data_manager_.get_mass(z, pair.first)});
                } else {
                    new_nuclides.push_back({z, pair.first, sym, frac * ratio, 0.0, 0.0, data_manager_.get_mass(z, pair.first)});
                }
            }
            continue;
        }

        const ElementData* element_data = data_manager_.get_element(sym);
        if (!element_data) {
            int z = data_manager_.get_z(sym);
            if (z == 0) {
                continue;
            }
            if (is_atom) {
                new_nuclides.push_back({z, 0, sym, 0.0, frac, 0.0, 0.0});
            } else {
                new_nuclides.push_back({z, 0, sym, frac, 0.0, 0.0, 0.0});
            }
            continue;
        }

        if (is_atom) {
            double total_abd = 0.0;
            for (const auto& iso : element_data->isotopes) {
                total_abd += iso.abundance;
            }
            for (const auto& iso : element_data->isotopes) {
                double iso_a = 0.0;
                if (total_abd > 0.0) {
                    iso_a = frac * (iso.abundance / total_abd);
                }
                if (iso_a > 0.0) {
                    new_nuclides.push_back({element_data->Z, iso.A, sym, 0.0, iso_a, 0.0, iso.mass});
                }
            }
        } else {
            double avg_mass = 0.0;
            for (const auto& iso : element_data->isotopes) {
                avg_mass += iso.abundance * iso.mass;
            }
            for (const auto& iso : element_data->isotopes) {
                double iso_w = 0.0;
                if (avg_mass > 0.0) {
                    iso_w = frac * (iso.abundance * iso.mass / avg_mass);
                }
                if (iso_w > 0.0) {
                    new_nuclides.push_back({element_data->Z, iso.A, sym, iso_w, 0.0, 0.0, iso.mass});
                }
            }
        }
    }

    nuclides_ = std::move(new_nuclides);
    calculate_properties(is_atom);
}

std::string Material::to_json() const {
    std::ostringstream output;
    output << "{\n";
    output << "  \"name\": \"" << name_ << "\",\n";
    output << "  \"density\": " << density_ << ",\n";
    output << "  \"molecular_weight\": " << molecular_weight_ << ",\n";
    output << "  \"total_atom_density\": " << total_atom_density_ << ",\n";
    output << "  \"nuclides\": [\n";
    for (size_t i = 0; i < nuclides_.size(); ++i) {
        const auto& n = nuclides_[i];
        output << "    {\"Z\": " << n.Z << ", \"A\": " << n.A
               << ", \"element\": \"" << n.element << "\", "
               << "\"weight_frac\": " << n.weight_frac << ", "
               << "\"atom_frac\": " << n.atom_frac << ", "
               << "\"atom_density\": " << n.atom_density << "}";
        if (i + 1 < nuclides_.size()) {
            output << ",";
        }
        output << "\n";
    }
    output << "  ]\n";
    output << "}\n";
    return output.str();
}

void Material::to_json_file(const std::string& filepath) const {
    std::ofstream stream(filepath);
    stream << to_json();
}

Material Material::from_json_file(const std::string& filepath) {
    JsonValue root = parse_json_file(filepath);
    if (!root.is_object()) {
        throw std::invalid_argument("Invalid JSON material file");
    }
    const JsonObject& obj = root.as_object();
    std::string name = obj.at("name").as_string();
    double density = obj.at("density").as_number();
    Material material(name, density);
    material.molecular_weight_ = obj.at("molecular_weight").as_number();
    material.total_atom_density_ = obj.at("total_atom_density").as_number();
    for (const auto& item : obj.at("nuclides").as_array()) {
        const JsonObject& n = item.as_object();
        material.nuclides_.push_back({
            static_cast<int>(n.at("Z").as_number()),
            static_cast<int>(n.at("A").as_number()),
            n.at("element").as_string(),
            n.at("weight_frac").as_number(),
            n.at("atom_frac").as_number(),
            n.at("atom_density").as_number(),
            0.0
        });
    }
    return material;
}

std::string Material::get_summary() const {
    std::ostringstream output;
    output << "Material: " << name_ << "\n";
    if (density_ > 0.0) {
        output << "Density (g/cm3) = " << density_ << "\n";
    } else {
        output << "Density: Not defined\n";
    }
    output << "Molecular weight (g/mole) = " << molecular_weight_ << "\n";
    output << "Total atom density (atoms/b-cm) = " << total_atom_density_ << "\n";
    output << "\n";
    output << "Nuclide     | Weight Frac  | Atom Frac  | Atom Density\n";
    output << "------------------------------------------------------------\n";
    for (const auto& n : nuclides_) {
        output << n.element << "-" << n.A << "    | "
               << n.weight_frac << "    | "
               << n.atom_frac << "    | "
               << n.atom_density << "\n";
    }
    return output.str();
}

std::string Material::nuclide_name(const NuclideComponent& nuc) const {
    std::string symbol = data_manager_.get_symbol(nuc.Z);
    if (!symbol.empty()) {
        return symbol + std::to_string(nuc.A);
    }
    return std::to_string(nuc.Z) + "_" + std::to_string(nuc.A);
}

std::string Material::to_openmc_xml(int material_id) const {
    std::ostringstream output;
    output << "<material id=\"" << material_id << "\" name=\"" << name_ << "\" density=\"" << density_ << "\" target=\"g/cm3\">\n";
    output << std::fixed << std::setprecision(8);
    for (const auto& nuclide : nuclides_) {
        output << "  <nuclide name=\"" << nuclide_name(nuclide) << "\">" << nuclide.atom_frac << "</nuclide>\n";
    }
    output << "</material>\n";
    return output.str();
}

const std::vector<NuclideComponent>& Material::nuclides() const noexcept {
    return nuclides_;
}

double Material::total_atom_density() const noexcept {
    return total_atom_density_;
}

double Material::density() const noexcept {
    return density_;
}

} // namespace materiais
