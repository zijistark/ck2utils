// -*- c++ -*-

#ifndef _MDH_BMP_FORMAT_H_
#define _MDH_BMP_FORMAT_H_


#include <cstdint>

static const uint16_t BMP_MAGIC = 0x4D42;


struct bmp_file_header {
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
} __attribute__ ((packed));



#endif
