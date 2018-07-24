#ifndef __LIBCK2_COLOR_H__
#define __LIBCK2_COLOR_H__

#include "common.h"


_CK2_NAMESPACE_BEGIN;


//TODO: compare default MSVC code generation for `rgb` vs. packing `rgb` to fit within a 32-bit word
//#pragma pack(push, 1)


struct RGB {
    uint8_t r;
    uint8_t g;
    uint8_t b;

    constexpr RGB(uint red, uint green, uint blue) :
        r(static_cast<uint8_t>(red)),
        g(static_cast<uint8_t>(green)),
        b(static_cast<uint8_t>(blue)) {}
 
    constexpr RGB(uint rgb) :
        r(static_cast<uint8_t>( (rgb >> 16) & 0xFF )),
        g(static_cast<uint8_t>( (rgb >> 8) & 0xFF )),
        b(static_cast<uint8_t>( rgb & 0xFF )) {}

    constexpr operator uint() const noexcept { // implicit conversion to unsigned int with 24-bit RGB value
        return (static_cast<uint>(r) << 16) | (static_cast<uint>(g) << 8) | b;
    }

    constexpr auto red()   const noexcept { return r; }
    constexpr auto green() const noexcept { return g; }
    constexpr auto blue()  const noexcept { return b; }
    
    constexpr bool operator==(const RGB& c) const noexcept {
        return (r == c.r && g == c.g && b == c.b);
    }
};

//#pragma pack(pop)

_CK2_NAMESPACE_END;

/* inject std::hash<rgb> specialization */

namespace std {
    template<> struct hash<ck2::RGB> {
        typedef ck2::RGB argument_type;
        typedef size_t result_type;
        // TODO: try to find an actual 24-bit hash or something that will help improve this hash in an RGB context
        // or, rather, just fiddle with FNV-1a vs. other popular functions and see what happens. the most obvious
        // problem is that all the colors have their 8 MSBs all zeroed.
        result_type operator()(argument_type const& c) const { return std::hash<unsigned int>{}( c ); }
    };
}

#endif
