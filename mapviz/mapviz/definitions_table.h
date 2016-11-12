// -*- c++ -*-

#pragma once

#include "default_map.h"
#include "mod_vfs.h"
#include "color.h"

#include <boost/filesystem.hpp>

#include <string>
#include <vector>

namespace fs = boost::filesystem;

struct definitions_table {
    struct row {
        std::string name;
        rgba_color color;

        row(const std::string& n, const rgba_color& c)
        : name(n), color(c) { }
    };

    std::vector<row> row_vec;

    definitions_table(const mod_vfs&, const default_map&);
    void write(const fs::path& path);
};
