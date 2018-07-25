#ifndef __LIBCK2_FILESYSTEM_H__
#define __LIBCK2_FILESYSTEM_H__

#include "common.h"
#include <boost/filesystem.hpp>
#include <string>


// this header exists foremost as a compilation proxy between the different not-quite-there-yet C++17
// implementations of <filesystem> (or <experimental/filesytem>) and Boost.

// after that, it's convenience stuff for users of FS-related things.


_CK2_NAMESPACE_BEGIN;


namespace fs = boost::filesystem;


struct PathError : public Error {
    PathError(const std::string& msg_, const fs::path& path_) : Error(msg_), _path(path_) {}
    auto&       path()       noexcept { return _path; }
    const auto& path() const noexcept { return _path; }

protected:
    fs::path _path;
};


struct PathNotFoundError : public PathError {
    PathNotFoundError(const fs::path& path_)
        : PathError(fmt::format("Path not found: {}", path_.generic_string()), path_) {}
};


struct PathTypeError : public PathError {
    PathTypeError(const fs::path& path_) // TODO: tell the user what type of file it does point to vs. expected
        : PathError(fmt::format("Path points to unexpected file type (e.g., directory vs. regular file): {}",
                                path_.generic_string()), path_) {}
};


_CK2_NAMESPACE_END;
#endif
