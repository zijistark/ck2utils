
#include "default_map.h"
#include "error.h"

#include <cstdio>
#include <cassert>
#include <string>
#include <cstring>
#include <cerrno>
#include <cstdint>
#include <cstdlib>
#include <unordered_map>


//const std::string ROOT_DIR("/cygdrive/d/SteamLibrary/steamapps/common/Crusader Kings II");
const std::string ROOT_DIR("/cygdrive/d/g/SWMH-BETA/SWMH");


typedef std::unordered_map<uint32_t, uint16_t> color2id_map_t;
void fill_color2id_map(color2id_map_t&, const std::string& definitions_path, uint max_province_id);


int main(int argc, char** argv) {

    // TODO: parse arguments

    // TODO: load map/provinces.bmp into province-indexed bitmap

    // TODO: draw output image

    try {
        default_map dm(ROOT_DIR + "/map/default.map");
        
        color2id_map_t color2id_map;
        fill_color2id_map(color2id_map, ROOT_DIR + "/map/" + dm.definitions_filename(), dm.max_province_id());

    }
    catch (std::exception& e) {
        fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }

    return 0;
}


void fill_color2id_map(color2id_map_t& m, const std::string& definitions_path, uint max_prov_id) {
    FILE* f;

    if ( (f = fopen(definitions_path.c_str(), "rb")) == 0 )
        throw va_error("could not open file: %s: %s", strerror(errno), definitions_path.c_str());

    char buf[128];
    char* p = &buf[0];
    uint n_line = 0;
    
    if ( fgets(p, sizeof(buf), f) == NULL ) // consume CSV header
        return;
    
    while ( fgets(p, sizeof(buf), f) != NULL ) {

        ++n_line;

        char* n_str[4];
        n_str[0] = strtok(p, ";");

        for (uint x = 1; x < 4; ++x) {
            n_str[x] = strtok(NULL, ";");
            assert(n_str[x] != NULL);
        }

        uint n[4];

        for (uint x = 0; x < 4; ++x) {
            char* p_end;
            long l = strtol(n_str[x], &p_end, 10);
            assert( *p_end == '\0' );
            n[x] = l;
        }

        uint32_t color = (n[3]<<24) | (n[2]<<16) | (n[1]<<8); // BGR
        m.emplace(color, (uint16_t)n[0]);

        if (n[0] == max_prov_id)
            break;
    }

    fclose(f);
}
