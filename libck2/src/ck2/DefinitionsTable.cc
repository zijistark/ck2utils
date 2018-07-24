
#include "DefinitionsTable.h"
#include "FileLocation.h"
#include "legacy_compat.h" // ?!
#include "filesystem.h"
#include <cstdio>
#include <cstdlib>
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

    FILE* f;

    if ( (f = fopen(spath.c_str(), "rb")) == nullptr )
        throw Error("Failed to open file: {}: {}", strerror(errno), spath);

    char buf[512];
    uint n_line = 0;

    const auto fl = [&]() { return FLoc(path, n_line); };

    if ( fgets(&buf[0], sizeof(buf), f) == nullptr ) // consume CSV header
        throw FLError(fl(), "This type of CSV file must have a header line");

    while ( fgets(&buf[0], sizeof(buf), f) != nullptr )
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
            if ( (n_str[x] = strsep(&p, ";")) == nullptr )
                throw FLError(fl(),
                              "Not enough columns in CSV record (need at least {} but only {} found)", N_COLS, x);
        }

        str_view rest(p);

        if (!rest.empty() && rest.back() == '\n') rest.remove_suffix(1);
        if (!rest.empty() && rest.back() == '\r') rest.remove_suffix(1);

        const uint N_INT_COLS = N_COLS - 1;
        long n[N_INT_COLS];
        p = nullptr;

        for (uint x = 0; x < N_INT_COLS; ++x)
        {
            if (*n_str[x] == '\0')
                throw FLError(fl(), "CSV column #{} is empty (integer expected)", x + 1);

            // this allows much less strict integer syntax than CK2 does, another reason for specialized CSVReader
            n[x] = strtol(n_str[x], &p, 10);

            if (*p)
                throw FLError(fl(), "Malformed integer value in CSV column #{}", x + 1);

            if (n[x] < 0)
                throw FLError(fl(), "Negative integer value in CSV column #{}", x + 1);

            if (x != 0 && n[x] >= 256)
                throw FLError(fl(),
                              "RGB color component in CSV column #{} is too large (must be less than 256)", x + 1);
        }

        if (!dm.is_valid_province(n[0]))
            throw FLError(fl(), "Invalid province ID #{}", n[0]);

        if ((uint)n[0] != n_line - 1)
            throw FLError(fl(), "CSV record with province ID #{} is out of order or IDs were skipped", n[0]);

        _v.emplace_back(n[0], rgb{ (uint)n[1], (uint)n[2], (uint)n[3] }, n_str[4], rest);

        if ((uint)n[0] == dm.max_province_id())
            break;
    }

    fclose(f);

    if (size() != dm.max_province_id())
        throw FLError(path, "Defined {} provinces while default.map specified {}", size(), dm.max_province_id());
}


void DefinitionsTable::write(const fs::path& p) const {
    errno = 0;

    const std::string spath = p.generic_string();
    FILE* f;

    // TODO: needs a unique_file_ptr (exception guard)

    if ( (f = fopen(spath.c_str(), "wb")) == nullptr )
        throw Error("Failed to write to file: {}: {}", strerror(errno), spath);

    fmt::print(f, "province;red;green;blue;name;x\n");

    for (auto&& r : *this)
        fmt::print(f, "{};{};{};{};{};{}\n",
                   r.id, r.color.red(), r.color.green(), r.color.blue(), r.name,
                   (r.rest.empty()) ? "x" : r.rest);

    fclose(f);
 
    if (errno)
        throw Error("Failed to write all data to file: {}: {}", strerror(errno), spath);
}


_CK2_NAMESPACE_END;
