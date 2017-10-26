
#include "adjacencies_file.h"
#include <ck2/error.h>

#include <stdexcept>
#include <memory>
#include <fstream>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <cerrno>

typedef std::unique_ptr<std::FILE, int (*)(std::FILE *)> unique_file_ptr;


static int column_to_int(const char* col, const char* col_name, unsigned int n_line, const char* path) {
    /* allow a special case where the column is completely unspecified to resolve to the invalid
     * province ID of 0 */
    if (*col == '\0') return 0;

    int r = atoi(col);

    if (r == 0) // 0 is not a valid input integer for this file type (and also atoi's error return code)
        throw ck2::va_error("Value in column '%s' not a valid integer input on line %u: %s", col_name, n_line, path);

    return r;
}


adjacencies_file::adjacencies_file(const fs::path& in_path) {
    const std::string spath = in_path.string();
    const char* path = spath.c_str();

    unique_file_ptr ufp( std::fopen(path, "rb"), std::fclose );

    if ( ufp.get() == nullptr )
        throw ck2::va_error("Could not open adjacencies file: %s: %s", strerror(errno), path);

    char buf[256];
    unsigned int n_line = 0;

    if ( fgets(&buf[0], sizeof(buf), ufp.get()) == nullptr ) // consume CSV header
        throw std::runtime_error("Adjacencies file lacks at least 1 line of text (header): " + spath);

    ++n_line;

    while ( fgets(&buf[0], sizeof(buf), ufp.get()) != nullptr ) {
        ++n_line;
        char* p = &buf[0];

        if (*p == '#')
            continue; // not sure if entries can be commented-out, but we'll support it minimally

        const int NUM_COLS = 9;
        char* cols[NUM_COLS];

        cols[0] = p;

        for (int c = 1; c < NUM_COLS; ++c) {
            char* prev_end = strchr(cols[c-1], ';');

            if (prev_end == nullptr)
                throw ck2::va_error("Adjacency entry on line %u has insufficient amount of columns: %s", n_line, path);

            *prev_end = '\0';
            cols[c] = prev_end + 1;
        }

        /* trim potential EOL from final column */
        p = strchr(cols[NUM_COLS-1], '\r');
        if (p != nullptr) *p = '\0';
        p = strchr(cols[NUM_COLS-1], '\n');
        if (p != nullptr) *p = '\0';

        /* add to end of internal list of adjacencies */
        _vec.emplace_back(column_to_int(cols[0], "From",    n_line, path),
                          column_to_int(cols[1], "To",      n_line, path),
                          column_to_int(cols[3], "Through", n_line, path),
                          cols[2],
                          cols[8]);
    }
}


void adjacencies_file::write(const fs::path& out_path) {
    const std::string& spath = out_path.string();
    std::ofstream os(spath);

    if (!os)
        throw std::runtime_error("Adjacencies file could not be opened for output: " + spath);

    os << "From;To;Type;Through;-1;-1;-1;-1;Comment\n";

    for (const auto& adj : _vec) {
        if (adj.deleted) continue;

        if (adj.from) os << adj.from; // treat 0-value as blank
        os << ';';
        if (adj.to) os << adj.to; // treat 0-value as blank
        os << ';' << adj.type << ';';
        if (adj.through) os << adj.through; // treat 0-value as blank
        os << ";-1;-1;-1;-1;" << adj.comment << "\n";
    }
}
