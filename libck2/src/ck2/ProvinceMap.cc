
#include "ProvinceMap.h"
#include "BMPHeader.h"
#include "FileLocation.h"
#include "Color.h"
#include <cstdio>
#include <cerrno>
#include <cstdlib>
#include <string>
#include <unordered_map>


_CK2_NAMESPACE_BEGIN;


ProvinceMap::ProvinceMap(const VFS& vfs, const DefaultMap& dm, const DefinitionsTable& def_tbl)
: _up_map(nullptr),
  _n_width(0),
  _n_height(0)
{
    /* map provinces.bmp color to province ID */
    std::unordered_map<RGB, uint16_t> color2id_map;

    for (const auto& row : def_tbl)
        color2id_map.emplace(row.color, row.id);

    const auto path = vfs["map" / dm.province_map_path()];
    const std::string spath = path.generic_string();

    // unique_file_ptr will automatically destroy/close its FILE* if we throw an exception (or return)
    typedef std::unique_ptr<std::FILE, int (*)(std::FILE *)> unique_file_ptr;
    unique_file_ptr ufp( std::fopen(spath.c_str(), "rb"), std::fclose );

    if (ufp.get() == nullptr)
        throw Error("Failed to open file: {}: {}", strerror(errno), spath);

    BMPHeader bf_hdr;

    if (errno = 0; fread(&bf_hdr, sizeof(bf_hdr), 1, ufp.get()) < 1)
    {
        if (errno)
            throw FLError(path, "Failed to read bitmap file header: {}", strerror(errno));
        else
            throw FLError(path, "Unexpected EOF while reading bitmap file header (corrupted?)");
    }

    if (bf_hdr.magic != BMPHeader::MAGIC)
        throw FLError(path, "Unsupported bitmap file type (magic={:06X} but want magic={:06X})",
                      bf_hdr.magic, BMPHeader::MAGIC);

    // TODO: all these not to be handled by compile-time assertions (every damn one from here one!)
    assert( bf_hdr.n_header_size >= 40 );
    assert( bf_hdr.n_width > 0 );
    assert( bf_hdr.n_height > 0 ); // TODO (though not sure if game supports top-to-bottom scan order)
    assert( bf_hdr.n_planes == 1 );
    assert( bf_hdr.n_bpp == 24 );
    assert( bf_hdr.compression_type == 0 );
    assert( bf_hdr.n_colors == 0 );
    assert( bf_hdr.n_important_colors == 0 );

    _n_width = bf_hdr.n_width;
    _n_height = bf_hdr.n_height;

    /* calculate row size with 32-bit alignment padding */
    uint n_row_sz = 4 * ((bf_hdr.n_bpp * _n_width + 31) / 32);

    if (bf_hdr.n_bitmap_size)
        assert( bf_hdr.n_bitmap_size == n_row_sz * _n_height );

    /* allocate ID map */
    _up_map = std::make_unique<uint16_t[]>(_n_width * _n_height);

    /* seek past any other bytes and directly to offset of pixel array (if needed). */
    if (fseek(ufp.get(), bf_hdr.n_bitmap_offset, SEEK_SET) != 0)
        throw FLError(path, "Failed to seek to raw bitmap data (offset={0:010X}/{0}): {1}",
                      bf_hdr.n_bitmap_offset,
                      strerror(errno));

    /* read bitmap image data (pixel array), row by row, in bottom-to-top raster scan order */

    uint8_t* p_row = new uint8_t[n_row_sz];

    for (uint row = 0; row < _n_height; ++row)
    {
        if (errno = 0; fread(p_row, n_row_sz, 1, ufp.get()) < 1)
        {
            if (errno)
                throw FLError(path, "Failed to read scanline #{} of bitmap data: {}", row, strerror(errno));
            else
                throw FLError(path, "Unexpected EOF while reading bitmap data");
        }

        const uint y = _n_height - 1 - row;

        /* cache previous pixel's value & province ID */
        uint8_t  prev_b = 0;
        uint8_t  prev_g = 0;
        uint8_t  prev_r = 0;
        uint16_t prev_id = 0;

        for (uint x = 0; x < _n_width; ++x)
        {
            const uint8_t* p = &p_row[3*x];
            uint16_t id;

            if (p[0] == 0xFF && p[1] == 0xFF && p[2] == 0xFF)
                id = PM_OCEAN;
            else if (p[0] == 0x00 && p[1] == 0x00 && p[2] == 0x00)
                id = PM_IMPASSABLE;
            else if (x > 0 && p[0] == prev_b && p[1] == prev_g && p[2] == prev_r)
                id = prev_id; // save time at the bottleneck of the hash table lookup due to color locality
            else
            {
                if (auto it = color2id_map.find({ p[2], p[1], p[0] }); it != color2id_map.end())
                    id = it->second;
                else
                    throw FLError(path, "Unexpected color RGB(%hhu, %hhu, %hhu) in provinces bitmap at (%u, %u)",
                                  p[2], p[1], p[0], x, y);
            }

            prev_b = p[0];
            prev_g = p[1];
            prev_r = p[2];
            prev_id = _up_map[y*_n_width + x] = id;
        }
    }
}


_CK2_NAMESPACE_END;
