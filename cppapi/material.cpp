#include "material.hpp"

#include <cmath>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>

#include "json.hpp"
#include <map>

namespace materiais {

Material::Material(std::string name, double density)
        : description_(std::move(name)),
            name_("material"),
            density_(density),
            molecular_weight_(0.0),
            total_atom_density_(0.0) {  // Will be set to compact name after nuclides are added
}

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
    
    // Generate compact isotope-based name after properties are calculated
    name_ = generate_compact_isotope_name();
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
    // Generate compact isotope-based name from loaded nuclides
    material.name_ = material.generate_compact_isotope_name();
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

std::string Material::generate_compact_isotope_name() const {
    if (nuclides_.empty()) {
        return "empty";
    }

    // Group nuclides by element (Z) and sum atom fractions
    std::map<int, std::pair<std::string, double>> element_fracs;
    for (const auto& nuc : nuclides_) {
        std::string symbol = data_manager_.get_symbol(nuc.Z);
        if (symbol.empty()) symbol = "X";  // fallback
        auto &entry = element_fracs[nuc.Z];
        if (entry.first.empty()) entry.first = symbol;
        entry.second += nuc.atom_frac;
    }

    // Sort elements by total atom fraction (descending)
    std::vector<std::pair<double, std::string>> sorted_elements;
    for (const auto& kv : element_fracs) {
        sorted_elements.push_back({kv.second.second, kv.second.first});
    }
    std::sort(sorted_elements.begin(), sorted_elements.end(),
              [](const auto& a, const auto& b) { return a.first > b.first; });

    // Build base name from top elements (up to 3)
    std::ostringstream base_ss;
    const int max_elements = 3;
    int taken = std::min(static_cast<int>(sorted_elements.size()), max_elements);
    for (int i = 0; i < taken; ++i) {
        if (i) base_ss << '_';
        base_ss << sorted_elements[i].second;
    }
    std::string base = base_ss.str();

    // Build a simple fingerprint from density and nuclide composition
    std::ostringstream fp_ss;
    fp_ss << std::fixed << std::setprecision(4) << density_;
    for (const auto& nuc : nuclides_) {
        fp_ss << "_" << nuc.Z << nuc.A << std::setprecision(2) << nuc.atom_frac;
    }
    std::string fp = fp_ss.str();

    // Simple hash: CRC16-like
    unsigned short tag = 0xFFFF;
    for (char c : fp) {
        tag ^= static_cast<unsigned char>(c);
        for (int i = 0; i < 8; ++i) {
            if (tag & 1) tag = (tag >> 1) ^ 0xA001;
            else tag >>= 1;
        }
    }
    std::ostringstream tag_ss;
    tag_ss << std::hex << std::nouppercase << std::setfill('0') << std::setw(4) << tag;

    std::string compact = base + "_" + tag_ss.str();

    // Ensure compact name length stays small (under 20-22 chars)
    if (compact.length() > 22) {
        compact = compact.substr(0, 22);
    }
    return compact;
}

std::string Material::to_openmc_xml(int material_id) const {
    std::ostringstream output;
    output << "<material id=\"" << material_id << "\" name=\"" << name_ << "\" target=\"g/cm3\">\n";
    if (!description_.empty()) {
        output << "  <description>" << description_ << "</description>\n";
    }
    output << "  <density units=\"g/cm3\" value=\"" << density_ << "\" />\n";
    output << std::fixed << std::setprecision(8);
    for (const auto& nuclide : nuclides_) {
        output << "  <nuclide name=\"" << nuclide_name(nuclide) << "\" ao=\"" << (nuclide.atom_frac * 100.0) << "\" />\n";
    }
    output << "</material>\n";
    return output.str();
}

std::string Material::to_openmc_materials_xml(const std::vector<Material>& materials,
                                              const std::string& cross_sections_xml,
                                              int starting_id) {
    std::ostringstream output;
    output << "<?xml version=\"1.0\"?>\n";
    output << "<materials cross_sections=\"" << cross_sections_xml << "\">\n";
    int id = starting_id;
    for (const auto& material : materials) {
        output << material.to_openmc_xml(id++);
    }
    output << "</materials>\n";
    return output.str();
}

bool Material::write_openmc_materials_xml_file(const std::filesystem::path& filepath,
                                              const std::vector<Material>& materials,
                                              const std::string& cross_sections_xml,
                                              int starting_id) {
    // Deduplicate materials: keep only unique compositions
    std::vector<Material> unique_materials;
    for (const auto& mat : materials) {
        bool is_duplicate = false;
        for (const auto& unique : unique_materials) {
            if (mat.is_same_composition(unique)) {
                is_duplicate = true;
                break;
            }
        }
        if (!is_duplicate) {
            unique_materials.push_back(mat);
        }
    }
    
    std::ofstream out(filepath);
    if (!out) {
        return false;
    }
    out << to_openmc_materials_xml(unique_materials, cross_sections_xml, starting_id);
    return static_cast<bool>(out);
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

std::string Material::name() const noexcept {
    return name_;
}

bool Material::is_same_composition(const Material& other) const noexcept {
    // Check density (within 1e-6 tolerance)
    if (std::abs(density_ - other.density_) > 1e-6) {
        return false;
    }
    
    // Check number of nuclides
    if (nuclides_.size() != other.nuclides_.size()) {
        return false;
    }
    
    // Check each nuclide (Z, A, and atom fraction within 1e-8 tolerance)
    for (size_t i = 0; i < nuclides_.size(); ++i) {
        const auto& n1 = nuclides_[i];
        const auto& n2 = other.nuclides_[i];
        if (n1.Z != n2.Z || n1.A != n2.A || 
            std::abs(n1.atom_frac - n2.atom_frac) > 1e-8) {
            return false;
        }
    }
    
    return true;
}

} // namespace materiais
