export module materiais.models;

#include <string>
#include <vector>

export namespace materiais {

export struct IsotopeData {
    int A;
    double mass;
    double abundance;
};

export struct ElementData {
    int Z;
    std::string symbol;
    std::vector<IsotopeData> isotopes;
    std::vector<double> collprob;
};

export struct NuclideComponent {
    int Z;
    int A;
    std::string element;
    double weight_frac{0.0};
    double atom_frac{0.0};
    double atom_density{0.0};
    double mass{0.0};
};

export struct SubstitutionRule {
    int from_zaid;
    int to_zaid{-1};
    std::string reason;
};

} // namespace materiais
