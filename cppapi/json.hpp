#pragma once

#include <map>
#include <string>
#include <variant>
#include <vector>

namespace materiais {

struct JsonValue;
using JsonObject = std::map<std::string, JsonValue>;
using JsonArray = std::vector<JsonValue>;

struct JsonValue {
    std::variant<std::nullptr_t, bool, double, std::string, JsonArray, JsonObject> value;

    bool is_null() const noexcept { return std::holds_alternative<std::nullptr_t>(value); }
    bool is_bool() const noexcept { return std::holds_alternative<bool>(value); }
    bool is_number() const noexcept { return std::holds_alternative<double>(value); }
    bool is_string() const noexcept { return std::holds_alternative<std::string>(value); }
    bool is_array() const noexcept { return std::holds_alternative<JsonArray>(value); }
    bool is_object() const noexcept { return std::holds_alternative<JsonObject>(value); }

    const JsonObject& as_object() const { return std::get<JsonObject>(value); }
    const JsonArray& as_array() const { return std::get<JsonArray>(value); }
    const std::string& as_string() const { return std::get<std::string>(value); }
    double as_number() const { return std::get<double>(value); }
    bool as_bool() const { return std::get<bool>(value); }
};

JsonValue parse_json(const std::string& text);
JsonValue parse_json_file(const std::string& path);

} // namespace materiais
