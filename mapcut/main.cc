
#include "default_map.h"
#include "definitions_table.h"
#include "provsetup.h"
#include "pdx/pdx.h"
#include "pdx/error.h"

#include <boost/filesystem.hpp>

#include <cstdio>
#include <cerrno>
#include <cstring>
#include <string>
#include <unordered_map>
#include <fstream>
#include <iomanip>
#include <algorithm>


using namespace boost::filesystem;


/* TODO: use Boost::ProgramOptions (or just a config file), and end this nonsense */
/*
const path VROOT_DIR("/var/local/vanilla-ck2");
const path ROOT_DIR("/var/local/git/SWMH-BETA/SWMH");
const path OUT_ROOT_DIR("/var/local/git/MiniSWMH/MiniSWMH");
*/

const path VROOT_DIR("/home/ziji/vanilla");
const path ROOT_DIR("/home/ziji/g/SWMH-BETA/SWMH");
const path OUT_ROOT_DIR("/home/ziji/g/MiniSWMH/MiniSWMH");


const path TITLES_FILE("swmh_landed_titles.txt"); // only uses this landed_titles file
const path PROVSETUP_FILE("00_province_setup.txt"); // only uses this prov_setup file


typedef std::vector<std::string> strvec_t;
typedef std::unordered_map<std::string, uint> str2id_map_t;


const pdx::block* find_title(const char* title, const pdx::block* p_root);
void find_titles_under(const pdx::block*, strvec_t& out);
void fill_county_to_id_map(const pdx::vfs&, const default_map&, const definitions_table&, str2id_map_t& out);
void blank_title_history(const pdx::vfs&, const strvec_t&);


class lt_printer {
    std::ofstream os;
    strvec_t      top_titles;
    uint          indent;
    bool          in_code_block;

    void print(const pdx::block&);
    void print(const pdx::list&);
    void print(const pdx::statement&);
    void print(const pdx::object&);

public:
    lt_printer(const fs::path& out_path, const strvec_t& top_titles, const pdx::block* p_root_block);
};


struct {
    uint n_counties_before;
    uint n_counties_cut;
    uint n_titles_cut;
    uint n_title_hist_blanked;
} g_stats;


