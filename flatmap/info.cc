
#include "error.h"
#include "bmp_format.h"

#include <boost/filesystem.hpp>

#include <cstdio>
#include <cerrno>
#include <cstring>
#include <cstdlib>
#include <cassert>

using namespace boost::filesystem;

const path IN_PATH("D:/SteamLibrary/steamapps/common/Crusader Kings II/map/topology.bmp");

int main(int argc, char** argv) {

    path in_path = IN_PATH;

    if (argc >= 2)
        in_path = path(argv[1]);

    try {
        const char* path = in_path.c_str();
        FILE* f;

        if ( (f = fopen(path, "rb")) == nullptr )
            throw va_error("could not open file: %s: %s", strerror(errno), path);

        bmp_file_header bf_hdr;

        if ( fread(&bf_hdr, sizeof(bf_hdr), 1, f) < 1 )
            throw va_error("failed to read bitmap file header: %s: %s", strerror(errno), path);

        assert( bf_hdr.magic == BMP_MAGIC );
        printf("file size:        %u\n", bf_hdr.n_file_size);
        printf("bitmap offset:    %u (0x%04X)\n", bf_hdr.n_bitmap_offset, bf_hdr.n_bitmap_offset);
        printf("DIB header size:  %u\n", bf_hdr.n_header_size);
        printf("image width:      %d\n", bf_hdr.n_width);
        printf("image height:     %d\n", bf_hdr.n_height);
        printf("planes:           %hu\n", bf_hdr.n_planes);
        printf("bits/pixel:       %hu\n", bf_hdr.n_bpp);
        printf("compression type: %hu\n", bf_hdr.compression_type);
        printf("bitmap size:      %u\n", bf_hdr.n_bitmap_size);
        printf("X resolution:     %d\n", bf_hdr.x_resolution);
        printf("Y resolution:     %d\n", bf_hdr.y_resolution);
        printf("colors:           %u\n", bf_hdr.n_colors);
        printf("important colors: %u\n", bf_hdr.n_important_colors);
    }
    catch (std::exception& e) {
        fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }

    return 0;
}
