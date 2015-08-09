
#include "province_map.h"
#include "error.h"

#include <cstdio>
#include <cstring>
#include <cerrno>
#include <cstdlib>
#include <cassert>


province_map::province_map(const default_map& dm)
    : _p_blocks(nullptr),
      _n_width(0),
      _n_height(0) {
    
    color2id_map_t color2id_map;
    fill_color2id_map(color2id_map, dm);


}


void province_map::fill_color2id_map(color2id_map_t& m, const default_map& dm) {

    const char* path = dm.definitions_path().c_str();
    FILE* f;

    if ( (f = fopen(path, "rb")) == nullptr )
        throw va_error("could not open file: %s: %s", strerror(errno), path);

    char buf[128];
    char* p = &buf[0];
    uint n_line = 0;
    
    if ( fgets(p, sizeof(buf), f) == nullptr ) // consume CSV header
        return;
    
    while ( fgets(p, sizeof(buf), f) != nullptr ) {

        ++n_line;

        char* n_str[4];
        n_str[0] = strtok(p, ";");

        for (uint x = 1; x < 4; ++x)
            n_str[x] = strtok(nullptr, ";");

        uint n[4];

        for (uint x = 0; x < 4; ++x) {
            char* p_end;
            long l = strtol(n_str[x], &p_end, 10);
            assert( *p_end == '\0' );
            n[x] = l;
        }

        uint32_t color = (n[3]<<24) | (n[2]<<16) | (n[1]<<8); // BGR
        m.emplace(color, (uint16_t)n[0]);

        if (n[0] == dm.max_province_id())
            break;
    }

    fclose(f);
}
