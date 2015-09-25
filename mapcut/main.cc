
#include "default_map.h"
#include "definitions_table.h"
#include "pdx.h"
#include "error.h"

#include <boost/filesystem.hpp>

#include <cstdio>
#include <cerrno>
#include <cstring>
#include <string>
#include <unordered_map>

using namespace boost::filesystem;


const path VROOT_DIR("D:/SteamLibrary/steamapps/common/Crusader Kings II");
const path ROOT_DIR("D:/g/SWMH-BETA/SWMH");
const path OUT_ROOT_DIR("D:/g/minswmh/minswmh");
const path TITLES_PATH("common/landed_titles/swmh_landed_titles.txt");

void print_block(int indent, const pdx::block*);
void print_stmt(int indent, const pdx::stmt&);
void print_obj(int indent, const pdx::obj&);

typedef std::vector<std::string> strvec_t;
typedef std::unordered_map<std::string, uint> str2id_map_t;

const pdx::block* find_title(const char* title, const pdx::block* p_root);
void find_titles_under(const pdx::block*, strvec_t& out);
void fill_county_to_id_map(const default_map&, const definitions_table&, str2id_map_t& out);
void blank_title_history(const strvec_t&);


int main(int argc, char** argv) {

    if (argc != 2) {
        // TODO: use Boost::ProgramOptions, and cut the crap! :frowning_imp:
        fprintf(stderr, "USAGE:\n  %s <TITLE>\n", argv[0]);
        return 1;
    }

    const char* top_title = argv[1];
    assert( pdx::looks_like_title(top_title) );
    assert( pdx::title_tier(top_title) >= pdx::TIER_COUNT );

    try {
        default_map dm(ROOT_DIR);
        definitions_table def_tbl(dm);

        str2id_map_t county_to_id_map;
        fill_county_to_id_map(dm, def_tbl, county_to_id_map);

        const path titles_path = ROOT_DIR / TITLES_PATH;
        pdx::plexer lex(titles_path.c_str());
        pdx::block doc(lex, true);

        const pdx::block* p_top_title_block = find_title(top_title, &doc);

        if (p_top_title_block == nullptr)
            throw va_error("top de jure title '%s' not found: %s",
                           top_title, titles_path.c_str());

        strvec_t del_titles = { top_title };

        find_titles_under(p_top_title_block, del_titles);

        /* for every deleted county title, convert its associated province into
           wasteland */

        for (auto&& t : del_titles) {
            if (pdx::title_tier(t.c_str()) != pdx::TIER_COUNT)
                continue;

            auto i = county_to_id_map.find(t);

            if (i == county_to_id_map.end())
                throw va_error("County not assigned in province history: %s", t.c_str());

            uint id = i->second;

            /* blank the province name in definitions to turn it into a wasteland */
            def_tbl.row_vec[id-1].name = "";
        }

        path out_def_path = OUT_ROOT_DIR / "map" / dm.definitions_path();
        def_tbl.write(out_def_path);

        blank_title_history(del_titles);
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

        if (pdx::title_tier(t) <= top_title_tier)
            continue; // skip recursion, because the title's tier is insufficient

        p = find_title(top_title, p); // recurse into title block

        if (p != nullptr)
            return p; // cool, found in subtree, pass it along and terminate search
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
        }
    }
}


void print_block(int indent, const pdx::block* p_b) {
    for (auto&& s : p_b->stmt_list)
        print_stmt(indent, s);
}


void print_stmt(int indent, const pdx::stmt& s) {
    printf("%*s", indent, "");
    print_obj(indent, s.key);
    printf(" = ");
    print_obj(indent, s.val);
    printf("\n");
}


void print_obj(int indent, const pdx::obj& o) {

    using namespace pdx;

    if (o.type == obj::STR) {
        if (!strchr(o.data.s, ' ')) // not the only time to quote, but whatever
            printf("%s", o.data.s);
        else
            printf("\"%s\"", o.data.s);
    }
    else if (o.type == obj::INT) {
        printf("%d", o.data.i);
    }
    else if (o.type == obj::DECIMAL) {
        printf("%s", o.data.s);
    }
    else if (o.type == obj::DATE) {
        printf("DATE(%s)", o.data.s);
    }
    else if (o.type == obj::TITLE) {
        printf("TITLE(%s)", o.data.s);
    }
    else if (o.type == obj::BLOCK) {
        printf("{\n");
        print_block(indent+4, o.data.p_block);
        printf("%*s}", indent, "");
    }
    else if (o.type == obj::LIST) {
        printf("{ ");

        for (auto&& i : o.data.p_list->obj_list) {
            print_obj(indent, i);
            printf(" ");
        }

        printf("}");
    }
    else if (o.type == obj::COLOR) {
        printf("{ %u %u %u }", o.data.color.r, o.data.color.g, o.data.color.b);
    }
    else {
        assert(false);
    }
}


