#ifndef __LIBCK2_FILESYSTEM_H__
#define __LIBCK2_FILESYSTEM_H__

#include "common.h"
#include <boost/filesystem.hpp>
#include <string>


_CK2_NAMESPACE_BEGIN;


namespace fs = boost::filesystem;


class PathError : public Error {
protected:
    fs::path _path;
public:
    PathError() = delete;
    ~PathError() noexcept {}
    PathError(const std::string& msg_, const fs::path& path_) : Error(msg_), _path(path_) {}
    const auto& path() const noexcept { return _path; }
};

struct PathNotFoundError : public PathError {
    PathNotFoundError() = delete;
    PathNotFoundError(const fs::path& path_)
        : PathError(fmt::format("path not found: {}", path_.generic_string()), path_) {}
};

struct PathTypeError : public PathError {
    PathTypeError() = delete;
    PathTypeError(const fs::path& path_)
        : PathError(fmt::format("path points to unexpected file type (e.g., directory vs. regular file): {}",
                                path_.generic_string()), path_) {}
};


_CK2_NAMESPACE_END;
#endif
