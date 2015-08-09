
#include "province_map.h"
#include "error.h"

#include <cstdio>
#include <cstring>
#include <cerrno>
#include <cstdlib>
#include <cassert>


static const uint16_t BMP_MAGIC = 0x4D42;


struct bmp_file_header {
    uint16_t magic; // should be 0x424D ("BM")
    uint32_t n_file_size; // bytes (entire file)
    uint16_t reserved1;
    uint16_t reserved2;
    uint32_t n_bitmap_offset; // byte offset into file that starts actual bitmap image data
} __attribute__ ((packed));


struct bmp_info_header {
    uint32_t n_header_size; // bytes that this header takes (40 for a BITMAPINFOHEADER such as this)
    int32_t  n_width;
    int32_t  n_height; // if negative, bitmap uses top-to-bottom scan order rather than bottom-to-top
    uint16_t n_planes; // should be 1
    uint16_t n_bpp; // in our case, should be 24
    uint16_t compression_type; // should be 0 for BI_RGB (no compression)
    uint32_t n_bitmap_size; // 0 or size of raw bitmap image data section
    int32_t  x_resolution; // horizontal resolution (pixels/meter)
    int32_t  y_resolution; // vertical resolution (pixels/meter)
    uint32_t n_colors; // 0 for 2^n_bpp, else palette size
    uint32_t n_important_colors; // should be 0
} __attribute__ ((packed));


province_map::province_map(const default_map& dm)
    : _p_map(nullptr),
      _n_width(0),
      _n_height(0) {
    
    color2id_map_t color2id_map;
    fill_color2id_map(color2id_map, dm);

    const char* path = dm.provinces_path().c_str();
    FILE* f;

    if ( (f = fopen(path, "rb")) == nullptr )
        throw va_error("could not open file: %s: %s", strerror(errno), path);

    bmp_file_header bf_hdr;
    bmp_info_header bi_hdr;
    errno = 0;

    if ( fread(&bf_hdr, sizeof(bf_hdr), 1, f) < 1 ) {
        if (errno)
            throw va_error("failed to read bitmap file header: %s: %s", strerror(errno), path);
        else
            throw va_error("unexpected EOF: %s", path);
    }

    if ( fread(&bi_hdr, sizeof(bi_hdr), 1, f) < 1 ) {
        if (errno)
            throw va_error("failed to read bitmap info header: %s: %s", strerror(errno), path);
        else
            throw va_error("unexpected EOF after bitmap file header: %s", path);
    }

    if (bf_hdr.magic != BMP_MAGIC)
        throw va_error("unsupported bitmap file type (magic=%04x): %s", bf_hdr.magic, path);

    assert( bi_hdr.n_header_size >= sizeof(bi_hdr) );
    assert( bi_hdr.n_width > 0 );
    assert( bi_hdr.n_height > 0 ); // TODO (though not sure if game supports top-to-bottom scan order)
    assert( bi_hdr.n_planes == 1 );
    assert( bi_hdr.n_bpp == 24 );
    assert( bi_hdr.compression_type == 0 );
    assert( bi_hdr.n_colors == 0 );
    assert( bi_hdr.n_important_colors == 0 );

    uint n_width = bi_hdr.n_width;
    uint n_height = bi_hdr.n_height;

    /* calculate row size with 32-bit alignment padding */
    uint n_row_sz = (bi_hdr.n_bpp * n_width + 31) / 32;
    n_row_sz *= 4;

    if (bi_hdr.n_bitmap_size)
        assert( bi_hdr.n_bitmap_size == n_row_sz * n_height );

    /* seek past any other bytes and directly to offset of pixel array (if needed). */
    if ( fseek(f, bf_hdr.n_bitmap_offset, SEEK_SET) != 0 )
        throw va_error("failed to seek to raw bitmap data (offset=%lu): %s: %s",
                       bf_hdr.n_bitmap_offset,
                       strerror(errno),
                       path);

    /* read bitmap image data (pixel array), row by row, in bottom-to-top raster scan order */

    unsigned char row_buf[n_row_sz];

    for (uint row = 0; row < n_height; ++row) {
        
        if ( fread(&row_buf, n_row_sz, 1, f) < 1 ) {
            if (errno)
                throw va_error("failed to read bitmap file header: %s: %s", strerror(errno), path);
            else
                throw va_error("unexpected EOF while reading raw bitmap data: %s", path);
        }

        const uint y = n_height-1 - row;

        for (uint x = 0; x < n_width; ++x) {
            const unsigned char* p = &row_buf[3*x];
            uint32_t color = make_color(p[2], p[1], p[0]);
            auto i = color2id_map.find(color);

            if (i == color2id_map.end())
                throw va_error("unexpected color RGB(%hhu, %hhu, %hhu) in provinces bitmap at (%u, %u)",
                               p[2], p[1], p[0], x, y);

            printf("%u\n", i->second);
        }
    }

    fclose(f);
}


void province_map::fill_color2id_map(color2id_map_t& m, const default_map& dm) {

    const char* path = dm.definitions_path().c_str();
    FILE* f;

    if ( (f = fopen(path, "rb")) == nullptr )
        throw va_error("could not open file: %s: %s", strerror(errno), path);

    char buf[128];
    char* p = &buf[0];
    uint n_line = 0;
    
    if ( fgets(p, sizeof(buf), f) == nullptr ) // consume CSV header
        return;
    
    while ( fgets(p, sizeof(buf), f) != nullptr ) {

        ++n_line;

        char* n_str[4];
        n_str[0] = strtok(p, ";");

        for (uint x = 1; x < 4; ++x)
            n_str[x] = strtok(nullptr, ";");

        uint n[4];
        char* p_end;

        for (uint x = 0; x < 4; ++x) {
            n[x] = strtol(n_str[x], &p_end, 10);
            assert( *p_end == '\0' );
        }

        m.emplace( make_color(n[1], n[2], n[3]), static_cast<uint16_t>(n[0]) );

        if (n[0] == dm.max_province_id())
            break;
    }

    fclose(f);
}
