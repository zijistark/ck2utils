// -*- c++ -*-

#pragma once
#include "common.h"


_CK2_NAMESPACE_BEGIN;


class file_location {
    uint        _line;
    const char* _pathname;

    // column index tracking will be added when we migrate from the flex scanner to a quex scanner; we could do it now,
    // but it's more of a PITA.
    // uint column;

public:

    file_location(const char* path = "", uint line = 0) : _line(line), _pathname(path) {}

    uint        line()     const noexcept { return _line; }
    const char* pathname() const noexcept { return _pathname; }

    void line(uint line)            noexcept { _line = line; }
    void pathname(const char* path) noexcept { _pathname = path; }
};


// since file_location is quite verbose for such a common thing to be passing around, we actually use this alias:

using floc = file_location;


_CK2_NAMESPACE_END;
