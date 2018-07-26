
#include "ProvinceMap.h"
#include "BMPHeader.h"
#include "FileLocation.h"
#include "Color.h"
#include "VFS.h"
#include "DefaultMap.h"
#include "DefinitionsTable.h"
#include <cstdio>
#include <cerrno>
#include <cstdlib>
#include <string>
#include <unordered_map>


_CK2_NAMESPACE_BEGIN;


ProvinceMap::ProvinceMap(const VFS& vfs, const DefaultMap& dm, const DefinitionsTable& def_tbl)
: _map(nullptr),
  _cols(0),
  _rows(0)
{
    /* map provinces.bmp color to province ID */
    std::unordered_map<RGB, uint16_t> color2id_map;

    for (const auto& row : def_tbl)
        color2id_map.emplace(row.color, row.id);

    const auto path = vfs["map" / dm.province_map_path()];
    const string spath = path.generic_string();

    // unique_file_ptr will automatically destroy/close its FILE* if we throw an exception (or return)
    unique_file_ptr ufp( std::fopen(spath.c_str(), "rb"), std::fclose );
    FILE* f = ufp.get();

    if (f == nullptr)
        throw Error("Failed to open file: {}: {}", strerror(errno), spath);

    BMPHeader bf_hdr;

    if (errno = 0; fread(&bf_hdr, sizeof(bf_hdr), 1, f) < 1)
    {
        if (errno)
            throw FLError(path, "Failed to read bitmap file header: {}", strerror(errno));
        else
            throw FLError(path, "Unexpected EOF while reading bitmap file header (likely a corrupt file)");
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

    _cols = bf_hdr.n_width;
    _rows = bf_hdr.n_height;

    /* calculate row size with 32-bit alignment padding */
    uint row_sz = 4 * ((bf_hdr.n_bpp * _cols + 31) / 32);

    if (bf_hdr.n_bitmap_size)
        assert( bf_hdr.n_bitmap_size == row_sz * _rows );

    /* allocate ID map */
    _map = std::make_unique<id_t[]>(_cols * _rows);

    /* seek past any other bytes and directly to offset of pixel array (if needed). */
    if (fseek(f, bf_hdr.n_bitmap_offset, SEEK_SET) != 0)
        throw FLError(path, "Failed to seek to raw bitmap data (offset={0:010X}/{0}): {1}",
                      bf_hdr.n_bitmap_offset,
                      strerror(errno));

    /* read bitmap image data (pixel array), row by row, in bottom-to-top raster scan order */

    auto row_buf = std::make_unique<uint8_t[]>(row_sz);

    for (uint row = 0; row < _rows; ++row)
    {
        if (errno = 0; fread(&row_buf, row_sz, 1, f) < 1)
        {
            if (errno)
                throw FLError(path, "Failed to read scanline #{} of bitmap data: {}", row, strerror(errno));
            else
                throw FLError(path, "Unexpected EOF while reading bitmap data");
        }

        const auto y = _rows - 1 - row;

        /* cache previous pixel's value & province ID */
        uint8_t  prev_b = 0;
        uint8_t  prev_g = 0;
        uint8_t  prev_r = 0;
        uint16_t prev_id = 0;

        for (uint x = 0; x < _cols; ++x)
        {
            const uint8_t* p = &row_buf[3*x];
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
            prev_id = _map[y*_cols + x] = id;
        }
    }
}


_CK2_NAMESPACE_END;
