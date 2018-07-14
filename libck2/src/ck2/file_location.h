#ifndef __LIBCK2_FILE_LOCATION_H__
#define __LIBCK2_FILE_LOCATION_H__

#include "common.h"
#include "filesystem.h"


_CK2_NAMESPACE_BEGIN;


class file_location {
    fs::path _path;
    uint     _line;

    // column index tracking will be added when we migrate from the flex scanner to a Ragel FSM scanner; we could
    // do it now, but it's more of a PITA.
    // uint column;

public:
    file_location(const fs::path& path = fs::path(), uint line = 0) : _path(path), _line(line) {}

    uint            line() const noexcept { return _line; }
    const fs::path& path() const noexcept { return _path; }

    void line(uint line)   noexcept { _line = line; }
    void path(const fs::path& path) { _path = path; }
};

// since file_location is quite verbose for such a common thing to be passing around, we actually use this alias:
using floc = file_location;


_CK2_NAMESPACE_END;
#endif
