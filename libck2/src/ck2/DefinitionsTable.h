#ifndef __LIBCK2_DEFINITIONS_TABLE_H__
#define __LIBCK2_DEFINITIONS_TABLE_H__

#include "common.h"
#include "DefaultMap.h"
#include "VFS.h"
#include "Color.h"
#include "filesystem.h"
#include <string>
#include <vector>


_CK2_NAMESPACE_BEGIN;


class DefinitionsTable
{
public:
    struct Row {
        uint        id;
        RGB         color;
        std::string name;
        std::string rest;

        Row(uint id_, RGB color_, str_view name_, str_view rest_ = "")
            : id(id_), color(color_), name(name_), rest(rest_) {}
    };

    // construct an empty file; default ctor must adjust the row vector due to the API's 1:1 mapping of province ID
    // (1-based) to row vector index (0-based)
    DefinitionsTable();

    // construct from an existing file
    DefinitionsTable(const VFS&, const DefaultMap&);

    // write back to a file
    void write(const fs::path& output_path) const;

    /* act somewhat like an STL container... */

    uint size()  const noexcept { return _v.size() - 1; }
    auto empty() const noexcept { return size() == 0; }

    auto operator[](uint id) const noexcept { return _v[id]; }
    auto operator[](uint id)       noexcept { return _v[id]; }

    auto begin() const noexcept { return _v.cbegin() + 1; }
    auto begin()       noexcept { return _v.begin() + 1; }
    auto end()   const noexcept { return _v.cend(); }
    auto end()         noexcept { return _v.end(); }

private:
    std::vector<Row> _v;
    static inline const auto DUMMY_ROW = Row{ 0, 0, "" };
};


_CK2_NAMESPACE_END;
#endif
