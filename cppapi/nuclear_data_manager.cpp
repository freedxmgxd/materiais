export module materiais.nuclear_data_manager;

#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <map>
#include <array>
#include <vector>

import materiais.models;
import materiais.json;

export namespace materiais {

NuclearDataManager::NuclearDataManager(std::string data_dir)
    : data_dir_(std::move(data_dir)) {
    if (data_dir_.empty()) {
        data_dir_ = std::string(__FILE__);
        auto pos = data_dir_.find_last_of("/");
        if (pos != std::string::npos) {
            data_dir_.erase(pos + 1);
        }
        data_dir_ += "../nuclear_data";
    }
    load_all();
}

const ElementData* NuclearDataManager::get_element(const std::string& symbol) const noexcept {
    auto it = elements_.find(symbol);
    return it == elements_.end() ? nullptr : &it->second;
}

double NuclearDataManager::get_mass(int z, int a) const noexcept {
    int key = z * 1000 + a;
    auto it = atomic_masses_.find(key);
    return it == atomic_masses_.end() ? 0.0 : it->second;
}

std::string NuclearDataManager::get_symbol(int z) const noexcept {
    if (z > 0 && z < static_cast<int>(periodic_table_.size())) {
        return periodic_table_[z];
    }
    return {};
}

int NuclearDataManager::get_z(const std::string& symbol) const noexcept {
    for (int index = 1; index < static_cast<int>(periodic_table_.size()); ++index) {
        if (periodic_table_[index] == symbol) {
            return index;
        }
    }
    return 0;
}

const SubstitutionRule* NuclearDataManager::get_substitution(int from_zaid) const noexcept {
    auto it = substitutions_.find(from_zaid);
    return it == substitutions_.end() ? nullptr : &it->second;
}

void NuclearDataManager::load_all() {
    load_periodic_table();
    load_natural_abundances();
    load_atomic_masses();
    load_substitutions();
}

void NuclearDataManager::load_periodic_table() {
    auto root = parse_json_file(data_dir_ + "/periodic_table.json");
    if (!root.is_object()) {
        throw std::runtime_error("Invalid periodic_table.json");
    }
    for (const auto& pair : root.as_object()) {
        const std::string& symbol = pair.first;
        const JsonValue& entry = pair.second;
        int z = 0;
        if (entry.is_number()) {
            z = static_cast<int>(entry.as_number());
        } else if (entry.is_object()) {
            z = static_cast<int>(entry.as_object().at("Z").as_number());
        }
        if (z > 0 && z < static_cast<int>(periodic_table_.size())) {
            periodic_table_[z] = symbol;
        }
    }
}

void NuclearDataManager::load_natural_abundances() {
    auto root = parse_json_file(data_dir_ + "/natural_abundances.json");
    if (!root.is_object()) {
        throw std::runtime_error("Invalid natural_abundances.json");
    }
    for (const auto& pair : root.as_object()) {
        const std::string& symbol = pair.first;
        const auto& entry = pair.second.as_object();
        ElementData element;
        element.Z = static_cast<int>(entry.at("Z").as_number());
        element.symbol = symbol;
        for (const auto& item : entry.at("isotopes").as_array()) {
            const auto& iso = item.as_object();
            IsotopeData data;
            data.A = static_cast<int>(iso.at("A").as_number());
            data.mass = iso.at("mass").as_number();
            data.abundance = iso.at("abundance").as_number();
            element.isotopes.push_back(data);
        }
        for (const auto& value : entry.at("collprob").as_array()) {
            element.collprob.push_back(value.as_number());
        }
        elements_.emplace(symbol, std::move(element));
    }
}

void NuclearDataManager::load_atomic_masses() {
    auto root = parse_json_file(data_dir_ + "/atomic_masses.json");
    if (!root.is_object()) {
        throw std::runtime_error("Invalid atomic_masses.json");
    }
    for (const auto& pair : root.as_object()) {
        const auto& entry = pair.second.as_object();
        int z = static_cast<int>(entry.at("Z").as_number());
        for (const auto& item : entry.at("isotopes").as_array()) {
            const auto& iso = item.as_object();
            int a = static_cast<int>(iso.at("A").as_number());
            int key = z * 1000 + a;
            atomic_masses_[key] = iso.at("mass").as_number();
        }
    }
}

void NuclearDataManager::load_substitutions() {
    auto root = parse_json_file(data_dir_ + "/xs_substitutions.json");
    if (!root.is_object()) {
        return;
    }
    const auto& array = root.as_object().at("substitutions").as_array();
    for (const auto& item : array) {
        const auto& entry = item.as_object();
        int from_zaid = parse_zaid(entry.at("from").as_string());
        int to_zaid = -1;
        if (!entry.at("to").is_null()) {
            to_zaid = parse_zaid(entry.at("to").as_string());
        }
        SubstitutionRule rule;
        rule.from_zaid = from_zaid;
        rule.to_zaid = to_zaid;
        if (!entry.at("reason").is_null()) {
            rule.reason = entry.at("reason").as_string();
        }
        substitutions_.emplace(from_zaid, std::move(rule));
    }
}

int NuclearDataManager::parse_zaid(const std::string& zaid_str) const {
    size_t sep = zaid_str.find('-');
    if (sep != std::string::npos) {
        std::string symbol = zaid_str.substr(0, sep);
        int A = std::stoi(zaid_str.substr(sep + 1));
        int Z = get_z(symbol);
        return Z * 1000 + A;
    }
    return std::stoi(zaid_str);
}

} // namespace materiais
