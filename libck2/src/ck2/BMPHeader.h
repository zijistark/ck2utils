#ifndef __LIBCK2_BMP_HEADER_H__
#define __LIBCK2_BMP_HEADER_H__

#include "common.h"


_CK2_NAMESPACE_BEGIN;


// NOTE: we currently assume that if the compiler isn't MSVC that it must be gcc. however, I believe clang also
// supports the __attribute__((packed)) syntax, so that should also be good to go.

// BTW, BMPHeader is "packed" (i.e., absolute literal memory alignment in the structure -- nothing is padded for
// memory alignment) so that it can be overlaid onto a raw byte array without any further data marshalling.

#ifdef _MSC_VER
    #pragma pack(push, 1)
#endif

// NOTE: we currently assume that we're only dealing with little endian byte order architectures, mainly because
// one is hard-pressed to find a big endian architecture these days.

struct BMPHeader
{
    static constexpr uint16_t MAGIC = 0x4D42;

    // data layout:
    uint16_t magic; // should be 0x4D42 ("BM", accounting for endianness)
    uint32_t n_file_size; // bytes (entire file)
    uint16_t reserved1;
    uint16_t reserved2;
    uint32_t n_bitmap_offset; // byte offset into file that starts actual bitmap image data
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
}
#ifndef _MSC_VER
    __attribute__ ((packed))
#endif
; // close the struct definition statement

#ifdef _MSC_VER
    #pragma pack(pop)
#endif


_CK2_NAMESPACE_END;
#endif
