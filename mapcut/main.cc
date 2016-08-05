
#include "default_map.h"
#include "definitions_table.h"
#include "provsetup.h"
#include "pdx.h"
#include "error.h"

#include <boost/filesystem.hpp>

#include <cstdio>
#include <cerrno>
#include <cstring>
#include <string>
#include <unordered_map>

using namespace boost::filesystem;


/* TODO: use Boost::ProgramOptions (or just a config file), and end this nonsense */
const path VROOT_DIR("/home/ziji/ck2");
const path ROOT_DIR("/home/ziji/g/SWMH-BETA/SWMH");
const path OUT_ROOT_DIR("/home/ziji/g/MiniSWMH/MiniSWMH");
const path TITLES_PATH("common/landed_titles/swmh_landed_titles.txt"); // only uses this landed_titles file
const path PROVSETUP_FILE("00_province_setup.txt"); // only uses this prov_setup file

typedef std::vector<std::string> strvec_t;
typedef std::unordered_map<std::string, uint> str2id_map_t;

const pdx::block* find_title(const char* title, const pdx::block* p_root);
void find_titles_under(const pdx::block*, strvec_t& out);
void fill_county_to_id_map(const default_map&, const definitions_table&, str2id_map_t& out);
void blank_title_history(const strvec_t&);

struct {
    uint n_counties_before;
    uint n_counties_cut;
    uint n_titles_cut;
    uint n_title_hist_blanked;

    /* all wishful thinking below (FOR NOW!) */
    uint n_adjacencies_before;
    uint n_adjacencies_cut;
    uint n_title_hist_rewritten;
    uint n_regions_modified;
    uint n_regions_cut;
    uint n_island_regions_modified;
    uint n_island_regions_cut;
    uint n_invalidated_prov_refs;
    uint n_invalidated_title_refs;
} g_stats;


int main(int argc, char** argv) {

    if (argc < 2) {
        fprintf(stderr, "USAGE:\n  %s TITLE [TITLE ...]\n\nTITLE: top de jure title to remove (if plural, should not overlap)\n", argv[0]);
        return 1;
    }

    const char* top_titles[argc-1];

    for (int i = 1; i < argc; ++i) {
        const int j = i-1;
        top_titles[j] = argv[i];

        assert( pdx::looks_like_title( top_titles[j] ) );
        assert( pdx::title_tier( top_titles[j] ) >= pdx::TIER_COUNT );
    }


    try {
      default_map dm(ROOT_DIR);
        definitions_table def_tbl(dm);
        provsetup ps_tbl(ROOT_DIR / "common" / "province_setup" / PROVSETUP_FILE);

        str2id_map_t county_to_id_map;
        fill_county_to_id_map(dm, def_tbl, county_to_id_map);

        g_stats.n_counties_before = county_to_id_map.size();

        const path titles_path = ROOT_DIR / TITLES_PATH;
        pdx::plexer lex(titles_path.c_str());
        pdx::block doc(lex, true);

        strvec_t del_titles;

        for (auto top_title : top_titles) {
            const pdx::block* p_top_title_block = find_title(top_title, &doc);

            if (p_top_title_block == nullptr)
                throw va_error("top de jure title '%s' not found: %s",
                               top_title, titles_path.c_str());

            del_titles.emplace_back(top_title);
            find_titles_under(p_top_title_block, del_titles);
        }

        g_stats.n_titles_cut = del_titles.size();
        g_stats.n_counties_cut = 0;

        /* for every deleted county title, convert its associated province into
           wasteland */

        for (auto&& t : del_titles) {
            if (pdx::title_tier(t.c_str()) != pdx::TIER_COUNT)
                continue;

            auto i = county_to_id_map.find(t);

            if (i == county_to_id_map.end())
                throw va_error("county not assigned in province history: %s", t.c_str());

            uint id = i->second;

            /* blank the province name in definitions to turn it into a wasteland */
            def_tbl.row_vec[id-1].name = "";

            /* blank the province's county title in provsetup to turn into a wasteland */
            std::string& title = ps_tbl.row_vec[id-1].title;

            if (title != t)
                throw va_error("province_setup: province %u assigned as %s but it should be %s",
                               id, title.c_str(), t.c_str());

            title = "";

            ++g_stats.n_counties_cut;
        }

        path out_def_path(OUT_ROOT_DIR / "map");
        create_directories(out_def_path);
        out_def_path /= dm.definitions_path();
        def_tbl.write(out_def_path);

        path out_ps_path(OUT_ROOT_DIR / "common" / "province_setup");
        create_directories(out_ps_path);
        out_ps_path /= PROVSETUP_FILE;
        ps_tbl.write(out_ps_path);

        blank_title_history(del_titles);

        printf("Counties before cut:   %u\n", g_stats.n_counties_before);
        printf("Counties cut:          %u\n", g_stats.n_counties_cut);
        printf("Titles cut:            %u\n", g_stats.n_titles_cut);
        printf("Blanked title history: %u\n", g_stats.n_title_hist_blanked);
    }
    catch (std::exception& e) {
        fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }

    return 0;
}


