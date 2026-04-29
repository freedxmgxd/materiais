#pragma once

#include <string>
#include <vector>

namespace materiais {

struct IsotopeData {
    int A;
    double mass;
    double abundance;
};

struct ElementData {
    int Z;
    std::string symbol;
    std::vector<IsotopeData> isotopes;
    std::vector<double> collprob;
};

struct NuclideComponent {
    int Z;
    int A;
    std::string element;
    double weight_frac{0.0};
    double atom_frac{0.0};
    double atom_density{0.0};
    double mass{0.0};
};

struct SubstitutionRule {
    int from_zaid;
    int to_zaid{-1};
    std::string reason;
};

} // namespace materiais
