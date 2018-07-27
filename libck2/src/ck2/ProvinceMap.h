#ifndef __LIBCK2_PROVINCE_MAP_H__
#define __LIBCK2_PROVINCE_MAP_H__

#include "common.h"
#include "filesystem.h"
#include <memory>
#include <limits>


_CK2_NAMESPACE_BEGIN;


class DefinitionsTable;
class DefaultMap;
class VFS;


// A ProvinceMap class opens & processes the raw bitmap from 'provinces.bmp' & allocates it into a buffer(s) of
// 16-bit province IDs. It then provides read-only access to that mapping of IDs to raster (x, y) grid coordinates.
// Some province IDs at the very top of the ID range are reserved for useful classifications.

// API NOTE: Never assume the actual memory representation of the grid is indeed one big, rectangular grid. Ergo,
// always access grid contents via the operator(x, y) overload. [didn't feel like dealing with proxy overloads for
// operator[].]
//
// there will probably be a faster, layout-aware means of traversing the grid later.
struct ProvinceMap
{
    using id_t = uint16_t;

    ProvinceMap(const VFS&, const DefaultMap&, const DefinitionsTable&);

    static constexpr id_t PM_IMPASSABLE  = 0; // zero isn't a valid province ID, so reuse it
    static constexpr id_t PM_OCEAN       = std::numeric_limits<id_t>::max();
    static constexpr id_t PM_REAL_ID_CAP = std::numeric_limits<id_t>::max() - 1;

    auto width()  const noexcept { return _cols; }
    auto height() const noexcept { return _rows; }

    id_t&       operator()(uint x, uint y)       noexcept { return _map[ y * _cols + x ]; }
    id_t const& operator()(uint x, uint y) const noexcept { return _map[ y * _cols + x ]; }

private:
    unique_ptr<id_t[]> _map;
    uint _cols;
    uint _rows;
};


_CK2_NAMESPACE_END;
#endif
