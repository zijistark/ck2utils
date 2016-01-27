
#include "error.h"
#include "default_map.h"
#include "province_map.h"
#include "bmp_format.h"

#include <boost/filesystem.hpp>

#include <cstdio>
#include <cerrno>
#include <cstring>
#include <cassert>

using namespace boost::filesystem;


const path ROOT_PATH("D:/SteamLibrary/steamapps/common/Crusader Kings II");
//const path ROOT_PATH("D:/g/SWMH-BETA/SWMH");
const path OUT_PATH("00_province_setup.txt");


int main(int argc, char** argv) {

    path output_path = OUT_PATH;

    if (argc >= 2)
        output_path = path(argv[1]);

    try {
        default_map dm(ROOT_PATH);
        definitions_table def_tbl(dm);
        province_map pm(dm, def_tbl);
    }
    catch (std::exception& e) {
        fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }

    return 0;
}
