#include "BMPHeader.h"
#include "fmt/format.h"


_CK2_NAMESPACE_BEGIN;


void BMPHeader::print(FILE* out) const {
    fmt::print(out, "BMP Header ({} bytes)\n", sizeof(*this));
    fmt::print(out, "==========================\n");
    fmt::print(out, "Magic:      0x{:04X}\n", magic);
    fmt::print(out, "FileSz:     {}\n", n_file_size);
    fmt::print(out, "Reserved1:  {}\n", reserved1);
    fmt::print(out, "Reserved2:  {}\n", reserved2);
    fmt::print(out, "MapOffset:  {}\n", n_bitmap_offset);
    fmt::print(out, "HeaderSz:   {}\n", n_header_size);
    fmt::print(out, "Width:      {}\n", n_width);
    fmt::print(out, "Height:     {}\n", n_height);
    fmt::print(out, "NumPlanes:  {}\n", n_planes);
    fmt::print(out, "BPP:        {}\n", n_bpp);
    fmt::print(out, "Compress:   {}\n", compression_type);
    fmt::print(out, "MapSz:      {}\n", n_bitmap_size);
    fmt::print(out, "XRes:       {}\n", x_resolution);
    fmt::print(out, "YRes:       {}\n", y_resolution);
    fmt::print(out, "Colors:     {}\n", n_colors);
    fmt::print(out, "ImptColors: {}\n", n_important_colors);
}


_CK2_NAMESPACE_END;
