#ifndef __LIBCK2_BMP_HEADER_H__
#define __LIBCK2_BMP_HEADER_H__

#include "common.h"
#include <cstdio>


_CK2_NAMESPACE_BEGIN;


// Apparently GCC 7.3 on MinGW64 is only paying attention to these 'pack' pragmas (which are traditionally the MSVC
// way to override data alignment & packing choices of the compiler) while actually _ignoring_ GCC's traditional
// __attribute__((packed)) system for expressing the same stuff. IDEK, man.

// TODO: Investigate this further so that we can be as portable as we'd like to be for this library. Particularly:
// A) Does GCC just support the MSVC pragmas on all platforms now? If so, which version added this, because we
//    should just use whatever approach is unified (though I personally prefer GCC-style attributes to pragmas).
// B) Does Clang support these pragmas?

// Explanation of packing pragmas:
//
// Until we pop this pragma, `pack` shall be set to 1, which means that every variable/class declaration
// recursively encountered will be "packed into place" by the compiler on 1-byte boundaries (i.e., maximum possible
// packing with no ability for the compiler to add any padding bytes to align data — in contrast, one could specify
// 2 and the compiler would be allowed to add a padding byte to an inconveniently placed 'char' variable in order
// to at least make it accessible on a 16-bit memory address if the compiler thinks it will actually improve any
// performance). Full documentation is on MSDN somewhere, although I guess that w/ GCC now supporting it at least
// on the MinGW-64 port, there's probably plenty of other docs too.

#pragma pack(push, 1)

struct BMPHeader
{
    static constexpr uint16_t MAGIC = 0x4D42;
    // file header:
    uint16_t magic; // should be 0x4D42 ("BM", accounting for endianness)
    uint32_t n_file_size; // bytes (entire file)
    uint16_t reserved1;
    uint16_t reserved2;
    uint32_t n_bitmap_offset; // byte offset into file that starts actual bitmap image data
    // DIB header:
    uint32_t n_header_size; // bytes that this header takes (40 for a BITMAPINFOHEADER such as this)
    int32_t  n_width;
    int32_t  n_height; // if negative, bitmap uses top-to-bottom scan order rather than bottom-to-top
    uint16_t n_planes; // should be 1
    uint16_t n_bpp; // in our case, should be 24
    uint32_t compression_type; // should be 0 for BI_RGB (no compression)
    uint32_t n_bitmap_size; // 0 or size of raw bitmap image data section
    int32_t  x_resolution; // horizontal resolution (pixels/meter)
    int32_t  y_resolution; // vertical resolution (pixels/meter)
    uint32_t n_colors; // 0 for 2^n_bpp, else palette size
    uint32_t n_important_colors; // should be 0

    void print(FILE* out = stderr) const;
};

#pragma pack(pop)


_CK2_NAMESPACE_END;
#endif
