
#include "mod_vfs.h"
#include "default_map.h"
#include "province_map.h"
#include "definitions_table.h"
#include "bmp_format.h"
#include "pdx.h"
#include "color.h"
#include "error.h"
#include "optional.h"

#include <boost/filesystem.hpp>
#include <boost/program_options.hpp>

#include <string>
#include <fstream>
#include <iostream>

using namespace std;
using namespace std::experimental;
using namespace boost::filesystem;
namespace po = boost::program_options;

struct province {
    /* facts about this province */
    uint id;
    bool is_seazone;
    optional<string> county_title;

    /* options regarding this province's painting */
    optional<rgb> color; // fill the province with this color, if specified

    province(uint16_t _id, bool attr_seazone)
        : is_seazone(attr_seazone), id(_id) { }
    province(uint16_t _id, bool attr_seazone, const std::string& title)
        : is_seazone(attr_seazone), id(_id), county_title(title) { }
};


class province_table {
    typedef vector<province> vec_t;
    vec_t vec;
   
public:
    province_table() = delete;

    province_table(const mod_vfs& vfs, const default_map& dm, const definitions_table& dt) {
        vec.reserve(dm.max_province_id() + 1);
        vec.emplace_back(province{ 0, false });

        char filename[128];
        path real_path;

        for (uint16_t id = 1; id <= dm.max_province_id(); ++id) {
            auto&& def = dt[id];
            bool is_seazone{ dm.id_is_seazone(id) };

            if (!(def.name.empty() || is_seazone)) {
                sprintf(filename, "%u - %s.txt", id, def.name.c_str());
                path virt_path{ "history/provinces" };
                virt_path /= filename;

                if (vfs.resolve_path(&real_path, virt_path)) {
                    const string spath{ real_path.string() };
                    pdx::plexer lex{ spath.c_str() };
                    pdx::block doc{ lex, true };

                    for (auto&& s : doc.stmt_list)
                        if (s.key_eq("title") && s.val.is_title())
                            vec.emplace_back(province{ id, is_seazone, s.val.as_c_str() });

                    continue;
                }
                else
                    cerr << "warning: failed to find expected file: " << virt_path.native() << endl;
            }

            vec.emplace_back(province{ id, is_seazone });
        }
    }

    province& operator[](uint16_t id) noexcept { return vec[id]; }
    const province& operator[](uint16_t id) const noexcept { return vec[id]; }

    vec_t::iterator begin() noexcept { return vec.begin() + 1; }
    vec_t::const_iterator begin() const noexcept { return vec.cbegin() + 1; }
    vec_t::iterator end() noexcept { return vec.end(); }
    vec_t::const_iterator end() const noexcept { return vec.cend(); }

    /* convenience methods that handle the pseudo-province-IDs of TYPE_OCEAN & TYPE_IMPASSABLE */

    bool is_water(uint16_t id) const noexcept {
        return id == province_map::TYPE_OCEAN || (id <= province_map::REAL_ID_MAX && vec[id].is_seazone);
    }

    bool is_impassable(uint16_t id) const noexcept { return id == province_map::TYPE_IMPASSABLE; }

    bool is_wasteland(uint16_t id) const noexcept {
        return id <= province_map::REAL_ID_MAX && !vec[id].county_title && !vec[id].is_seazone;
    }
};


int erode_impassable_pixels(province_map&, const province_table&);


