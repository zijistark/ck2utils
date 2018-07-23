#ifndef __LIBCK2_FILE_LOCATION_H__
#define __LIBCK2_FILE_LOCATION_H__

#include "common.h"
#include "Error.h"
#include "Location.h"
#include "filesystem.h"
#include <utility>


_CK2_NAMESPACE_BEGIN;


class FileLocation : public Location {
    fs::path _path;
public:
    FileLocation(const fs::path& path_, const Location& loc_) : Location(loc_), _path(path_) {}
    FileLocation(const fs::path& path_, uint line_ = 0, uint col_ = 0) : Location(line_, col_), _path(path_) {}

    auto const& path() const noexcept { return _path; }
    auto&       path()       noexcept { return _path; }

    auto to_string() const
    {
        auto loc_s = Location::to_string();
        return (loc_s.empty()) ? path().generic_string() :
                                 path().generic_string() + ":" + loc_s;
    }

    auto to_string_prefix() const { return to_string() + ": "; }

    auto to_string_suffix() const
    {
        return Location::to_string_suffix() + fmt::format(" in '{}'", path().generic_string());
    }
};


class FLError : public Error {
    FileLocation _fl;
public:
    FLError() = delete;
    ~FLError() noexcept {}

    FLError(const FileLocation& fl, const std::string& msg)
        : Error( fl.to_string_prefix() + msg ), _fl(fl) {}

    template<typename... Args>
    FLError(const FileLocation& fl, str_view format, const Args& ...args)
        : Error( fl.to_string_prefix() + fmt::vformat(format, fmt::make_format_args(args...)) ), _fl(fl) {}

    const auto& floc() const noexcept { return _fl; }
};


using FLoc = FileLocation;


_CK2_NAMESPACE_END;
#endif
