#ifndef __LIBCK2_FILE_LOCATION_H__
#define __LIBCK2_FILE_LOCATION_H__

#include "common.h"
#include "Error.h"
#include "Location.h"
#include "filesystem.h"


_CK2_NAMESPACE_BEGIN;


class FileLocation : public Location {
    using Base = Location;
public:
    FileLocation(const fs::path& path_, const Location& loc_) : Base(loc_), _path(path_) {}
    FileLocation(const fs::path& path_, uint line_ = 0, uint col_ = 0) : Base(line_, col_), _path(path_) {}

    auto const& path() const noexcept { return _path; }
    auto&       path()       noexcept { return _path; }

    auto to_string() const
    {
        auto ls = Base::to_string();
        return ls.empty() ? _path.generic_string() : _path.generic_string() + ":" + ls;
    }

    auto to_string_prefix() const { return to_string() + ": "; }

    auto to_string_suffix() const {
        return Base::to_string_suffix() + fmt::format(" in '{}'", _path.generic_string());
    }

private:
    fs::path _path;
};


using FLoc = FileLocation;


class FLError : public Error {
    using Base = Error;
public:
    auto const& floc() const noexcept { return _fl; }
    auto&       floc()       noexcept { return _fl; }

    FLError(const FLoc& fl_, const string& msg)
        : Base(fl_.to_string_prefix() + msg), _fl(fl_) {}

    template<typename... Args>
    FLError(const FLoc& fl_, string_view format, const Args& ...args)
        : Base(fl_.to_string_prefix() + fmt::vformat(format, fmt::make_format_args(args...))), _fl(fl_) {}

private:
    FLoc _fl;
};


_CK2_NAMESPACE_END;
#endif
