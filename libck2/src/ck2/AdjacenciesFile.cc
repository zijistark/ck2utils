#include "AdjacenciesFile.h"
#include "FileLocation.h"
#include "DefaultMap.h"
#include "VFS.h"
#include <memory>
#include <fstream>
#include <cstdio>
#include <cstdlib>
#include <cerrno>


_CK2_NAMESPACE_BEGIN;


static uint col_to_province_id(
    const FLoc& fl,
    const char* col,
    const string_view& col_name,
    const DefaultMap& dm)
{
    /* allow a special case where the column is completely unspecified to resolve to the invalid
     * province ID of 0
     *
     * NOTE here from 2018: I see no examples of this, but I'm guessing it's related to "wormholes."
     */
    if (*col == '\0') return 0;

    char* p_potential_junk = nullptr;
    long l = strtol(col, &p_potential_junk, 10);

    if (*p_potential_junk)
        throw FLError(fl, "Malformed integer value in CSV column '{}' (should be a province ID)", col_name);

    if (l < 0)
        throw FLError(fl, "Negative integer value in CSV column '{}' (should be a province ID)", col_name);

    if (!dm.is_valid_province(l))
        throw FLError(fl, "Invalid province ID #{} in CSV column '{}'", l, col_name);

    return static_cast<uint>(l);
}


AdjacenciesFile::AdjacenciesFile(const VFS& vfs, const DefaultMap& dm)
{
    auto path = vfs["map" / dm.adjacencies_path()];
    auto spath = path.generic_string();

    unique_file_ptr ufp( std::fopen(spath.c_str(), "rb"), std::fclose );
    FILE* f = ufp.get();
    
    if (f == nullptr)
        throw Error("Failed to open file: {}: {}", strerror(errno), spath);

    char buf[512];
    uint n_line = 0;

    const auto fl = [&]() { return FLoc(path, n_line); };

    if (fgets(&buf[0], sizeof(buf), f) == nullptr) // consume CSV header
        throw FLError(path, "This type of CSV file must have a header line");

    ++n_line;

    while (fgets(&buf[0], sizeof(buf), f) != nullptr)
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
        string_view rest( cols[NUM_COLS - 1] );
        if (!rest.empty() && rest.back() == '\n') rest.remove_suffix(1);
        if (!rest.empty() && rest.back() == '\r') rest.remove_suffix(1);

        /* add to end of internal list of adjacencies */
        _v.emplace_back(col_to_province_id(fl(), cols[0], "From", dm),
                        col_to_province_id(fl(), cols[1], "To", dm),
                        col_to_province_id(fl(), cols[3], "Through", dm),
                        cols[2], // TODO: validate types into an Enum
                        rest);

        // TODO: once there's a warning log/trace sink, warn about non-negative-1 values for cols 4-8 (1-based)
    }
}


void AdjacenciesFile::write(const fs::path& out_path)
{
    // TODO: needs a unique_file_ptr-like thing (exception guard to close/release the file should we return
    // unexpectedly)

    const string spath = out_path.generic_string();
    std::ofstream os(spath);

    // don't think errno is set for ofstream failure, and the C++ exception model for iostreams is fucking uber-
    // complicated. perma-TODO to decide whether IOStreams are worthwhile (on the input side mainly, but it'd be
    // nice to use one API for both).
    if (!os)
        throw FLError(out_path, "Failed to write to adjacencies file: {}", strerror(errno));

    os << "From;To;Type;Through;-1;-1;-1;-1;Comment\n";

    /* again, NOTE from 2018: apparently 0-values are blanks. k, IDK, whatever. */

    for (const auto& adj : _v)
    {
        if (adj.from) os << adj.from; // treat 0-value as blank
        os << ';';
        if (adj.to) os << adj.to; // treat 0-value as blank
        os << ';' << adj.type << ';';
        if (adj.through) os << adj.through; // treat 0-value as blank
        os << ";-1;-1;-1;-1;" << adj.comment << EOL;
    }
}


_CK2_NAMESPACE_END;
