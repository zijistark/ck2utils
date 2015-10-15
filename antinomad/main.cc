
#include "an_province.h"
#include "default_map.h"
#include "definitions_table.h"
#include "pdx.h"
#include "error.h"

#include <boost/filesystem.hpp>

#include <cstdio>
#include <cerrno>
#include <cstring>
#include <vector>
#include <algorithm>

using namespace boost::filesystem;


/*

config:

- where to write our generated events (stdout seems a reasonable default)
- where to find the province history (path to mod root)
- where to find fallback province history (path to vanilla)
- start year, end year
- [filter list of province IDs] path to this file or accept it on stdin (stdin default)
*/


const path VROOT_DIR("D:/SteamLibrary/steamapps/common/Crusader Kings II");
const path ROOT_DIR("D:/g/SWMH-BETA/SWMH");

const uint START_YEAR = 867;
const uint END_YEAR = 1337;


void do_stuff_with_provinces(const default_map&, const definitions_table&, an_province**);

void print_block(int indent, const pdx::block*);
void print_stmt(int indent, const pdx::stmt&);
void print_obj(int indent, const pdx::obj&);

int main(int argc, char** argv) {

    try {
        default_map dm(ROOT_DIR);
        definitions_table def_tbl(dm);

        an_province** prov_map = new an_province*[ dm.max_province_id() ];

        do_stuff_with_provinces(dm, def_tbl, prov_map);

    }
    catch (std::exception& e) {
        fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }

    return 0;
}



bool block_has_title_stmt(const pdx::block& block) {
    for (auto&& s : block.stmt_list)
        if (s.key_eq("title"))
            return true;
    return false;
}


struct hist_record {
    pdx::date_t date;
    const char* cul;
    const char* rel;
    bool is_holy;

    hist_record(pdx::date_t d)
        : date(d), cul(nullptr), rel(nullptr), is_holy(false) {}

    bool operator<(const hist_record& e) const noexcept {
        return date < e.date;
    }
};


bool process_hist_record(const pdx::block* p_block, std::vector<hist_record>& records) {

    hist_record& r = records.back();

    for (auto&& s : p_block->stmt_list) {
        if (s.key.is_c_str()) {
            const char* key = s.key.c_str();

            if (strcasecmp(key, "culture") == 0)
                r.cul = s.val.as_c_str();
            else if (strcasecmp(key, "religion") == 0)
                r.rel = s.val.as_c_str();
        }
        else if (s.key.is_title()) {
            assert( pdx::title_tier(s.key.title()) == pdx::TIER_BARON );

            if (s.val.is_integer()) {
                // e.g., b_roma = 0
                assert( s.val.integer() == 0 );
            }
            else {
                const char* holding_type = s.val.as_c_str();

                if (strcasecmp(holding_type, "temple") == 0)
                    r.is_holy = true;
            }
        }
    }

    return (r.cul || r.rel || r.is_holy);
}


void do_stuff_with_provinces(const default_map& dm,
                             const definitions_table& def_tbl,
                             an_province** prov_map) {

    using namespace pdx;

    path prov_hist_root = ROOT_DIR / "history/provinces";
    path prov_hist_vroot = VROOT_DIR / "history/provinces";

    char filename[256];
    uint id = 0;

    for (auto&& r : def_tbl.row_vec) {
        ++id;
        prov_map[id] = 0;

        if (dm.id_is_seazone(id)) // sea | major river
            continue;

        if (r.name.empty()) // wasteland | external
            continue;

        sprintf(filename, "%u - %s.txt", id, r.name.c_str());

        path prov_hist_file = prov_hist_root / filename;

        if (!exists(prov_hist_file)) {
            path prov_hist_vfile = prov_hist_vroot / filename;

            if (!exists(prov_hist_vfile))
                throw va_error("could not find province history file: %s", filename);
            else
                prov_hist_file = prov_hist_vfile;
        }

        pdx::plexer lex(prov_hist_file.c_str());
        pdx::block doc(lex, true);


        std::vector<hist_record> records;

        /* scan top-level... */

        static const pdx::date_t EPOCH = { 1, 1, 1 };
        records.emplace_back(EPOCH);
        process_hist_record(&doc, records);

        if (!records.front().cul && block_has_title_stmt(doc))
            throw va_error("province %u lacks a top-level culture assignment: %s",
                           id, prov_hist_file.c_str());

        if (!records.front().rel && block_has_title_stmt(doc))
            throw va_error("province %u lacks a top-level religion assignment: %s",
                           id, prov_hist_file.c_str());

        /* scan history entries... */

        for (auto&& s : doc.stmt_list) {
            if (!s.key.is_date())
                continue;

            records.emplace_back( s.key.date() );
            if (!process_hist_record(s.val.as_block(), records))
                records.pop_back(); // n/m, the entry didn't contain any relevant info

        }

        // history records are possibly out-of-order, so fix that now.
        std::sort(records.begin(), records.end());

        /* build a merged (start year, culture, religion, has_temple) level table... */

        an_province* p_prov = prov_map[id] = new an_province(id);

        // ACTUALLY DO THE MERGE...

        /* and some useful debugging output... */

        printf("%u (%s):\n", id, r.name.c_str());

        for (auto&& r : records) {
            printf("  %hu.%hhu.%hhu:\n", r.date.y, r.date.m, r.date.d);

            if (r.cul)
                printf("    culture:  %s\n", r.cul);
            if (r.rel)
                printf("    religion: %s\n", r.rel);
            if (r.is_holy)
                printf("    HOLY\n");
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
        printf("%s", o.data.s);
    }
    else if (o.type == obj::TITLE) {
        printf("%s", o.data.s);
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


