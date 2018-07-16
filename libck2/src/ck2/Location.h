#ifndef __LIBCK2_LOCATION_H__
#define __LIBCK2_LOCATION_H__

#include "common.h"
#include "fmt/format.h"
#include <string>


_CK2_NAMESPACE_BEGIN;


class Location {
    uint _line;
    uint _col;

public:
    Location(uint line_ = 0, uint col_ = 0) : _line(line_), _col(col_) {}

    auto line() const noexcept { return _line; }
    auto col()  const noexcept { return _col; }

    void line(uint line_) noexcept { _line = line_; }
    void col(uint col_)   noexcept { _col  = col_; }

    auto to_string() const {
        return (line() && col()) ? fmt::format("L{}:C{}", line(), col()) :
                                   (line()) ? fmt::format("L{}", line()) : "";
    }

    auto to_string_prefix() const {
        auto s = to_string();
        if (!s.empty()) s += ": ";
        return s;
    }

    auto to_string_suffix() const {
        return (line() && col()) ? fmt::format(" on line {}, column {}", line(), col()) :
                                   (line()) ? fmt::format(" on line {}", line()) : "";
    }
};


using Loc = Location;


_CK2_NAMESPACE_END;
#endif
