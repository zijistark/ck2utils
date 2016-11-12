// -*- c++ -*-

#ifndef _MDH_MOD_VFS_H_
#define _MDH_MOD_VFS_H_

#include <stdexcept>
#include <string>
#include <vector>
#include <boost/filesystem.hpp>

namespace fs = boost::filesystem;

class mod_vfs {
    std::vector<fs::path> _path_stack;

public:
    mod_vfs(const fs::path& base_path) : _path_stack( { base_path } ) { }
    mod_vfs() { }

    void push_mod_path(const fs::path& p) { _path_stack.push_back(p); }

    bool resolve_path(fs::path* p_real_path, const fs::path& virtual_path) const {
        /* search path vector for a filesystem hit in reverse */
        for (auto i = _path_stack.crbegin(); i != _path_stack.crend(); ++i)
            if (fs::exists( *p_real_path = *i / virtual_path.native() ))
                return true;
        return false;
    }

    /* a more convenient accessor which auto-throws on a nonexistent path */
    fs::path operator[](const fs::path& virtual_path) const {
        fs::path p;
        if (!resolve_path(&p, virtual_path))
            throw std::runtime_error("missing game file: " + virtual_path.string());
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


#endif
