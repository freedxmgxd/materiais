load("@rules_cc//cc:cc_binary.bzl", "cc_binary")
load("@rules_cc//cc:cc_library.bzl", "cc_library")

cc_library(
    name = "materiais_cppapi",
    srcs = [
        "models.cpp",
        "json.cpp",
        "material.cpp",
        "nuclear_data_manager.cpp",
        "material_factory.cpp",
    ],
    hdrs = [
        "material.hpp",
        "nuclear_data_manager.hpp",
        "models.hpp",
        "material_factory.hpp",
        "json.hpp",
    ],
    copts = ["-std=c++20"],
    visibility = ["//visibility:public"],
)

cc_binary(
    name = "material_example",
    srcs = ["example.cpp"],
    copts = ["-std=c++20"],
    deps = [":materiais_cppapi"],
    visibility = ["//visibility:public"],
)
