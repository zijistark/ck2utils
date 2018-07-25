#ifndef __LIBCK2_LOCATION_H__
#define __LIBCK2_LOCATION_H__

#include "common.h"
#include "fmt/format.h"
#include <string>


_CK2_NAMESPACE_BEGIN;


class Location {
public:
    Location(uint line_ = 0, uint col_ = 0) : _line(line_), _col(col_) {}

    /* getters */
    auto line() const noexcept { return _line; }
    auto col()  const noexcept { return _col; }

    /* setters */
    void line(uint line_) noexcept { _line = line_; }
    void col(uint col_)   noexcept { _col  = col_; }

    /* stringification */
    auto to_string() const
    {
        return (_line && _col) ? fmt::format("L{}:C{}", _line, _col) :
                       (_line) ? fmt::format("L{}", _line) :
                                 "";
    }

    auto to_string_prefix() const
    {
        auto s = to_string();
        if (!s.empty()) s += ": ";
        return s;
    }

    auto to_string_suffix() const
    {
        return (_line && _col) ? fmt::format(" on line {}, column {}", _line, _col) :
                       (_line) ? fmt::format(" on line {}", _line)
                               : "";
    }

private:
    uint _line;
    uint _col;
};


using Loc = Location;


_CK2_NAMESPACE_END;
#endif
