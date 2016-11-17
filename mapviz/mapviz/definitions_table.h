// -*- c++ -*-

#pragma once

#include "default_map.h"
#include "mod_vfs.h"
#include "color.h"

#include <boost/filesystem.hpp>

#include <string>
#include <vector>

typedef unsigned int uint;
namespace fs = boost::filesystem;

class definitions_table {
public:
    struct row {
        std::string name;
        rgb color;
        row() = delete; // a default row in definition.csv makes no sense
        row(const std::string& n, const rgb& c) : name(n), color(c) { }
    };

private:
    typedef std::vector<row> vec_t;
    vec_t vec;

public:
    definitions_table(const mod_vfs&, const default_map&);
    void write(const fs::path& path);

    size_t size() const noexcept { return vec.size() - 1; }

    row& operator[](uint id) noexcept { return vec[id]; }
    const row& operator[](uint id) const noexcept { return vec[id]; }

    vec_t::iterator begin() noexcept { return vec.begin(); }
    vec_t::const_iterator begin() const noexcept { return vec.cbegin(); }
    vec_t::iterator end() noexcept { return vec.end(); }
    vec_t::const_iterator end() const noexcept { return vec.cend(); }
};
