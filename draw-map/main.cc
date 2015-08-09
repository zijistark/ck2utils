
#include "default_map.h"
#include "province_map.h"
#include "error.h"

#include <cstdio>
#include <string>


//const std::string ROOT_DIR("/cygdrive/d/SteamLibrary/steamapps/common/Crusader Kings II");
const std::string ROOT_DIR("/cygdrive/d/g/SWMH-BETA/SWMH");


int main(int argc, char** argv) {

    // TODO: parse arguments

    // TODO: load map/provinces.bmp into province-indexed bitmap

    // TODO: draw output image

    try {
        default_map dm(ROOT_DIR);

        province_map pm(dm);
    }
    catch (std::exception& e) {
        fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }

    return 0;
}

