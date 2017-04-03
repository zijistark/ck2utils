
#include "island_region_file.h"
#include "pdx/parser.h"
#include "pdx/error.h"

#include <algorithm>
#include <fstream>

island_region_file::island_region_file(const pdx::vfs& vfs, const default_map& dm) {
    const std::string spath = vfs["map" / dm.island_region_path()].string();
    const char* path = spath.c_str();

    pdx::parser parse(path);

    for (const auto& s : *parse.root_block()) {
        /* looking for <region name> = { <BLOCK> } */
        if (!s.key().is_string())
            throw va_error("unexpected non-string value when expecting region name: %s", path);
        if (!s.value().is_block())
            throw va_error("expected region definition to follow string value '%s', but it did not: %s",
                           s.key().as_string(), path);

        _regions.push_back( parse_region( s.key().as_string(), s.value().as_block(), path ) );
    }
}


unique_ptr<island_region_file::region>
island_region_file::parse_region(const char* name, const pdx::block* block, const char* path) {
    auto p_region = std::make_unique<region>(name);

    for (const auto& s : *block) {
        /* looking for provinces = { <LIST> } */
        if (s.key() != "provinces")
            throw va_error("unexpected token when expecting 'provinces' in region '%s': %s", name, path);
        if (!s.value().is_list())
            throw va_error("expected a list value-type for province elements in region '%s': %s", name, path);

        const pdx::list* v = s.value().as_list();

        for (const auto& e : *v) {
            if (!e.is_integer())
                throw va_error("unexpected non-integer value when expecting province ID in region '%s': %s", name, path);
            if (e.as_integer() <= 0)
                throw va_error("invalid province ID (must be positive and nonzero) in region '%s': %s", name, path);

            p_region->provinces.emplace_back(e.as_integer());
        }
    }

    return p_region;
}


void island_region_file::delete_province(unsigned int province_id) {
    for (auto&& pr : _regions) {
        if (pr->empty()) continue;
        auto& vec = pr->provinces;
        vec.erase(std::remove(vec.begin(), vec.end(), province_id), vec.end());
    }
}


static int num_digits(unsigned int n) {
    return (n >= 10000) ? 5 :
           (n >= 1000) ? 4 :
           (n >= 100) ? 3 :
           (n >= 10) ? 2 : 1;
}


void island_region_file::write(const fs::path& out_path) {
    std::ofstream os(out_path.string());
    if (!os) throw std::runtime_error("could not write to file: " + out_path.string());

    /* NOTE: we use \n instead of std::endl intentionally (UNIX format) */

    os << "# -*- ck2 -*-\n\n";

    for (auto&& pr : _regions) {
        if (pr->empty()) continue;

        os << pr->name << " = {\n";
        os << "\tprovinces = {\n";

        const int TAB_WIDTH = 8;
        const int MAX_LINE_LEN = 80;

        os << "\t\t";
        int cur_line_len = TAB_WIDTH*2;

        for (const auto& e : pr->provinces) {
            int d = num_digits(e) + 1; // assume a space following it

            if (d + cur_line_len > MAX_LINE_LEN) {
                os << "\n\t\t";
                cur_line_len = TAB_WIDTH*2;
            }

            os << e << " ";
            cur_line_len += d;
        }

        os << "\n\t}\n";
        os << "}\n";
    }
}

