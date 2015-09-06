
#include "default_map.h"
#include "error.h"

#include <cstdio>
#include <string>


//const std::string ROOT_DIR("/cygdrive/d/SteamLibrary/steamapps/common/Crusader Kings II");
const std::string ROOT_DIR("/cygdrive/d/g/SWMH-BETA/SWMH");


int main(int argc, char** argv) {

    try {
        default_map dm(ROOT_DIR);

    }
    catch (std::exception& e) {
        fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }

    return 0;
}

