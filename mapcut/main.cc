
#include "default_map.h"
#include "definitions_table.h"
#include "pdx.h"
#include "error.h"

#include <boost/filesystem.hpp>

#include <cstdio>
#include <string>
#include <unordered_map>

using namespace boost::filesystem;

void print_block(int indent, const pdx::block*);
void print_stmt(int indent, const pdx::stmt&);
void print_obj(int indent, const pdx::obj&);

const path VROOT_DIR("D:/SteamLibrary/steamapps/common/Crusader Kings II");
const path ROOT_DIR("D:/g/SWMH-BETA/SWMH");
const path TITLES_PATH("common/landed_titles/swmh_landed_titles.txt");



int main(int argc, char** argv) {

    try {
        default_map dm(ROOT_DIR.string());

        definitions_table def_tbl(dm);

        std::unordered_map<std::string, uint> county_to_id_map;

        path prov_hist_root = ROOT_DIR / "history/provinces";
        path prov_hist_vroot = VROOT_DIR / "history/provinces";

        for (uint i = 0; i < def_tbl.row_vec.size(); ++i) {
            const definitions_table::row& r = def_tbl.row_vec[i];
            const uint id = i+1;

            if (dm.id_is_seazone(id)) // sea | major river
                continue;

            if (r.name.empty()) // wasteland | external
                continue;

            char filename[128];
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

            assert( exists(prov_hist_file) );

            const char* county = nullptr;

            pdx::plexer lex(prov_hist_file.c_str());
            pdx::block doc(lex, true);

            for (auto&& s : doc.stmt_list) {
                if (s.key_eq("title")) {
                    assert( s.val.type == pdx::obj::TITLE );
                    county = s.val.data.s;
                    assert( county[0] == 'c' && "Expected count-tier title ID; got some other-tier title ID" );
                }
            }

            if (county == nullptr) {
                /* history file contained no title assignment.  it was probably
                   blank (for a wasteland or something). we may want to warn the
                   user about this, although the behavior of CK2's error.log
                   would suggest that empty history files ought be used for
                   wasteland (which I believe is incorrect). */
                continue;
            }

            if (!county_to_id_map.insert( {county, id} ).second) {
                throw va_error("county '%s' maps to both province %u and %u (at the least)!",
                               county, county_to_id_map[county], id);
            }
        }

        for (auto&& m : county_to_id_map) {
            printf("%s => %u\n", m.first.c_str(), m.second);
        }
    }
    catch (std::exception& e) {
        fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }

    return 0;
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


