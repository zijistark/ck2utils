
#ifndef _MDH_PROVINCE_MAP_H_
#define _MDH_PROVINCE_MAP_H_

#include "default_map.h"

#include <string>
#include <cstdint>
#include <unordered_map>


class province_map {
    uint16_t* _p_map;
    uint _n_width;
    uint _n_height;

    typedef std::unordered_map<uint32_t, uint16_t> color2id_map_t;
    void fill_color2id_map(color2id_map_t&, const default_map&);

    template<typename T>
    static uint32_t make_color(T r, T g, T b) noexcept {
        return (static_cast<uint32_t>(b)<<24) |
               (static_cast<uint32_t>(g)<<16) |
               (static_cast<uint32_t>(r)<<8);
    }

public:
    province_map(const default_map&);

    static const uint16_t TYPE_OCEAN = (1<<16)-1;
    static const uint16_t TYPE_IMPASSABLE = (1<<16)-2;

    uint width() const noexcept { return _n_width; }
    uint height() const noexcept { return _n_height; }

    uint16_t at(uint x, uint y) const noexcept {
        return _p_map[ y*_n_width + x ];
    }

    uint16_t* map() const noexcept { return _p_map; }
};


#endif
