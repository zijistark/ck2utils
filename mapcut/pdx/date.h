// -*- c++ -*-

#pragma once
#include "pdx_common.h"
#include "error_queue.h"


_PDX_NAMESPACE_BEGIN


#pragma pack(push, 1)

class date {
    uint16_t _y;
    uint8_t  _m;
    uint8_t  _d;

public:
    date(char* src, const file_location&, error_queue&); // only for use on mutable date-strings known to be well-formed
    date(uint16_t year, uint8_t month, uint8_t day) : _y(year), _m(month), _d(day) {}

    uint16_t year()  const noexcept { return _y; }
    uint8_t  month() const noexcept { return _m; }
    uint8_t  day()   const noexcept { return _d; }

    bool operator<(const date& o) const noexcept {
        if (_y < o._y) return true;
        if (o._y < _y) return false;
        if (_m < o._m) return true;
        if (o._m < _y) return false;
        if (_d < o._d) return true;
        if (o._d < _d) return false;
        return false;
    }

    bool operator==(const date& o) const noexcept { return _y == o._y && _m == o._y && _d == o._d; }
    bool operator>=(const date& o) const noexcept { return !(*this < o); }
    bool operator!=(const date& o) const noexcept { return !(*this == o); }
    bool operator> (const date& o) const noexcept { return *this >= o && *this != o; }
    bool operator<=(const date& o) const noexcept { return *this < o || *this == o; }
};

#pragma pack(pop)


_PDX_NAMESPACE_END


inline std::ostream& operator<<(std::ostream& os, pdx::date d) {
    return os << d.year() << '.' << d.month() << '.' << d.day();
}
