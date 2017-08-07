// -*- c++ -*-

#pragma once
#include "common.h"


_CK2_NAMESPACE_BEGIN


class file_location {
    const char* _pathname;
    uint        _line;

    // column index tracking will be added when we migrate from the flex scanner to a quex scanner
    // uint column;

public:

    file_location(const char* path = "", uint line = 0) : _pathname(path), _line(line) {}

    const char* pathname() const noexcept { return _pathname; }
    uint        line()     const noexcept { return _line; }

    void set_pathname(const char* path) noexcept { _pathname = path; }
    void set_line(uint line)            noexcept { _line = line; }
};


// since file_location is quite verbose for such a common thing to be passing around, we actually use this alias:

using floc = file_location;


_CK2_NAMESPACE_END
