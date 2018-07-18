#ifndef __LIBCK2_DEFINITIONS_TBL_H__
#define __LIBCK2_DEFINITIONS_TBL_H__

#include "DefaultMap.h"
#include "VFS.h"
#include "Color.h"
#include "filesystem.h"
#include <string>
#include <vector>


_CK2_NAMESPACE_BEGIN;


class DefinitionsTbl {
public:
    class Row {
    public:
        Row(uint id_, str_view name_, rgb color_, str_view rest_ = "")
            : _id(id_), _name(name_), _color(color_), _rest(rest_) {}

        auto        id()    const noexcept { return _id; }
        auto        color() const noexcept { return _color; }
        const auto& name()  const noexcept { return _name; }
        const auto& rest()  const noexcept { return _rest; }

        void id(uint id_)         noexcept { _id = id_; }
        void color(rgb color_)    noexcept { _color = color_; }
        void name(str_view name_) { _name = name_; }
        void rest(str_view rest_) { _rest = rest_; }

    private:
        uint        _id;
        std::string _name;
        rgb         _color;
        std::string _rest;
    };

    // construct an empty file; default ctor must adjust the row vector due to the API's 1:1 mapping of province ID
    // (1-based) to row vector index (0-based)
    DefinitionsTbl();

    // construct from an existing file
    DefinitionsTbl(const VFS&, const DefaultMap&);

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
    static inline const auto DUMMY_ROW = Row{ 0, "", 0 };
};


_CK2_NAMESPACE_END;
#endif
