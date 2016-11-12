#pragma once

#include <cstdint>

#pragma pack(push, 1)

struct rgba_color {
    uint8_t r;
    uint8_t g;
    uint8_t b;
    uint8_t a;

    constexpr rgba_color(uint red, uint green, uint blue, uint alpha = 0) :
        r(static_cast<uint8_t>(red)),
        g(static_cast<uint8_t>(green)),
        b(static_cast<uint8_t>(blue)),
        a(static_cast<uint8_t>(alpha)) { }
 
    constexpr rgba_color(uint rgb, uint alpha = 0) :
        r(static_cast<uint8_t>( (rgb >> 16) & 0xFF )),
        g(static_cast<uint8_t>( (rgb >> 8) & 0xFF )),
        b(static_cast<uint8_t>( rgb & 0xFF )),
        a(static_cast<uint8_t>(alpha)) { }

    constexpr uint32_t to_rgba() const noexcept {
        return (static_cast<uint32_t>(r) << 24) | (static_cast<uint32_t>(g) << 16) | (static_cast<uint32_t>(b) << 8) | a;
    }
    constexpr uint32_t to_bgra() const noexcept {
        return (static_cast<uint32_t>(b) << 24) | (static_cast<uint32_t>(g) << 16) | (static_cast<uint32_t>(r) << 8) | a;
    }

    constexpr uint8_t red()   const { return r; }
    constexpr uint8_t green() const { return g; }
    constexpr uint8_t blue()  const { return b; }
    constexpr uint8_t alpha() const { return a; }

    constexpr bool operator==(const rgba_color& c) const noexcept {
        return (r == c.r && g == c.g && b == c.b && a == c.a);
    }
};

#pragma pack(pop)

/* inject std::hash<color> specialization */

namespace std {
    template<> struct hash<rgba_color> {
        typedef rgba_color argument_type;
        typedef size_t result_type;
        result_type operator()(argument_type const& c) const { return std::hash<uint32_t>{}( c.to_rgba() ); }
    };
}
