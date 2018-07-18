#ifndef __LIBCK2_COLOR_H__
#define __LIBCK2_COLOR_H__

#include "common.h"


_CK2_NAMESPACE_BEGIN;


//TODO: compare default MSVC code generation for `rgb` vs. packing `rgb` to fit within a 32-bit word
//#pragma pack(push, 1)


struct rgb {
    uint8_t r;
    uint8_t g;
    uint8_t b;

    rgb() = delete; // no such thing as a default color

    constexpr rgb(uint red, uint green, uint blue) :
        r(static_cast<uint8_t>(red)),
        g(static_cast<uint8_t>(green)),
        b(static_cast<uint8_t>(blue)) { }
 
    constexpr rgb(uint rgb) :
        r(static_cast<uint8_t>( (rgb >> 16) & 0xFF )),
        g(static_cast<uint8_t>( (rgb >> 8) & 0xFF )),
        b(static_cast<uint8_t>( rgb & 0xFF )) { }

    constexpr operator uint() const noexcept { // implicit conversion to unsigned int with 24-bit RGB value
        return (static_cast<uint>(r) << 16) | (static_cast<uint>(g) << 8) | b;
    }

    constexpr uint8_t red()   const { return r; }
    constexpr uint8_t green() const { return g; }
    constexpr uint8_t blue()  const { return b; }
    
    constexpr bool operator==(const rgb& c) const noexcept {
        return (r == c.r && g == c.g && b == c.b);
    }
};

//#pragma pack(pop)

_CK2_NAMESPACE_END;

/* inject std::hash<rgb> specialization */

namespace std {
    template<> struct hash<ck2::rgb> {
        typedef ck2::rgb argument_type;
        typedef size_t result_type;
        result_type operator()(argument_type const& c) const { return std::hash<unsigned int>{}( c ); }
    };
}

#endif
