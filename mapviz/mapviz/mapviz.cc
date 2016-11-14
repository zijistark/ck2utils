
#include "mod_vfs.h"
#include "default_map.h"
#include "province_map.h"
#include "definitions_table.h"
#include "bmp_format.h"
#include "pdx.h"
#include "color.h"
#include "error.h"

#include <boost/filesystem.hpp>
#include <boost/program_options.hpp>

#include <string>
#include <fstream>
#include <iostream>

using namespace std;
using namespace boost::filesystem;
namespace po = boost::program_options;


struct province {
    bool       is_seazone;
    uint16_t   id;
    string     county_title;
    rgba_color color;

    province(uint16_t _id, bool attr_seazone)
        : is_seazone(attr_seazone), id(_id), color{ 0xFF,0xFF,0xFF } { }
};


class province_table {
    vector<province> vec;
   
public:
    province_table(const default_map& dm) {
        vec.reserve(dm.max_province_id());

        for (uint i = 0; i < dm.max_province_id(); ++i)
            vec.emplace_back(province{ static_cast<uint16_t>(i + 1), dm.id_is_seazone(i + 1) });
    }

    bool is_water(uint16_t id) const noexcept {
        return id == province_map::TYPE_OCEAN || (id <= vec.size() && vec[id - 1].is_seazone);
    }

    bool is_impassable(uint16_t id) const noexcept { return id == province_map::TYPE_IMPASSABLE; }

    bool is_wasteland(uint16_t id) const noexcept {
        return id <= vec.size() && vec[id - 1].county_title.empty() && !vec[id - 1].is_seazone;
    }

    province& operator[](uint16_t id) noexcept { return vec[id - 1]; }
    const province& operator[](uint16_t id) const noexcept { return vec[id - 1]; }
};


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

        default_map dm{ vfs };
        definitions_table def_tbl{ vfs, dm };
        province_map pm{ vfs, dm, def_tbl };
        province_table prov_tbl{ dm };

        {
            char filename[128];
            uint id = 0;

            for (auto&& d : def_tbl.row_vec) {
                ++id;

                if (d.name.empty() || prov_tbl[id].is_seazone)
                    continue;

                sprintf(filename, "%u - %s.txt", id, d.name.c_str());

                path real_path;
                path virt_path{ "history/provinces" };
                virt_path /= filename;
                
                if (!vfs.resolve_path(&real_path, virt_path)) {
                    cerr << "warning: failed to find expected file: " << virt_path.native() << endl;
                    continue;
                }

                const string spath = real_path.string();
                pdx::plexer lex(spath.c_str());
                pdx::block doc(lex, true);

                for (auto&& s : doc.stmt_list)
                    if (s.key_eq("title"))
                        prov_tbl[id].county_title = s.val.as_c_str();
            }
        }

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

        printf("width:  %u\n", n_width);
        printf("height: %u\n", n_height);
        printf("size:   %0.2f MiB\n", bf_hdr.n_file_size / 1024.0 / 1024.0);

        if (fwrite(&bf_hdr, sizeof(bf_hdr), 1, f) < 1)
            throw va_error("failed to write bitmap header: %s: %s", strerror(errno), path);

        auto p_out_map = make_unique<uint8_t[]>( n_map_sz );

        const rgb WATER_COLOR{ 0x5B,0xAD,0xFF };

        /* draw base map */

        for (uint y = 0; y < n_height; ++y) {
            auto p_out_row = &p_out_map[n_row_sz * (n_height - 1 - y)];

            for (uint x = 0; x < n_width; ++x) {
                uint16_t prov_id = pm.at(x, y);

                if (prov_tbl.is_water(prov_id)) {
                    p_out_row[3 * x + 0] = WATER_COLOR.blue();
                    p_out_row[3 * x + 1] = WATER_COLOR.green();
                    p_out_row[3 * x + 2] = WATER_COLOR.red();
                }
                else if (prov_tbl.is_impassable(prov_id)) {
                    p_out_row[3 * x + 0] = 0x00;
                    p_out_row[3 * x + 1] = 0x00;
                    p_out_row[3 * x + 2] = 0x00;
                }
                else {
                    const province& prov = prov_tbl[prov_id];
                    p_out_row[3 * x + 0] = prov.color.blue();
                    p_out_row[3 * x + 1] = prov.color.green();
                    p_out_row[3 * x + 2] = prov.color.red();
                }
            }
        }

        if (opt_outline_provinces) {
            /* draw province outline: top & left edges */

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

                        p_out_row[3 * x + 0] = 0x7F;
                        p_out_row[3 * x + 1] = 0x7F;
                        p_out_row[3 * x + 2] = 0x7F;
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
