
#include "default_map.h"
#include "error.h"

#include <cstdio>
#include <cassert>
#include <string>


typedef std::string string;


//const string ROOT_DIR("/cygdrive/d/SteamLibrary/steamapps/common/Crusader Kings II");
const string ROOT_DIR("/cygdrive/d/g/SWMH-BETA/SWMH");


int main(int argc, char** argv) {

    // TODO: parse arguments

    // TODO: load map/default.map

    // TODO: load map/definitions.csv (map color keys to province ID)

    // TODO: load map/provinces.bmp into province-indexed bitmap

    // TODO: draw output image

    try {
        default_map dm(ROOT_DIR + "/map/default.map");
    }
    catch (std::exception& e) {
        fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }

    return 0;
}
