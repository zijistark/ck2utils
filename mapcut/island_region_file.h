// -*- c++ -*-

#pragma once

#include "default_map.h"
#include "pdx/vfs.h"

#include <boost/filesystem.hpp>
#include <vector>
#include <string>
#include <memory>

namespace fs = boost::filesystem;
using std::unique_ptr;

namespace pdx { class block; }


class island_region_file {
private:
    typedef std::vector<unsigned int> uintvec_t;

    struct region {
        std::string name;
        uintvec_t   provinces;

        region(const std::string& _name) : name(_name) {}
        bool empty() const noexcept { return provinces.empty(); }
    };

    std::vector< unique_ptr<region> > _regions;

    unique_ptr<region> parse_region(const char* name, const pdx::block* block, const char* path);

public:
    island_region_file(const pdx::vfs& vfs, const default_map& dm);
    void write(const fs::path&);

    /* remove a province from the island_region_file */
    void delete_province(unsigned int province_id);
};
