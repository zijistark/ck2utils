#ifndef __LIBCK2_FILESYSTEM_H__
#define __LIBCK2_FILESYSTEM_H__

#include "Error.h"
#include <boost/filesystem.hpp>
#include <string>


_CK2_NAMESPACE_BEGIN;


namespace fs = boost::filesystem;


class PathError : public Error {
protected:
    fs::path _path;
public:
    PathError() = delete;
    PathError(const fs::path& path, const std::string& msg) : Error(msg), _path(path) {}
    const auto& path() const noexcept { return _path; }
};

struct PathNotFoundError : public PathError {
    PathNotFoundError() = delete;
    PathNotFoundError(const fs::path& path)
        : PathError(path, fmt::format("path not found: %s", path.string())) {}
};

struct PathTypeError : public PathError {
    PathTypeError() = delete;
    PathTypeError(const fs::path& path)
        : PathError(path, fmt::format("path points to unexpected file type (e.g., directory vs. regular file): %s",
                                      path.string())) {}
};


_CK2_NAMESPACE_END;
#endif
