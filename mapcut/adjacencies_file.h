// -*- c++ -*-

#pragma once

#include <boost/filesystem.hpp>
#include <vector>
#include <string>

namespace fs = boost::filesystem;


class adjacencies_file {
public:
    struct adjacency {
        int from;
        int to;
        int through;
        std::string type;
        std::string comment;
        bool deleted;

        adjacency(int _from, int _to, int _through, const std::string& _type, const std::string& _comment)
            : from(_from), to(_to), through(_through), type(_type), comment(_comment), deleted(false) { }
    };

private:
    typedef std::vector<adjacency> vec_t;
    vec_t _vec;

public:
    adjacencies_file(const fs::path&);
    void write(const fs::path&);

    /* give this type a container-like interface and C++11 range-based-for support */
    vec_t::size_type      size()  const noexcept { return _vec.size(); }
    bool                  empty() const noexcept { return size() == 0; }
    vec_t::iterator       begin()       noexcept { return _vec.begin(); }
    vec_t::iterator       end()         noexcept { return _vec.end(); }
    vec_t::const_iterator begin() const noexcept { return _vec.cbegin(); }
    vec_t::const_iterator end()   const noexcept { return _vec.cend(); }
};
