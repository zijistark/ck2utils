
#ifndef _MDH_PROVINCE_MAP_H_
#define _MDH_PROVINCE_MAP_H_

#include "default_map.h"

#include <string>
#include <cstdint>
#include <unordered_map>


class province_map {
    struct block {
        /* 128-bit blocks of 8 pixels */
        static const uint SZ = 8;
        uint16_t id[SZ];
    };

    block* _p_blocks;
    uint _n_width;
    uint _n_height;

    typedef std::unordered_map<uint32_t, uint16_t> color2id_map_t;
    void fill_color2id_map(color2id_map_t&, const default_map&);

public:
    province_map(const default_map&);

    uint width() const noexcept { return _n_width; }
    uint height() const noexcept { return _n_height; }
    
    uint16_t at(uint x, uint y) const noexcept {
        return _p_blocks[ (y*_n_width + x) / block::SZ ].id[ x % block::SZ ];
    }
};


#endif
