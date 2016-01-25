
#include "error.h"
#include "default_map.h"
#include "province_map.h"
#include "bmp_format.h"

#include <boost/filesystem.hpp>

#include <cstdio>
#include <cerrno>
#include <cstring>
#include <cstdlib>
#include <cassert>

using namespace boost::filesystem;

//const path ROOT_PATH("D:/SteamLibrary/steamapps/common/Crusader Kings II");
const path ROOT_PATH("D:/g/SWMH-BETA/SWMH");
//const path OUT_PATH("D:/SteamLibrary/steamapps/common/Crusader Kings II/map/topology.bmp");
//const path HEIGHTMAP_PATH("D:/g/SWMH-BETA/SWMH/map/topology.bmp");
const path OUT_PATH("topology.bmp");

int main(int argc, char** argv) {

    path output_path = OUT_PATH;

    if (argc >= 2)
        output_path = path(argv[1]);

    try {
        default_map dm(ROOT_PATH);
        province_map pm(dm);

        assert( pm.width() % 4 == 0 );

        const char* path = output_path.c_str();
        FILE* f;

        if ( (f = fopen(path, "wb")) == nullptr )
            throw va_error("could not open file for writing: %s: %s", strerror(errno), path);

        bmp_file_header bf_hdr;
        errno = 0;

        bf_hdr.magic = BMP_MAGIC;
        bf_hdr.reserved1 = 0;
        bf_hdr.reserved2 = 0;
        bf_hdr.n_header_size = 40;
        bf_hdr.n_width = pm.width();
        bf_hdr.n_height = pm.height();
        bf_hdr.n_planes = 1;
        bf_hdr.n_bpp = 8;
        bf_hdr.compression_type = 0;
        bf_hdr.n_bitmap_size = pm.width()*pm.height();
        bf_hdr.x_resolution = 0;
        bf_hdr.y_resolution = 0;
        bf_hdr.n_colors = 0;
        bf_hdr.n_important_colors = 0;

        uint bitmap_offset = static_cast<uint>(sizeof(bf_hdr) + 256*4);

        bf_hdr.n_file_size = bitmap_offset + pm.width() * pm.height();
        bf_hdr.n_bitmap_offset = bitmap_offset;

        printf("width: %u\n", pm.width());
        printf("height: %u\n", pm.height());
        printf("header size: %lu\n", sizeof(bf_hdr));
        printf("bitmap offset: %u\n", bf_hdr.n_bitmap_offset);
        printf("file size: %u\n", bf_hdr.n_file_size);

        if ( fwrite(&bf_hdr, sizeof(bf_hdr), 1, f) < 1 )
            throw va_error("failed to write bitmap header: %s: %s", strerror(errno), path);

        for (int i = 0; i < 256; ++i) {
            uint8_t bgra[4];

            for (int j = 0; j < 3; ++j)
                bgra[j] = static_cast<uint8_t>(i);

            bgra[3] = 0;

            if ( fwrite(&bgra, sizeof(bgra), 1, f) < 1 )
                throw va_error("failed to write bitmap color index %u: %s: %s", i, strerror(errno), path);
        }

        const uint16_t* pm_map = pm.map();
        uint8_t topo_row[pm.width()];

        for (int y = pm.height()-1; y >= 0; --y) {

            const uint16_t* pm_row = &pm_map[ y*pm.width() ];

            for (int x = 0; x < (signed)pm.width(); ++x)
                topo_row[x] = (pm_row[x] == province_map::TYPE_OCEAN || dm.id_is_seazone(pm_row[x])) ? 93 : 95;

            if ( fwrite(&topo_row, sizeof(topo_row), 1, f) < 1 )
                throw va_error("failed to write row y=%d of pixel array: %s: %s", y, strerror(errno), path);
        }

        fclose(f);
    }
    catch (std::exception& e) {
        fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }

    return 0;
}
