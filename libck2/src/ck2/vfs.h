// -*- c++ -*-

#pragma once
#include "common.h"

#include <vector>
#include <string>
#include <boost/filesystem.hpp>


_CK2_NAMESPACE_BEGIN;


namespace fs = boost::filesystem;

class vfs {
    std::vector<fs::path> _path_stack;

public:
    vfs(const fs::path& base_path) : _path_stack({ base_path }) {}
    vfs() {}

    void push_mod_path(const fs::path& p) { _path_stack.push_back(p); }

    bool resolve_path(fs::path* p_real_path, const fs::path& virtual_path) const {
        /* search path vector for a filesystem hit in reverse */
        for (auto i = _path_stack.crbegin(); i != _path_stack.crend(); ++i)
            if (fs::exists( *p_real_path = *i / virtual_path ))
                return true;
        return false;
    }

    /* a more convenient accessor which auto-throws on a nonexistent path */
    fs::path operator[](const fs::path& virtual_path) const {
        fs::path p;
        if (!resolve_path(&p, virtual_path))
            throw std::runtime_error("Missing game file: " + virtual_path.string());
        return p;
    }

    /* std::string / c-string convenience overloads */

    bool resolve_path(fs::path* p_real_path, const std::string& virtual_path) const {
        return resolve_path(p_real_path, fs::path(virtual_path));
    }

    bool resolve_path(fs::path* p_real_path, const char* virtual_path) const {
        return resolve_path(p_real_path, fs::path(virtual_path));
    }

    fs::path operator[](const std::string& virtual_path) const { return (*this)[fs::path(virtual_path)]; }
    fs::path operator[](const char* virtual_path) const        { return (*this)[fs::path(virtual_path)]; }
};


_CK2_NAMESPACE_END;