int main(int argc, const char** argv) {
    try {
        path opt_game_path;
        bool opt_outline_provinces;
        bool opt_outline_seazones;
        bool opt_outline_between_wasteland;

        /* command-line & configuration file parameter specification */

        po::options_description opt_spec{ "Options" };
        opt_spec.add_options()
            ("help,h", "Show help information")
            ("config",
                po::value<path>(),
                "Configuration file")
            ("game-path",
                po::value<path>(&opt_game_path)->default_value("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings II"),
                "Path to game folder")
            ("mod-path",
                po::value<path>(),
                "Path to root folder of a mod")
            ("submod-path",
                po::value<path>(),
                "Path to root folder of a sub-mod")
            ("outline-provinces",
                po::value<bool>(&opt_outline_provinces)->default_value(true),
                "Draw province outline")
            ("outline-seazones",
                po::value<bool>(&opt_outline_seazones)->default_value(false),
                "Include seazones in province outline")
            ("outline-between-wasteland",
                po::value<bool>(&opt_outline_between_wasteland)->default_value(false),
                "Don't merge wasteland in province outline")
            ;

        /* parse command line & optional configuration file (command-line options override --config file options)
         *
         * example config file contents:
         *
         *   game-path = C:/SteamLibrary/steamapps/common/Crusader Kings II
         *   mod-path  = D:\git\SWMH-BETA\SWMH
         *
         *   outline-provinces = no  # don't draw the province outline (boolean options take yes/no/true/false/1/0)
         */

        po::variables_map opt;
        po::store(po::parse_command_line(argc, argv, opt_spec), opt);

        if (opt.count("config")) {
            const string cfg_path = opt["config"].as<path>().string();
            std::ifstream f_cfg{ cfg_path };

            if (f_cfg)
                po::store(po::parse_config_file(f_cfg, opt_spec), opt);
            else
                throw runtime_error("failed to open config file specified with --config: " + cfg_path);
        }

        if (opt.count("help")) {
            cout << opt_spec << endl;
            return 0;
        }

        po::notify(opt);

        mod_vfs vfs{ opt_game_path };

        if (opt.count("mod-path")) {
            vfs.push_mod_path(opt["mod-path"].as<path>());

            if (opt.count("submod-path"))
                vfs.push_mod_path(opt["submod-path"].as<path>());
        }
        else if (opt.count("submod-path"))
            throw runtime_error("cannot specify --submod-path without also providing a --mod-path");

        /* done with program option processing */

        const default_map dm{ vfs };
        const definitions_table def_tbl{ vfs, dm };
        const province_table prov_tbl{ vfs, dm, def_tbl };
        province_map pm{ vfs, dm, def_tbl };

        int n_impassable_px_removed = erode_impassable_pixels(pm, prov_tbl);
        if (n_impassable_px_removed < 0)
            throw runtime_error("impossible to redistribute impassable pixels on province map");

        const char* path = "out.bmp";
        FILE* f;

        if ((f = fopen(path, "wb")) == nullptr)
            throw va_error("could not open file for writing: %s: %s", strerror(errno), path);

        bmp_file_header bf_hdr;

        uint n_width = pm.width() - 1;
        uint n_height = pm.height() - 1;

        /* calculate row size with 32-bit alignment padding */
        uint n_row_sz = 4 * ((24 * n_width + 31) / 32);
        uint n_map_sz = n_row_sz * n_height;

        bf_hdr.magic = BMP_MAGIC;
        bf_hdr.n_file_size = sizeof(bf_hdr) + n_map_sz;
        bf_hdr.reserved1 = 0;
        bf_hdr.reserved2 = 0;
        bf_hdr.n_bitmap_offset = sizeof(bf_hdr);
        bf_hdr.n_header_size = 40;
        bf_hdr.n_width = n_width;
        bf_hdr.n_height = n_height;
        bf_hdr.n_planes = 1;
        bf_hdr.n_bpp = 24;
        bf_hdr.compression_type = 0;
        bf_hdr.n_bitmap_size = n_map_sz;
        bf_hdr.x_resolution = 0;
        bf_hdr.y_resolution = 0;
        bf_hdr.n_colors = 0;
        bf_hdr.n_important_colors = 0;

        printf("impassable: %d (%0.3f%%)\n", n_impassable_px_removed, 100. * n_impassable_px_removed / (pm.width() * pm.height()));
        printf("width:      %u\n", n_width);
        printf("height:     %u\n", n_height);
        printf("size:       %0.2f MiB\n", bf_hdr.n_file_size / 1024.0 / 1024.0);

        if (fwrite(&bf_hdr, sizeof(bf_hdr), 1, f) < 1)
            throw va_error("failed to write bitmap header: %s: %s", strerror(errno), path);

        auto p_out_map = make_unique<uint8_t[]>( n_map_sz );

        const rgb WATER_COLOR{ 0x5BADFF };
        const rgb WASTELAND_COLOR{ 0xAAAAAA };
        const rgb IMPASSABLE_COLOR{ 0x473A28 };

        /* draw base map */

        for (uint y = 0; y < n_height; ++y) {
            auto p_out_row = &p_out_map[n_row_sz * (n_height - 1 - y)];

            for (uint x = 0; x < n_width; ++x) {
                uint16_t prov_id = pm.at(x, y);

                rgb color{ 0xFF,0xFF,0xFF };

                if (prov_id <= province_map::REAL_ID_MAX) {
                    const province& prov = prov_tbl[prov_id];

                    if (prov.color)
                        color = *prov.color;
                    else if (prov.is_seazone)
                        color = WATER_COLOR;
                    else if (!prov.county_title)
                        color = WASTELAND_COLOR;
                }
                else if (prov_id == province_map::TYPE_OCEAN)
                    color = WATER_COLOR;
                else if (prov_id == province_map::TYPE_IMPASSABLE)
                    color = IMPASSABLE_COLOR;

                p_out_row[3 * x + 0] = color.blue();
                p_out_row[3 * x + 1] = color.green();
                p_out_row[3 * x + 2] = color.red();
            }
        }

        if (opt_outline_provinces) {
            /* draw province outline: top & left edges */

            const rgb OUTLINE_COLOR{ 0x7F7F7F };

            for (uint y = 0; y < n_height; ++y) {
                auto p_out_row = &p_out_map[n_row_sz * (n_height - 1 - y)];

                for (uint x = 0; x < n_width; ++x) {
                    uint16_t prov_id = pm.at(x, y);
                    uint16_t right_prov_id = pm.at(x + 1, y);
                    uint16_t below_prov_id = pm.at(x, y + 1);

                    if (prov_id == right_prov_id && prov_id == below_prov_id)
                        continue;

                    /* skip outline if edge(s) are only between wasteland, unless --outline-between-wasteland */

                    if (!opt_outline_between_wasteland &&
                        prov_tbl.is_wasteland(prov_id) &&
                        prov_tbl.is_wasteland(right_prov_id) &&
                        prov_tbl.is_wasteland(below_prov_id))
                        continue;

                    /* draw an outline pixel if any of the edges involve a land province or if --outline-seazones */

                    if (!prov_tbl.is_water(prov_id) ||
                        !prov_tbl.is_water(right_prov_id) ||
                        !prov_tbl.is_water(below_prov_id) ||
                        opt_outline_seazones) {

                        p_out_row[3 * x + 0] = OUTLINE_COLOR.blue();
                        p_out_row[3 * x + 1] = OUTLINE_COLOR.green();
                        p_out_row[3 * x + 2] = OUTLINE_COLOR.red();
                    }
                }
            }
        }

        if (fwrite(p_out_map.get(), n_map_sz, 1, f) < 1)
            throw va_error("failed to write bitmap: %s: %s", strerror(errno), path);
    }
    catch (const exception& e) {
        cerr << "fatal: " << e.what() << endl;
        return 1;
    }

    return 0;
}

