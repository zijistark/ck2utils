
#ifndef _MDH_DEFAULT_MAP_H_
#define _MDH_DEFAULT_MAP_H_

#include <pdx/vfs.h>

#include <boost/filesystem.hpp>

#include <string>
#include <vector>
#include <utility>
#include <unordered_set>

namespace fs = boost::filesystem;
typedef unsigned int uint;

class default_map {
    typedef std::vector< std::pair<uint, uint> > id_pair_vec_t;
    typedef std::unordered_set<uint> id_set_t;

    uint          _max_province_id;
    fs::path      _definitions_path;
    fs::path      _provinces_path;
    fs::path      _georegion_path;
    fs::path      _island_region_path;
    fs::path      _adjacencies_path;
    id_pair_vec_t _seazone_vec;
    id_set_t      _major_river_set;

public:
    default_map(const pdx::vfs& vfs);

    uint max_province_id() const noexcept { return _max_province_id; }

    const fs::path& definitions_path()         const noexcept { return _definitions_path; }
    const fs::path& provinces_path()           const noexcept { return _provinces_path; }
    const fs::path& geographical_region_path() const noexcept { return _georegion_path; }
    const fs::path& island_region_path()       const noexcept { return _island_region_path; }
    const fs::path& adjacencies_path()         const noexcept { return _adjacencies_path; }

    const id_pair_vec_t& seazone_vec() const noexcept { return _seazone_vec; }
    const id_set_t& major_river_set()  const noexcept { return _major_river_set; }

    bool id_is_valid(uint prov_id) const { return (prov_id > 0 && prov_id <= _max_province_id); }
    bool id_is_seazone(uint prov_id) const;
};


#endif
