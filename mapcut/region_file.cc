
#include "region_file.h"
#include <pdx/parser.h>
#include <pdx/error.h>

#include <algorithm>
#include <fstream>
#include <cstring>

region_file::region_file(const fs::path& in_path) {
    const std::string spath = in_path.string();
    const char* path = spath.c_str();

    pdx::parser parse(path);

    for (const auto& s : *parse.root_block()) {
        /* looking for <region name> = { <BLOCK> } */
        if (!s.key().is_string())
            throw va_error("unexpected non-string value when expecting region name: %s", path);
        if (!s.value().is_block())
            throw va_error("expected region definition to follow string value '%s', but it did not: %s", s.key().as_string(), path);

        _regions.push_back( parse_region( s.key().as_string(), s.value().as_block(), path ) );
    }
}


unique_ptr<region_file::region> region_file::parse_region(const char* name, const pdx::block* block, const char* path) {
    auto p_region = std::make_unique<region>(name);

    for (const auto& s : *block) {
        /* looking for regions|duchies|counties|provinces = { <LIST> } */
        if (!s.key().is_string())
            throw va_error("unexpected non-string value when expecting element-type-specifier in region '%s': %s", name, path);
        if (!s.value().is_list())
            throw va_error("expected a list value-type for elements in region '%s': %s", name, path);

        const char* k = s.key().as_string();
        const pdx::list* v = s.value().as_list();

        if (strcmp(k, "regions") == 0) {
            for (const auto& e : *v) {
                if (!e.is_string())
                    throw va_error("unexpected non-string value when expecting region-element name in region '%s': %s", name, path);

                p_region->regions.emplace_back(e.as_string());
            }
        }
        else if (strcmp(k, "duchies") == 0) {
            for (const auto& e : *v) {
                if (!e.is_string())
                    throw va_error("unexpected non-string value when expecting duchy name in region '%s': %s", name, path);

                p_region->duchies.emplace_back(e.as_string());
            }
        }
        else if (strcmp(k, "counties") == 0) {
            for (const auto& e : *v) {
                if (!e.is_string())
                    throw va_error("unexpected non-string value when expecting county name in region '%s': %s", name, path);

                p_region->counties.emplace_back(e.as_string());
            }
        }
        else if (strcmp(k, "provinces") == 0) {
            for (const auto& e : *v) {
                if (!e.is_integer())
                    throw va_error("unexpected non-integer value when expecting province ID in region '%s': %s", name, path);
                if (e.as_integer() <= 0)
                    throw va_error("invalid province ID (must be positive and nonzero) in region '%s': %s", name, path);

                p_region->provinces.emplace_back(e.as_integer());
            }
        }
        else
            throw va_error("invalid element-type-specifier '%s' in region '%s': %s", k, name, path);
    }

    return p_region;
}


void region_file::delete_region(const std::string& region_name) {
    for (auto&& r : _regions) {
        if (r->name == region_name) {
            /* this is just here for completeness; we don't currently use this method
             * to actually empty regions, just remove references to emptied regions. */
            r->regions.clear();
            r->duchies.clear();
            r->counties.clear();
            r->provinces.clear();
            continue;
        }

        if (r->empty()) continue; // ignore empty regions

        // remove any reference to the deleted region from this region's region set
        auto& vec = r->regions;
        vec.erase(std::remove(vec.begin(), vec.end(), region_name), vec.end());

        if (r->empty()) // if this [potential] removal made the current region empty, then...
            delete_region(r->name); // it's time to recurse and do it again with this region
    }
}


void region_file::delete_duchy(const std::string& title) {
    for (auto&& r : _regions) {
        if (r->empty()) continue;

        auto& vec = r->duchies;
        vec.erase(std::remove(vec.begin(), vec.end(), title), vec.end());

        if (r->empty())
            delete_region(r->name);
    }
}


void region_file::delete_county(const std::string& title) {
    for (auto&& r : _regions) {
        if (r->empty()) continue;

        auto& vec = r->counties;
        vec.erase(std::remove(vec.begin(), vec.end(), title), vec.end());

        if (r->empty())
            delete_region(r->name);
    }
}


void region_file::delete_province(unsigned int province_id) {
    for (auto&& r : _regions) {
        if (r->empty()) continue;

        auto& vec = r->provinces;
        vec.erase(std::remove(vec.begin(), vec.end(), province_id), vec.end());

        if (r->empty())
            delete_region(r->name);
    }
}

static constexpr int num_digits(unsigned int n) { // obviously only applicable to province IDs
    return (n >= 10000) ? 5 :
           (n >= 1000) ? 4 :
           (n >= 100) ? 3 :
           (n >= 10) ? 2 : 1;
}

void region_file::write(const fs::path& out_path) {
    std::ofstream os(out_path.string());
    if (!os) throw std::runtime_error("Could not write to file: " + out_path.string());

    const int TAB_WIDTH = 8;
    const int MAX_LINE_LEN = 72;

    /* NOTE: we use \n instead of std::endl intentionally (UNIX format) */

    os << "# -*- ck2 -*-\n\n";

    for (auto&& pr : _regions) {
        if (pr->empty()) continue;

        os << pr->name << " = {\n"; // use UNIX EOL

        if (!pr->regions.empty()) {
            os << "\tregions = {\n";
            for (const auto& e : pr->regions) os << "\t\t" << e << "\n";
            os << "\t}\n";
        }
        if (!pr->duchies.empty()) {
            os << "\tduchies = {\n";
            for (const auto& e : pr->duchies) os << "\t\t" << e << "\n";
            os << "\t}\n";
        }
        if (!pr->counties.empty()) {
            os << "\tcounties = {\n";
            for (const auto& e : pr->counties) os << "\t\t" << e << "\n";
            os << "\t}\n";
        }
        if (!pr->provinces.empty()) {
            os << "\tprovinces = {\n";

            os << "\t\t";
            int cur_line_len = TAB_WIDTH*2;

            for (const auto& e : pr->provinces) {
                int e_len = num_digits(e) + 1; // assume a space following it

                if (e_len + cur_line_len > MAX_LINE_LEN) {
                    os << "\n\t\t";
                    cur_line_len = TAB_WIDTH*2;
                }

                os << e << " ";
                cur_line_len += e_len;
            }

            os << "\n\t}\n";
        }

        os << "}\n";
    }
}