/* slices are discrete intervals along a fixed axis */
struct slice {
    int a; // a <= b (always)
    int b; // a == b for a singleton interval (point)
    int index; // slice index -- as used here, this is the y-value of an implied line segment
    constexpr slice(int min, int max, int i) : a(min), b(max), index(i) { }
    slice() = delete; // no default value semantics are valid
};

/* we'll want to change this data structure later if we choose to implement slice cutting (will reduce worst-case
 * computational complexity for highly abnormal input but, as such, is probably not worth the additional work for our
 * /current/ use case). simplest alternate data structure that guarantees same complexity gain is a doubly-linked list,
 * while an interval tree is theoretically optimal (but not a good choice here). */
typedef vector<slice> slice_vec_t;

/* decompose a province_map into slices (x-intervals) of impassable pixels */
int slice_province_map(slice_vec_t& sv, const province_map& pm) {
    int n_pixels = 0;
    const int width = pm.width();
    const int height = pm.height();
    auto p_row = pm.map();

    for (int y = 0; y < height; ++y) {
        const slice no_slice{ -1, -1, y };
        slice cur_slice{ no_slice };

        for (int x = 0; x <= width; ++x) {
            auto id = (x < width) ? p_row[x] : 0;
            
            if (id = province_map::TYPE_IMPASSABLE && cur_slice.a < 0)
                cur_slice.a = x; // start a slice
            else if (id != province_map::TYPE_IMPASSABLE && cur_slice.a >= 0) {
                /* finish a slice */
                n_pixels += x - cur_slice.a;
                cur_slice.b = x - 1;
                sv.emplace_back(cur_slice);
                cur_slice = no_slice;
            }
        }

        p_row += width;
    }

    return n_pixels;
}

