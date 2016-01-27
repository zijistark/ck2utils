// -*- c++ -*-

#ifndef _MDH_DEFINITIONS_TABLE_H_
#define _MDH_DEFINITIONS_TABLE_H_

#include "default_map.h"

#include <boost/filesystem.hpp>

#include <cstdint>
#include <string>
#include <vector>

namespace fs = boost::filesystem;

class definitions_table {

public:

    struct row {
        std::string name;
        uint8_t red;
        uint8_t green;
        uint8_t blue;

        row(const std::string& n, uint8_t r, uint8_t g, uint8_t b)
        : name(n), red(r), green(g), blue(b) { }
    };

    std::vector<row> row_vec;

    definitions_table(const default_map&);
    void write(const fs::path& path);
};


#endif
