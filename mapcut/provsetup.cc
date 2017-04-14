

#include "provsetup.h"
#include <pdx/parser.h>
#include <pdx/error.h>

#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cerrno>


provsetup::provsetup(const fs::path& in_path) {

    const std::string spath = in_path.string();
    const char* path = spath.c_str();
    pdx::parser parse(path);

    int id = 1;

    for (auto&& s : *parse.root_block()) {
        if (!s.key().is_integer())
            throw va_error("province_setup: unexpected non-integer where province ID %d expected: %s", id, path);

        const int prvid = s.key().as_integer();

        if (prvid != id)
            throw va_error("province_setup: unexpected province ID %d found where ID %d expected: %s", prvid, id, path);

        if (!s.value().is_block())
            throw va_error("province_setup: unexpected non-block value for province ID %d: %s", id, path);

        const pdx::block* p_block = s.value().as_block();
        row r;

        for (auto&& ps : *p_block) {
            if (!ps.key().is_string())
                throw va_error("province_setup: unexpected non-string key inside province %d: %s", id, path);

            if (ps.key() == "title") {
                assert( ps.value().is_string() );
                r.title = ps.value().as_string();
            }
            else if (ps.key() == "max_settlements") {
                assert( ps.value().is_integer() );
                r.max_settlements = ps.value().as_integer();
            }
            else if (ps.key() == "terrain") {
                assert( ps.value().is_string() );
                r.terrain = ps.value().as_string();
            }
        }

        if (r.title.empty())
            r.max_settlements = 7;
        else
            assert( pdx::title_tier(r.title.c_str()) == pdx::TIER_COUNT );

        if (r.max_settlements <= 0)
            throw va_error("province_setup: invalid max_settlements defined for province %d: %s", id, path);

        if (r.terrain.empty())
            throw va_error("province_setup: no terrain type defined for province %d: %s", id, path);

        row_vec.emplace_back(r);
        ++id;
    }
}


void provsetup::write(const fs::path& out_path) {

    const std::string spath = out_path.string();
    const char* path = spath.c_str();
    FILE* f;

    if ( (f = fopen(path, "wb")) == nullptr )
        throw va_error("could not write to file: %s: %s",
                       strerror(errno), path);

    unsigned int id = 0;

    for (auto&& r : row_vec) {

        fprintf(f, "%u = {\r\n", ++id);

        if (r.title.empty()) {
            fprintf(f, "\tmax_settlements=7\r\n");
        }
        else {
            fprintf(f, "\ttitle=%s\r\n", r.title.c_str());
            fprintf(f, "\tmax_settlements=%d\r\n", r.max_settlements);
        }

        fprintf(f, "\tterrain=%s\r\n", r.terrain.c_str());
        fprintf(f, "}\r\n");
    }

    fclose(f);
}
