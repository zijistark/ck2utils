#ifndef __LIBCK2_DATE_H__
#define __LIBCK2_DATE_H__

#include "common.h"


_CK2_NAMESPACE_BEGIN;


#ifdef _MSC_VER
    #pragma pack(push, 1)
#endif

class date {
    int16_t _y;
    int8_t  _m;
    int8_t  _d;

public:
    date(char* src); // only for use on mutable date-strings known to be well-formed
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

    friend std::ostream& operator<<(std::ostream& os, date d) {
        return os << (int)d.year() << '.' << (int)d.month() << '.' << (int)d.day();
    }
}
#ifndef _MSC_VER
    __attribute__ ((packed))
#endif
; // close the class definition statement

#ifdef _MSC_VER
    #pragma pack(pop)
#endif


_CK2_NAMESPACE_END;
#endif
