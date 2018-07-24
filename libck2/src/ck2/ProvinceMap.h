#ifndef __LIBCK2_PROVINCES_MAP_H__
#define __LIBCK2_PROVINCES_MAP_H__

#include "common.h"
#include "VFS.h"
#include "DefaultMap.h"
#include "DefinitionsTable.h"
#include "filesystem.h"
#include <memory>
#include <limits>


_CK2_NAMESPACE_BEGIN;


// A ProvinceMap class opens & processes the raw bitmap from 'provinces.bmp' & allocates it into a buffer(s) of
// 16-bit province IDs. It then provides read-only access to that mapping of IDs to raster (x, y) grid coordinates.
// Some province IDs at the very top of the ID range are reserved for useful classifications.

// API NOTE: Never assume the actual memory representation of the grid is indeed one big, rectangular grid. Ergo,
// always access grid contents via the operator(x, y) overload. [didn't feel like dealing with proxy overloads for
// operator[].]
//
// there will probably be a faster, layout-aware means of traversing the grid later.
class ProvinceMap
{
public:
    ProvinceMap() = delete;
    ProvinceMap(const VFS&, const DefaultMap&, const DefinitionsTable&);

    static constexpr uint16_t PM_IMPASSABLE  = 0; // zero isn't a valid province ID, so reuse it
    static constexpr uint16_t PM_OCEAN       = std::numeric_limits<uint16_t>::max();
    static constexpr uint16_t PM_REAL_ID_CAP = std::numeric_limits<uint16_t>::max() - 1;

    auto width()  const noexcept { return _n_width; }
    auto height() const noexcept { return _n_height; }

    uint16_t&       operator()(uint x, uint y)       noexcept { return _up_map[ y*_n_width + x ]; }
    uint16_t const& operator()(uint x, uint y) const noexcept { return _up_map[ y*_n_width + x ]; }

private:
    std::unique_ptr<uint16_t[]> _up_map;
    uint _n_width;
    uint _n_height;
};


_CK2_NAMESPACE_END;
#endif
