export module materiais.json;

#include <cctype>
#include <charconv>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <variant>
#include <vector>

export namespace materiais {

export struct JsonValue;
export using JsonObject = std::map<std::string, JsonValue>;
export using JsonArray = std::vector<JsonValue>;

export struct JsonValue {
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

export inline void skip_space(const std::string& text, size_t& index) {
    while (index < text.size() && std::isspace(static_cast<unsigned char>(text[index]))) {
        ++index;
    }
}

export inline std::string parse_string(const std::string& text, size_t& index) {
    std::string value;
    ++index;
    while (index < text.size()) {
        char c = text[index++];
        if (c == '"') {
            return value;
        }
        if (c == '\\' && index < text.size()) {
            char esc = text[index++];
            switch (esc) {
                case '"': value.push_back('"'); break;
                case '\\': value.push_back('\\'); break;
                case '/': value.push_back('/'); break;
                case 'b': value.push_back('\b'); break;
                case 'f': value.push_back('\f'); break;
                case 'n': value.push_back('\n'); break;
                case 'r': value.push_back('\r'); break;
                case 't': value.push_back('\t'); break;
                default: value.push_back(esc); break;
            }
            continue;
        }
        value.push_back(c);
    }
    return value;
}

export inline double parse_number(const std::string& text, size_t& index) {
    size_t start = index;
    if (text[index] == '-') {
        ++index;
    }
    while (index < text.size() && std::isdigit(static_cast<unsigned char>(text[index]))) {
        ++index;
    }
    if (index < text.size() && text[index] == '.') {
        ++index;
        while (index < text.size() && std::isdigit(static_cast<unsigned char>(text[index]))) {
            ++index;
        }
    }
    if (index < text.size() && (text[index] == 'e' || text[index] == 'E')) {
        ++index;
        if (text[index] == '+' || text[index] == '-') {
            ++index;
        }
        while (index < text.size() && std::isdigit(static_cast<unsigned char>(text[index]))) {
            ++index;
        }
    }
    double value = 0.0;
    std::from_chars(text.data() + start, text.data() + index, value);
    return value;
}

export inline JsonValue parse_value(const std::string& text, size_t& index);

export inline JsonArray parse_array(const std::string& text, size_t& index) {
    JsonArray array;
    ++index;
    skip_space(text, index);
    if (index < text.size() && text[index] == ']') {
        ++index;
        return array;
    }
    while (index < text.size()) {
        array.push_back(parse_value(text, index));
        skip_space(text, index);
        if (index < text.size() && text[index] == ',') {
            ++index;
            skip_space(text, index);
            continue;
        }
        if (index < text.size() && text[index] == ']') {
            ++index;
            break;
        }
        break;
    }
    return array;
}

export inline JsonObject parse_object(const std::string& text, size_t& index) {
    JsonObject object;
    ++index;
    skip_space(text, index);
    if (index < text.size() && text[index] == '}') {
        ++index;
        return object;
    }
    while (index < text.size()) {
        skip_space(text, index);
        std::string key = parse_string(text, index);
        skip_space(text, index);
        if (index < text.size() && text[index] == ':') {
            ++index;
        }
        skip_space(text, index);
        object.emplace(key, parse_value(text, index));
        skip_space(text, index);
        if (index < text.size() && text[index] == ',') {
            ++index;
            continue;
        }
        if (index < text.size() && text[index] == '}') {
            ++index;
            break;
        }
    }
    return object;
}

export inline JsonValue parse_value(const std::string& text, size_t& index) {
    skip_space(text, index);
    if (index >= text.size()) {
        return JsonValue{nullptr};
    }
    char c = text[index];
    if (c == '{') {
        return JsonValue{parse_object(text, index)};
    }
    if (c == '[') {
        return JsonValue{parse_array(text, index)};
    }
    if (c == '"') {
        return JsonValue{parse_string(text, index)};
    }
    if (std::isdigit(static_cast<unsigned char>(c)) || c == '-') {
        return JsonValue{parse_number(text, index)};
    }
    if (text.compare(index, 4, "true") == 0) {
        index += 4;
        return JsonValue{true};
    }
    if (text.compare(index, 5, "false") == 0) {
        index += 5;
        return JsonValue{false};
    }
    if (text.compare(index, 4, "null") == 0) {
        index += 4;
        return JsonValue{nullptr};
    }
    return JsonValue{nullptr};
}

export inline JsonValue parse_json(const std::string& text) {
    size_t index = 0;
    return parse_value(text, index);
}

export inline JsonValue parse_json_file(const std::string& path) {
    std::ifstream stream(path);
    std::ostringstream buffer;
    buffer << stream.rdbuf();
    return parse_json(buffer.str());
}

} // namespace materiais