int main(int argc, char** argv) {

    if (argc < 2) {
        fprintf(stderr, "USAGE:\n  %s TITLE [TITLE ...]\n\nTITLE: top de jure title to remove (if plural, should not overlap)\n", argv[0]);
        return 1;
    }

    strvec_t top_titles;
    top_titles.reserve(argc - 1);

    for (int i = 1; i < argc; ++i) {
        const char* t = argv[i];
        assert( pdx::looks_like_title(t) );
        assert( pdx::title_tier(t) >= pdx::TIER_COUNT );
        top_titles.emplace_back(t);
    }

    try {
        pdx::vfs vfs{ VROOT_DIR };
        vfs.push_mod_path(ROOT_DIR);

        default_map dm(vfs);
        definitions_table def_tbl(vfs, dm);
        provsetup ps_tbl( vfs["common/province_setup" / PROVSETUP_FILE] );

        str2id_map_t county_to_id_map;
        fill_county_to_id_map(vfs, dm, def_tbl, county_to_id_map);
        g_stats.n_counties_before = county_to_id_map.size();

        pdx::parser parse( vfs["common/landed_titles" / TITLES_FILE] );
        strvec_t del_titles;

        for (auto&& top_title : top_titles) {
            const pdx::block* p_top_title_block = find_title(top_title.c_str(), parse.root_block());

            if (p_top_title_block == nullptr)
                throw va_error("Top de jure title '%s' not found!", top_title.c_str());

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
                throw va_error("County not assigned in province history: %s", t.c_str());

            uint id = i->second;

            /* blank the province name in definitions to turn it into a wasteland */
            def_tbl[id].name = "";

            /* blank the province's county title in provsetup to turn into a wasteland */
            std::string& title = ps_tbl.row_vec[id-1].title;

            if (title != t)
                throw va_error("province_setup: Province %u assigned as %s but it should be %s",
                               id, title.c_str(), t.c_str());

            title = "";

            ++g_stats.n_counties_cut;
        }

        /* write definition file */
        path out_def_path(OUT_ROOT_DIR / "map");
        create_directories(out_def_path);
        out_def_path /= dm.definitions_path();
        def_tbl.write(out_def_path);

        /* write province_setup file */
        path out_ps_path(OUT_ROOT_DIR / "common" / "province_setup");
        create_directories(out_ps_path);
        out_ps_path /= PROVSETUP_FILE;
        ps_tbl.write(out_ps_path);

        /* rewrite landed_titles */
        path out_lt_path(OUT_ROOT_DIR / "common" / "landed_titles");
        create_directories(out_lt_path);
        out_lt_path /= TITLES_FILE;
        lt_printer ltp( out_lt_path, top_titles, parse.root_block() );

        /* blank as much title history as necessary */
        blank_title_history(vfs, del_titles);

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

    for (auto&& s : *p_root) {
        if ( !(s.key().is_string() && pdx::looks_like_title( s.key().as_string() )) )
            continue;

        const char* t = s.key().as_string();
        assert( s.value().is_block() );
        const pdx::block* p = s.value().as_block();

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

    for (auto&& s : *p_root) {
        if ( !(s.key().is_string() && pdx::looks_like_title( s.key().as_string() )) )
            continue;

        const char* t = s.key().as_string();
        found_titles.push_back(t);
        assert( s.value().is_block() );
        const pdx::block* p_block = s.value().as_block();

        if (pdx::title_tier(t) > pdx::TIER_BARON)
            find_titles_under(p_block, found_titles);
    }
}



void fill_county_to_id_map(const pdx::vfs& vfs,
                           const default_map& dm,
                           const definitions_table& def_tbl,
                           str2id_map_t& county_to_id_map) {

    char filename[256];
    uint id = 0;

    for (auto&& r : def_tbl) {
        ++id;

        if (dm.id_is_seazone(id)) // sea | major river
            continue;

        if (r.name.empty()) // wasteland | external
            continue;

        sprintf(filename, "history/provinces/%u - %s.txt", id, r.name.c_str());
        fs::path real_path;

        if (!vfs.resolve_path(&real_path, filename))
            continue;

        const char* county = nullptr;

        pdx::parser parse(real_path);

        for (auto&& s : *parse.root_block()) {
            if (s.key() == "title") {
                assert( s.value().is_string() && pdx::looks_like_title( s.value().as_string() ) );
                county = s.value().as_string();
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
            throw va_error("County '%s' maps to both province %u and %u (at the least)!",
                           county, county_to_id_map[county], id);
        }
    }
}


void blank_title_history(const pdx::vfs& vfs, const strvec_t& deleted_titles) {

    path title_hist_oroot = OUT_ROOT_DIR / "history/titles";

    if (! create_directories(title_hist_oroot)) {
        // output directory preexisted, so we need to ensure that it's clean first

        for (auto&& e : directory_iterator(title_hist_oroot))
            remove(e.path());
    }

    g_stats.n_title_hist_blanked = 0;

    for (auto&& title : deleted_titles) {

        std::string filename = title + ".txt";
        fs::path virt_path = "history/titles" / filename;

        fs::path real_path;

        if ( vfs.resolve_path(&real_path, virt_path) ) {

            /* there is indeed reason to add a blank file override for
               this title, so let's get on with it... */

            path title_hist_opath = OUT_ROOT_DIR / virt_path;
            FILE* f;

            if ( (f = fopen(title_hist_opath.string().c_str(), "w")) == nullptr )
                throw va_error("Failed to blank title history: %s: %s",
                               strerror(errno), title_hist_opath.c_str());

            fclose(f);
            ++g_stats.n_title_hist_blanked;
        }
    }
}



lt_printer::lt_printer(const fs::path& p, const strvec_t& _top_titles, const pdx::block* p_root_block)
    : os(p.string()), top_titles(_top_titles), indent(0), in_code_block(false) {

    if (!os) throw std::runtime_error("Could not write to file: " + p.string());

    os << "# -*- ck2.landed_titles -*-" << std::endl << std::endl;
    print(*p_root_block);
}


void lt_printer::print(const pdx::block& b) {
    for (auto&& stmt : b) print(stmt);
}


void lt_printer::print(const pdx::list& l) {
    for (auto&& obj : l) {
        print(obj);
        os << ' ';
    }
}


void lt_printer::print(const pdx::statement& s) {
    const pdx::object& k = s.key();
    const pdx::object& v = s.value();

    bool opened_code_block = false;

    if (k.is_string() && v.is_block()) {
        /* I'm unhinged... */
        const std::string t{ k.as_string() };

        if (std::find(top_titles.begin(), top_titles.end(), t) != top_titles.end())
            return; // oh, and this is an AST subtree filter.

        if (!in_code_block && (k == "allow" || k == "gain_effect")) {
            in_code_block = true;
            opened_code_block = true;
        }
    }

    os << std::setfill(' ') << std::setw(indent) << "";
    print(k);
    os << " = ";

    /* note that the more correct approach to match my intention with force-quoting would involve loading
     * valid culture tags and simply hashing k into a map of them */

    bool force_quote = (
        k.is_string() && v.is_string() && // both k,v are strings
        !in_code_block && // we're not somewhere in an arbitrary code block
        v != "yes" && v != "no" && // v isn't boolean
        /* special keywords whose values we should not force-quote */
        k != "culture" && k != "religion" && k != "controls_religion" && k != "mercenary_type" &&
        k != "title" && k != "title_female" && k != "title_prefix" && k != "foa" && k != "foa_female" &&
        k != "graphical_culture" && k != "name_tier" && k != "holy_site" && k != "pentarchy"
    );

    if (force_quote) os << '"' << v.as_string() << '"';
    else print(v);

    if (opened_code_block) in_code_block = false;

    os << std::endl;
}


void lt_printer::print(const pdx::object& o) {
    if (o.is_string()) {
        if (strpbrk(o.as_string(), " \t\r\n'"))
            os << '"' << o.as_string() << '"';
        else
            os << o.as_string();
    }
    else if (o.is_integer())
        os << o.as_integer();
    else if (o.is_date())
        os << o.as_date();
    else if (o.is_decimal())
        os << o.as_decimal();
    else if (o.is_block()) {
        os << '{' << std::endl;
        indent += 4;
        print(*o.as_block());
        indent -= 4;
        os << std::setfill(' ') << std::setw(indent) << "";
        os << '}';
    }
    else if (o.is_list()) {
        os << "{ ";
        print(*o.as_list());
        os << '}';
    }
    else
        assert(false && "Unhandled object type");
}
