
#include "AdjacenciesFile.h"

#include <stdexcept>
#include <memory>
#include <fstream>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <cerrno>


_CK2_NAMESPACE_BEGIN;


static uint col_to_province_id(const FLoc& fl, const char* col, const str_view& col_name, const DefaultMap& dm)
{
    /* allow a special case where the column is completely unspecified to resolve to the invalid
     * province ID of 0
     *
     * NOTE here from 2018: I see no examples of this, but I'm guessing it's related to "wormholes."
     */
    if (*col == '\0') return 0;

    long l = strtol(n_str[x], &col, 10);

    if (*col)
        throw FLError(fl, "Malformed integer value in CSV column '{}' (should be a province ID)", col_name);

    if (l < 0)
        throw FLError(fl, "Negative integer value in CSV column '{}' (should be a province ID)", col_name);

    if (!dm.is_valid_province(l))
        throw FLError(fl, "Invalid province ID #{} in CSV column '{}'", l, col_name);

    return static_cast<uint>(l);
}


AdjacenciesFile::AdjacenciesFile(const VFS& vfs, const DefaultMap& dm)
{
    auto path = vfs["map" / dm.definitions_path()];
    auto spath = path.generic_string();

    // unique_file_ptr will automatically destroy/close its FILE* if we throw an exception (or return)
    typedef std::unique_ptr<std::FILE, int (*)(std::FILE *)> unique_file_ptr;
    unique_file_ptr ufp( std::fopen(path, "rb"), std::fclose );

    if (ufp.get() == nullptr)
        throw Error("Failed to open file: {}: {}", strerror(errno), spath);

    char buf[512];
    uint n_line = 0;

    const auto fl = [&]() { return FLoc(path, n_line); };

    if ( fgets(&buf[0], sizeof(buf), ufp.get()) == nullptr ) // consume CSV header
        throw FLError("This type of CSV file must have a header line");

    ++n_line;

    while ( fgets(&buf[0], sizeof(buf), ufp.get()) != nullptr )
    {
        ++n_line;
        char* p = &buf[0];

        if (*p == '#')
            continue; // not sure if entries can be commented-out, but we'll support it minimally

        const uint NUM_COLS = 9;
        char* cols[NUM_COLS];

        cols[0] = p;

        for (uint c = 1; c < NUM_COLS; ++c) {
            auto prev_end = strchr(cols[c - 1], ';');

            if (prev_end == nullptr)
                throw FLError(fl(), "Not enough columns in CSV record (need at least {} but only {} found)",
                              NUM_COLS, c - 1);

            *prev_end = '\0';
            cols[c] = prev_end + 1;
        }

        /* trim potential EOL from final column */
        str_view rest( cols[NUM_COLS - 1] );
        if (!rest.empty() && rest.back() == '\n') rest.remove_suffix(1);
        if (!rest.empty() && rest.back() == '\r') rest.remove_suffix(1);

        /* add to end of internal list of adjacencies */
        _v.emplace_back(col_to_province_id(fl(), cols[0], "From"),
                        col_to_province_id(fl(), cols[1], "To"),
                        col_to_province_id(fl(), cols[3], "Through"),
                        cols[2], // TODO: validate types into an Enum
                        rest);

        // TODO: once there's a warning log/trace sink, warn about non-negative-1 values for cols 4-8 (1-based)
    }
}


// void AdjacenciesFile::write(const fs::path& out_path) {
//     const std::string& spath = out_path.string();
//     std::ofstream os(spath);

//     if (!os)
//         throw std::runtime_error("Adjacencies file could not be opened for output: " + spath);

//     os << "From;To;Type;Through;-1;-1;-1;-1;Comment\n";

//     for (const auto& adj : _v) {
//         if (adj.deleted) continue;

//         if (adj.from) os << adj.from; // treat 0-value as blank
//         os << ';';
//         if (adj.to) os << adj.to; // treat 0-value as blank
//         os << ';' << adj.type << ';';
//         if (adj.through) os << adj.through; // treat 0-value as blank
//         os << ";-1;-1;-1;-1;" << adj.comment << "\n";
//     }
// }


_CK2_NAMESPACE_END;
