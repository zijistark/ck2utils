

#include "definitions_table.h"
#include "error.h"

#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cerrno>

/*
 NOTE: I need to get rid of this cstdio crap, but I _REALLY_
       need to get rid of `strtok` usage here.
 */
definitions_table::definitions_table(const default_map& dm) {

    const char* path = dm.definitions_path().c_str();
    FILE* f;

    if ( (f = fopen(path, "rb")) == nullptr )
        throw va_error("could not open file: %s: %s", strerror(errno), path);

    char buf[256];
    uint n_line = 0;

    if ( fgets(&buf[0], sizeof(buf), f) == nullptr ) // consume CSV header
        throw va_error("definitions file lacks at least 1 line of text: %s", path);

    ++n_line;

    while ( fgets(&buf[0], sizeof(buf), f) != nullptr ) {

        ++n_line;

        char* p = &buf[0];

        if (*p == '#')
            continue;

        char* n_str[5];
        n_str[0] = strtok(p, ";");

        for (uint x = 1; x < 5; ++x)
            n_str[x] = strtok(nullptr, ";");

        uint n[4];
        char* p_end;

        for (uint x = 0; x < 4; ++x) {
            n[x] = strtol(n_str[x], &p_end, 10);
            assert( *p_end == '\0' );
        }

        if (n[0] != n_line-1)
            throw va_error("unexpected province ID %u on line %u: %s", n[0], n_line, path);

        row_vec.emplace_back((strcmp(n_str[4], "x") == 0) ? "" : n_str[4], // die, strtok, die!
                             n[1], n[2], n[3]);

        if (n[0] == dm.max_province_id())
            break;
    }

    fclose(f);

    if (row_vec.empty())
        throw va_error("definitions file lacked any data: %s", path);

    if (row_vec.size() != dm.max_province_id())
        throw va_error("definitions file only had %u rows for a map with %u provinces: %s",
                       row_vec.size(), dm.max_province_id(), path);
}


void definitions_table::write(const std::string& spath) {

    const char* path = spath.c_str();
    FILE* f;

    if ( (f = fopen(path, "wb")) == nullptr )
        throw va_error("could not open file: %s: %s", strerror(errno), path);

    fprintf(f, "province;red;green;blue;x;x\n");

    for (uint i = 0; i < row_vec.size(); ++i) {
        const row& r = row_vec[i];
        fprintf(f, "%u;%hhu;%hhu;%hhu;%s;x\n",
                i+1, r.red, r.green, r.blue, r.name.c_str());
    }

    fclose(f);
}
