#include "DefinitionsTable.h"
#include "DefaultMap.h"
#include "VFS.h"
#include "FileLocation.h"
#include "filesystem.h"
#include "string_utility.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cerrno>


_CK2_NAMESPACE_BEGIN;


DefinitionsTable::DefinitionsTable()
: _v(1, DUMMY_ROW) {} // map 1-based province ID indexing directly to Row vector indices w/ dummy Row


DefinitionsTable::DefinitionsTable(const VFS& vfs, const DefaultMap& dm)
{
    _v.reserve(2048);
    _v.emplace_back(DUMMY_ROW); // dummy Row for province 0

    auto path = vfs["map" / dm.definitions_path()];
    auto spath = path.generic_string();

    // TODO: all of this I/O and string splitting and type conversion/validation needs to be done in the future by
    // a generic CSVReader template class parameterized on the sequence of types (from left to right) for which to
    // extract valid values (presumably simply reusing the [variadic] tuple utility class & a callback function
    // provided by the user code to process a record)

    unique_file_ptr ufp( std::fopen(spath.c_str(), "rb"), std::fclose );
    FILE* f = ufp.get();
    
    if (f == nullptr)
        throw Error("Failed to open file: {}: {}", strerror(errno), spath);

    char buf[512];
    uint n_line = 0;

    auto floc = [&]() { return FLoc(path, n_line); };
    auto flerr = FLErrorFactory(floc);

    if (fgets(&buf[0], sizeof(buf), f) == nullptr) // consume CSV header
        throw flerr("This type of CSV file must have a header line");

    ++n_line;

    while (fgets(&buf[0], sizeof(buf), f) != nullptr)
    {
        ++n_line;

        // proper error handling here would also account for when a nullptr is returned but errno == 0, which means
        // that the line simply was too long for the buffer.

        auto p = &buf[0];

        if (*p == '#') continue;

        const uint N_COLS = 5;
        char* n_str[N_COLS];

        for (uint x = 0; x < N_COLS; ++x)
        {
            if ((n_str[x] = strsep(&p, ';')) == nullptr)
                throw flerr("Not enough columns in CSV record (need at least {} but only {} found)", N_COLS, x);
        }

        string_view rest(p);
        if (!rest.empty() && rest.back() == '\n') rest.remove_suffix(1);
        if (!rest.empty() && rest.back() == '\r') rest.remove_suffix(1);

        const uint N_INT_COLS = N_COLS - 1;
        long n[N_INT_COLS];
        p = nullptr;

        for (uint x = 0; x < N_INT_COLS; ++x)
        {
            if (str_is_blank(n_str[x]))
                throw flerr("CSV column #{} is empty/blank (integer expected)", x + 1);

            // this allows much less strict integer syntax than CK2 does, another reason for specialized CSVReader
            n[x] = strtol(n_str[x], &p, 10);

            if (*p)
                throw flerr("Malformed integer value in CSV column #{}", x + 1);

            if (n[x] < 0)
                throw flerr("Negative integer value in CSV column #{}", x + 1);

            if (x != 0 && n[x] >= 256)
                throw flerr("RGB color component in CSV column #{} is too large (must be less than 256)", x + 1);
        }

        if (!dm.is_valid_province(n[0]))
            throw flerr("Invalid province ID #{}", n[0]);

        // commented-out because I'm not entirely sure that this is a 100% valid constraint anymore.
        /*
        if ((uint)n[0] != n_line - 1)
            throw flerr("CSV record with province ID #{} is out of order or IDs were skipped", n[0]);
        */

        _v.emplace_back(n[0], RGB{ (uint)n[1], (uint)n[2], (uint)n[3] }, n_str[4], rest);

        // TODO: Find a different way to ignore extranneous province entries in definitions.csv (e.g., vanilla and
        // SWMH both have some extra 2-10,000 extra lines simply for pre-filled RGB values should more provinces be
        // added). Why? For the same reason I commented out the error check for the current province ID not being
        // equal to the current line number (minus 1) above; I'm not sure that entries need to appear in order, and
        // if they don't, quitting reading entries as soon as we see the max. province ID will fail to read all of
        // the necessary data.
        if ((unsigned)n[0] == dm.max_province_id())
            break;
    }

    if (size() != dm.max_province_id())
        throw FLError(path, "Defined {} provinces while default.map specified {}", size(), dm.max_province_id());
}


void DefinitionsTable::write(const fs::path& path) const {
    auto spath = path.generic_string();

    // in the future, use a unique_file_ptr that doesn't discard the return value of std::fclose(FILE*) and checks
    // it for an error condition.
    unique_file_ptr ufp( std::fopen(spath.c_str(), "wb"), std::fclose );
    auto f = ufp.get();

    if (f == nullptr)
        throw Error("Failed to open file for writing: {}: {}", strerror(errno), spath);

    fmt::print(f, "province;red;green;blue;name;x\n");

    for (const auto& r : _v)
        fmt::print(f, "{};{};{};{};{};{}\n",
                   r.id, r.color.red(), r.color.green(), r.color.blue(), r.name,
                   r.rest.empty() ? "x" : r.rest);
}


_CK2_NAMESPACE_END;
