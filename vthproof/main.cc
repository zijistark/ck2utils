
#include "pdx.h"
#include "error.h"

#include <boost/filesystem.hpp>

#include <cstdio>
#include <cerrno>
#include <cstring>
#include <string>
#include <unordered_set>

using namespace boost::filesystem;


/* TODO: use Boost::ProgramOptions (or just a config file), and end this nonsense */
const path VROOT_DIR("D:/SteamLibrary/steamapps/common/Crusader Kings II");
const path ROOT_DIR("D:/g/SWMH-BETA/SWMH");
const path TITLES_PATH("common/landed_titles/swmh_landed_titles.txt");

typedef std::unordered_set<std::string> strset_t;

void find_titles_under(const pdx::block*, strset_t& out);
//void blank_title_history(const strvec_t&);


int main(int argc, char** argv) {

    try {
        const path titles_path = ROOT_DIR / TITLES_PATH;
        pdx::plexer lex(titles_path.c_str());
        pdx::block doc(lex, true);

        strset_t title_set;
        find_titles_under(&doc, title_set);

        path hist_root = ROOT_DIR / "history/titles";
        path hist_vroot = VROOT_DIR / "history/titles";

        char filename[256];

        for (auto&& t : title_set) {

            sprintf(filename, "%s.txt", t.c_str());

            path hist_file = hist_root / filename;
            path hist_vfile = hist_vroot / filename;

            if (!exists(hist_file) && exists(hist_vfile)) {
                copy_file(hist_vfile, hist_file);
                printf("%s\n", t.c_str());
            }
        }
/*
        for (directory_entry& e : directory_iterator(hist_vroot)) {

        }
*/
    }
    catch (std::exception& e) {
        fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }

    return 0;
}



void find_titles_under(const pdx::block* p_root, strset_t& found_titles) {

    for (auto&& s : p_root->stmt_list) {
        if (s.key.type != pdx::obj::TITLE)
            continue;

        const char* t = s.key.data.s;
        found_titles.emplace(t);

        if (pdx::title_tier(t) > pdx::TIER_BARON)
            find_titles_under(s.val.as_block(), found_titles);
    }
}
