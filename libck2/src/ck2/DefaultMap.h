#ifndef __LIBCK2_DEFAULT_MAP_H__
#define __LIBCK2_DEFAULT_MAP_H__

#include "common.h"
#include "VFS.h"
#include "filesystem.h"
#include <string>
#include <string_view>
#include <vector>
#include <unordered_map>
#include <unordered_set>


_CK2_NAMESPACE_BEGIN;


class DefaultMap {
public:
    struct SeaRange {
        uint start_id;
        uint end_id;
    };

private:
    using seazone_vec_t = std::vector<SeaRange>;
    using ocean_vec_t = std::vector<uint>;
    using major_river_set_t = std::unordered_set<uint>;

    uint              _max_prov_id;
    fs::path          _definitions_path;
    fs::path          _province_map_path;
    fs::path          _positions_path;
    fs::path          _terrain_map_path;
    fs::path          _river_map_path;
    fs::path          _terrain_path;
    fs::path          _height_map_path;
    fs::path          _tree_map_path;
    fs::path          _continent_path;
    fs::path          _adjacencies_path;
    fs::path          _climate_path;
    fs::path          _geo_region_path;
    fs::path          _island_region_path;
    fs::path          _statics_path;
    fs::path          _seasons_path;
    seazone_vec_t     _seazone_vec;
    ocean_vec_t       _ocean_vec;
    major_river_set_t _major_river_set;

    const std::unordered_map<string_view, fs::path&> _req_path_map;

public:
    DefaultMap(const VFS& vfs);

    // non-const interface will be provided when we actually have the need

    auto        max_province_id()    const noexcept { return _max_prov_id; }
    const auto& definitions_path()   const noexcept { return _definitions_path; }
    const auto& province_map_path()  const noexcept { return _province_map_path; }
    const auto& positions_path()     const noexcept { return _positions_path; }
    const auto& terrain_map_path()   const noexcept { return _terrain_map_path; }
    const auto& river_map_path()     const noexcept { return _river_map_path; }
    const auto& terrain_path()       const noexcept { return _terrain_path; }
    const auto& height_map_path()    const noexcept { return _height_map_path; }
    const auto& tree_map_path()      const noexcept { return _tree_map_path; }
    const auto& continent_path()     const noexcept { return _continent_path; }
    const auto& adjacencies_path()   const noexcept { return _adjacencies_path; }
    const auto& climate_path()       const noexcept { return _climate_path; }
    const auto& geo_region_path()    const noexcept { return _geo_region_path; }
    const auto& island_region_path() const noexcept { return _island_region_path; }
    const auto& statics_path()       const noexcept { return _statics_path; }
    const auto& seasons_path()       const noexcept { return _seasons_path; }
    const auto& seazone_ranges()     const noexcept { return _seazone_vec; }
    const auto& major_river_set()    const noexcept { return _major_river_set; }

    bool is_valid_province(uint prov_id) const noexcept {
        return prov_id > 0 && prov_id <= _max_prov_id;
    }

    bool is_water_province(uint prov_id) const noexcept;
};


_CK2_NAMESPACE_END;
#endif