const pdx::block* find_title(const char* top_title, const pdx::block* p_root) {

    uint top_title_tier = pdx::title_tier(top_title);

    for (auto&& s : p_root->stmt_list) {
        if (s.key.type != pdx::obj::TITLE)
            continue;

        const pdx::block* p = s.val.as_block();
        const char* t = s.key.data.s;

        if (strcmp(t, top_title) == 0)
            return p; // base case, terminate

        /* recursive case... */

        if (pdx::title_tier(t) <= top_title_tier)
            continue; // skip recursion, because the title's tier is too low

        p = find_title(top_title, p); // recurse into title block

        if (p != nullptr)
            return p; // cool, found in subtree, pass it upstream and terminate
    }

    return nullptr;
}


void find_titles_under(const pdx::block* p_root, strvec_t& found_titles) {

    for (auto&& s : p_root->stmt_list) {
        if (s.key.type != pdx::obj::TITLE)
            continue;

        const char* t = s.key.data.s;
        found_titles.push_back(t);

        if (pdx::title_tier(t) > pdx::TIER_BARON)
            find_titles_under(s.val.as_block(), found_titles);
    }
}



void fill_county_to_id_map(const default_map& dm,
                           const definitions_table& def_tbl,
                           str2id_map_t& county_to_id_map) {

    path prov_hist_root = ROOT_DIR / "history/provinces";
    path prov_hist_vroot = VROOT_DIR / "history/provinces";

    char filename[256];
    uint id = 0;

    for (auto&& r : def_tbl.row_vec) {
        ++id;

        if (dm.id_is_seazone(id)) // sea | major river
            continue;

        if (r.name.empty()) // wasteland | external
            continue;

        sprintf(filename, "%u - %s.txt", id, r.name.c_str());

        path prov_hist_file = prov_hist_root / filename;

        if (!exists(prov_hist_file)) {

            path prov_hist_vfile = prov_hist_vroot / filename;

            if (!exists(prov_hist_vfile))
                throw va_error("could not find province history file: %s",
                               filename);
            else {
                if (false) {
                    /* SWMH doesn't want to rely upon inherited vanilla province
                       history, so fix this situation right now. note that is
                       definitely not general-purpose behavior. */
                    copy_file(prov_hist_vfile, prov_hist_file);
                }
                else {
                    prov_hist_file = prov_hist_vfile;
                }
            }
        }

        const char* county = nullptr;

        pdx::plexer lex(prov_hist_file.c_str());
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

        if (!county_to_id_map.insert( {county, id} ).second) {
            throw va_error("county '%s' maps to both province %u and %u (at the least)!",
                           county, county_to_id_map[county], id);
        }
    }
}


void blank_title_history(const strvec_t& deleted_titles) {

    path title_hist_root = ROOT_DIR / "history/titles";
    path title_hist_vroot = VROOT_DIR / "history/titles";
    path title_hist_oroot = OUT_ROOT_DIR / "history/titles";

    if (! create_directories(title_hist_oroot)) {
        // output directory preexisted, so we need to ensure that it's clean first

        for (auto&& e : directory_iterator(title_hist_oroot))
            remove(e.path());
    }

    g_stats.n_title_hist_blanked = 0;

    for (auto&& title : deleted_titles) {

        std::string filename = title + ".txt";

        path title_hist_path = title_hist_root / filename;
        path title_hist_vpath = title_hist_vroot / filename;

        if ( exists(title_hist_path) || exists(title_hist_vpath) ) {

            /* there is indeed reason to add a blank file override for
               this title, so let's get on with it... */

            path title_hist_opath = title_hist_oroot / filename;
            FILE* f;

            if ( (f = fopen(title_hist_opath.c_str(), "w")) == nullptr )
                throw va_error("Failed to blank title history: %s: %s",
                               strerror(errno), title_hist_opath.c_str());

            fclose(f);
            ++g_stats.n_title_hist_blanked;
        }
    }
}


