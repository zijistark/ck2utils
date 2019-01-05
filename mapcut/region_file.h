// -*- c++ -*-

#pragma once

#include <ck2/filesystem.h>
#include <vector>
#include <string>
#include <memory>

namespace fs = ck2::fs;
using std::unique_ptr;

namespace ck2 { class block; }


class region_file {
private:
    /* NOTE: these would ideally be std::unordered_set or std::set, but we want to preserve the
     * input order, and these containers are quite small in practice, so we KISS here and just
     * use vectors. */
    typedef std::vector<std::string> strvec_t;
    typedef std::vector<unsigned int> uintvec_t;

    struct region {
        std::string name;
        strvec_t    regions;
        strvec_t    duchies;
        strvec_t    counties;
        uintvec_t   provinces;

        region(const std::string& _name) : name(_name) {}
        bool empty() const noexcept {
            return regions.empty() && duchies.empty() && counties.empty() && provinces.empty();
        }
    };

    std::vector< unique_ptr<region> > _regions;

    unique_ptr<region> parse_region(const char* name, const ck2::block* block, const char* path);

public:
    region_file(const fs::path&);
    void write(const fs::path&);

    void delete_region(const std::string& region);
    void delete_duchy(const std::string& title);
    void delete_county(const std::string& title);
    void delete_province(unsigned int province_id);
};
