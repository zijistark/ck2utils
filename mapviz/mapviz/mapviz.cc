
#include "default_map.h"
#include "province_map.h"
#include "bmp_format.h"
#include "error.h"

#include <boost/filesystem.hpp>

using namespace boost::filesystem;

//const path ROOT_PATH("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings II");
const path ROOT_PATH("C:/cygwin64/home/ziji/g/SWMH-BETA/SWMH");
const path OUT_PATH("out.bmp");


bool prov_is_water(const default_map& dm, uint prov_id) {
    return prov_id == province_map::TYPE_OCEAN || dm.id_is_seazone(prov_id);
}


int main()
{
    try {
        default_map dm(ROOT_PATH);
        province_map pm(dm);

        std::string spath = OUT_PATH.string();
        const char* path = spath.c_str();

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

        printf("width: %u\n", n_width);
        printf("height: %u\n", n_height);
        printf("header size: %zu\n", sizeof(bf_hdr));
        printf("bitmap offset: %u\n", bf_hdr.n_bitmap_offset);
        printf("file size: %u\n", bf_hdr.n_file_size);

        if (fwrite(&bf_hdr, sizeof(bf_hdr), 1, f) < 1)
            throw va_error("failed to write bitmap header: %s: %s", strerror(errno), path);

        uint8_t* p_out_map = new uint8_t[n_map_sz];

        const uint8_t WATER_RED = 0x5B;
        const uint8_t WATER_GREEN = 0xAD;
        const uint8_t WATER_BLUE = 0xFF;

        const uint16_t* p_id_map = pm.map();

        /* draw base map */

        for (uint y = 0; y < n_height; ++y) {
            uint8_t* p_out_row = &p_out_map[n_row_sz * (n_height - 1 - y)];

            for (uint x = 0; x < n_width; ++x) {
                uint16_t prov_id = pm.at(x, y);

                if (prov_is_water(dm, prov_id)) {
                    p_out_row[3 * x + 0] = WATER_BLUE;
                    p_out_row[3 * x + 1] = WATER_GREEN;
                    p_out_row[3 * x + 2] = WATER_RED;
                }
                else if (prov_id == province_map::TYPE_IMPASSABLE) {
                    p_out_row[3 * x + 0] = 0x00;
                    p_out_row[3 * x + 1] = 0x00;
                    p_out_row[3 * x + 2] = 0x00;
                }
                else {
                    p_out_row[3 * x + 0] = 0xFF;
                    p_out_row[3 * x + 1] = 0xFF;
                    p_out_row[3 * x + 2] = 0xFF;
                }
            }
        }

        /* draw province outline: top & left edges */

        for (uint y = 0; y < n_height; ++y) {
            uint8_t* p_out_row = &p_out_map[n_row_sz * (n_height - 1 - y)];

            for (uint x = 0; x < n_width; ++x) {
                uint16_t prov_id = pm.at(x, y);
                uint16_t right_prov_id = pm.at(x + 1, y);
                uint16_t below_prov_id = pm.at(x, y + 1);

                if (prov_id == right_prov_id && prov_id == below_prov_id)
                    continue;

                /* draw an outline pixel if any of the edges involve a land province */

                if (!prov_is_water(dm, prov_id) ||
                    !prov_is_water(dm, right_prov_id) ||
                    !prov_is_water(dm, below_prov_id)) {

                    p_out_row[3 * x + 0] = 0x7F;
                    p_out_row[3 * x + 1] = 0x7F;
                    p_out_row[3 * x + 2] = 0x7F;
                }
            }
        }

        if (fwrite(p_out_map, n_map_sz, 1, f) < 1)
            throw va_error("failed to write bitmap: %s: %s", strerror(errno), path);
    }
    catch (const std::exception& e) {
        fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }

    return 0;
}

