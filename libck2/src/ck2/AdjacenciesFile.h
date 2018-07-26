#ifndef __LIBCK2_ADJACENCIES_FILE_H__
#define __LIBCK2_ADJACENCIES_FILE_H__

#include "common.h"
#include "filesystem.h"
#include <string_view>
#include <string>
#include <vector>


_CK2_NAMESPACE_BEGIN;


class VFS;
class DefaultMap;


class AdjacenciesFile {
public:
    struct Adjacency {
        uint from;
        uint to;
        uint through;
        string type;
        string comment;

        Adjacency(uint _from, uint _to, uint _through, string_view _type, string_view _comment)
            : from(_from), to(_to), through(_through), type(_type), comment(_comment) {}
    };

public:
    AdjacenciesFile(const VFS&, const DefaultMap&);
    void write(const fs::path&);

    /* give this type a container-like interface and C++11 range-based-for support */
    auto size()  const noexcept { return _v.size(); }
    auto empty() const noexcept { return (size() == 0); }
    auto begin()       noexcept { return _v.begin(); }
    auto end()         noexcept { return _v.end(); }
    auto begin() const noexcept { return _v.cbegin(); }
    auto end()   const noexcept { return _v.cend(); }

    // TODO: should have methods for adding entries, removing them, etc. that are forwarded to underlying vector.

private:
    std::vector<Adjacency> _v;
};


_CK2_NAMESPACE_END;
#endif
