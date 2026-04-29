#pragma once

#include <functional>
#include <map>
#include <string>
#include <vector>
#include "material.hpp"

namespace materiais {

class MaterialFactory {
public:
    using MaterialCreator = std::function<Material(const std::map<std::string, double>&)>;

    MaterialFactory() = default;
    static Material create(const std::string& material_name, const std::map<std::string, double>& params);
    Material create_from_json(const std::string& filepath) const;
    Material create_with_substitution(const Material& material, int from_zaid, int to_zaid) const;
    static std::vector<std::string> list_materials();
    static void register_material(const std::string& name, MaterialCreator creator);
    static bool unregister_material(const std::string& name);
};

} // namespace materiais
