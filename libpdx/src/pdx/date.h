// -*- c++ -*-

#pragma once
#include "pdx_common.h"
#include "error_queue.h"


_PDX_NAMESPACE_BEGIN


#pragma pack(push, 1)

class date {
    int16_t _y;
    int8_t  _m;
    int8_t  _d;

public:
    date(char* src, const file_location&, error_queue&); // only for use on mutable date-strings known to be well-formed
    date(int16_t year, int8_t month, int8_t day) : _y(year), _m(month), _d(day) {}

    int16_t year()  const noexcept { return _y; }
    int8_t  month() const noexcept { return _m; }
    int8_t  day()   const noexcept { return _d; }

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
    return os << (int)d.year() << '.' << (int)d.month() << '.' << (int)d.day();
}
