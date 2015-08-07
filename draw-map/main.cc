
#include "error.h"
#include "pdx.h"

#include <cstdio>
#include <string>


typedef std::string string;


const string ROOT_DIR("/cygdrive/d/SteamLibrary/steamapps/common/Crusader Kings II");


int main(int argc, char** argv) {

    // TODO: parse arguments

    // TODO: load map/default.map

    // TODO: load map/definitions.csv (map color keys to province ID)

    // TODO: load map/provinces.bmp into province-indexed bitmap

    // TODO: draw output image

    try {

        string dm_path = ROOT_DIR + "/map/default.map";
        pdx::plexer lex(dm_path.c_str());

        pdx::block* dm_root = new pdx::block(lex, true);

    }
    catch (std::exception& e) {
        fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }

    return 0;
}