struct erode_direction {
    uint i : 2; // 2-bit unsigned int behavior
    erode_direction() : i(0) {}
    erode_direction(uint j) : i(j) {}
    erode_direction operator++() { return ++i; }

    bool is_north() const noexcept { return i == 0; }
    bool is_east()  const noexcept { return i == 1; }
    bool is_south() const noexcept { return i == 2; }
    bool is_west()  const noexcept { return i == 3; }
    
    static const char* DIRECTION[4];
    operator const char*() noexcept { return DIRECTION[i]; }
};

const char* erode_direction::DIRECTION[] = { "N","E","S","W" };

/* fairly redistribute impassable pixels into adjacent land provinces */
int erode_impassable_pixels(province_map& pm, const province_table& pt) {
    slice_vec_t sv;
    const int n_pixels = slice_province_map(sv, pm);

    const int x_max = pm.width() - 1;
    const int y_max = pm.height() - 1;
    auto p_map = pm.map();

    erode_direction cur_direction;
    int n_stalled_passes = 0;
    int n_pixels_done = 0;

    while (n_pixels_done < n_pixels) {
        int n_pixels_done_this_pass = 0;
        erode_direction start_direction = cur_direction;

        for (auto&& s : sv) {
            const int y = s.index;

            for (int x = s.a; x <= s.b; ++x) {

                /* in later passes, we might encounter pixels in the slice that are no longer impassable, because we
                 * do not presently split slices or even bother shrinking them for now. */
                if (pm.at(x, y) == province_map::TYPE_IMPASSABLE) {
                    uint16_t receiver = 0;

                    if (cur_direction.is_north() && y > 0)
                        receiver = pm.at(x, y - 1);
                    else if (cur_direction.is_east() && x < x_max)
                        receiver = pm.at(x + 1, y);
                    else if (cur_direction.is_south() && y < y_max)
                        receiver = pm.at(x, y + 1);
                    else if (cur_direction.is_west() && x > 0)
                        receiver = pm.at(x - 1, y);

                    if (receiver && receiver <= province_map::REAL_ID_MAX && !pt[receiver].is_seazone) {
                        p_map[y*pm.width() + x] = receiver; // donate (x,y) to receiver
                        ++n_pixels_done_this_pass;
                    }
                }

                ++cur_direction;
            }
        }

        if (n_pixels_done_this_pass == 0) {
            if (++n_stalled_passes == 4) // have made no progress for 4 cycles (all 4 directional start states tried)
                return -1; // ... so it is fundamentally impossible for this algorithm to complete on this map

            if (start_direction == cur_direction) // our next pass would've started with the same initial direction
                ++cur_direction; // and we know that would result in a stalled pass, so we start on the next direction
        }
        else {
            n_stalled_passes = 0;
            n_pixels_done += n_pixels_done_this_pass;
        }
    }

    return n_pixels_done;
}
