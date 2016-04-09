// -*- c++ -*-

#ifndef _MDH_PROVSETUP_H_
#define _MDH_PROVSETUP_H_

#include <boost/filesystem.hpp>

#include <string>
#include <vector>

namespace fs = boost::filesystem;

class provsetup {

public:

    struct row {
        std::string title;
        int max_settlements;
        std::string terrain;

        row() : max_settlements(-1) {}
    };

    std::vector<row> row_vec;

    provsetup(const fs::path& path);
    void write(const fs::path& path);
};


#endif
