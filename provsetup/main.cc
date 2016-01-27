
#include "error.h"
#include "default_map.h"
#include "province_map.h"
#include "pdx.h"
#include "bmp_format.h"

#include <boost/filesystem.hpp>

#include <cstdio>
#include <cerrno>
#include <cstring>
#include <cassert>

using namespace boost::filesystem;


const path VROOT_PATH("D:/SteamLibrary/steamapps/common/Crusader Kings II");
const path ROOT_PATH(VROOT_PATH);
//const path ROOT_PATH("D:/g/SWMH-BETA/SWMH");
const path OUT_PATH("00_province_setup.txt");


struct province {
    uint id;
    std::string county; // empty when N/A (sea zones, wasteland, etc.)
    int max_settlements; // -1 for undefined
    int terrain_id; // before automatic terrain assignment, -1 for no explicit terrain

    uint* p_terrain_px_array; // array of terrain-type pixel counts, indexed by terrain type ID

    province() : id(0), max_settlements(-1), terrain_id(-1), p_terrain_px_array(nullptr) { }
};


void read_province_history(const default_map&, const definitions_table&, std::vector<province>&);


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


void read_province_history(const default_map& dm, const definitions_table& def_tbl, std::vector<province>& pr_vec) {

    path hist_root = ROOT_PATH / "history/provinces";
    path hist_vroot = VROOT_PATH / "history/provinces";

    uint id = 0;
    char filename[256];

    for (auto&& def : def_tbl.row_vec) {
        ++id;

        if (def.name.empty()) // wasteland | external
            continue;
        if (dm.id_is_seazone(id)) // sea | major river
            continue;

        sprintf(filename, "%u - %s.txt", id, def.name.c_str());

        path hist_file = hist_root / filename;

        if (!exists(hist_file)) {
            path hist_vfile = hist_vroot / filename;

            if (!exists(hist_vfile))
                throw va_error("could not find province history file implied by definitions table: %s", filename);
            else
                hist_file = hist_vfile;
        }

        const char* county = nullptr;

        pdx::plexer lex(hist_file.c_str());
        pdx::block doc(lex, true);

        for (auto&& s : doc.stmt_list) {
            if (s.key_eq("title")) {
                county = s.val.as_title();
                assert( pdx::title_tier(county) == pdx::TIER_COUNT );
            }
        }

        if (county == nullptr) {
            /* history file contained no title assignment.  it was probably
               blank (for a wasteland or something). we may want to warn the
               user about this, although the behavior of CK2's error.log
               would suggest that empty history files ought be used for
               wasteland (which is incorrect, causing confusion). */
            continue;
        }

        // TO BE CONTINUED...
    }
}
