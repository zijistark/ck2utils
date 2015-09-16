
#ifndef _MDH_DEFAULT_MAP_H_
#define _MDH_DEFAULT_MAP_H_

#include <string>
#include <vector>
#include <utility>
#include <unordered_set>


typedef unsigned int uint;


class default_map {
    typedef std::vector< std::pair<uint, uint> > id_pair_vec_t;
    typedef std::unordered_set<uint> id_set_t;

    uint          _max_province_id;
    std::string   _definitions_path;
    std::string   _provinces_path;
    id_pair_vec_t _seazone_vec;
    id_set_t      _major_river_set;

public:
    default_map(const std::string& root_path);

    uint max_province_id() const noexcept { return _max_province_id; }
    const std::string& definitions_path() const noexcept { return _definitions_path; }
    const std::string& provinces_path() const noexcept { return _provinces_path; }
    const id_pair_vec_t& seazone_vec() const noexcept { return _seazone_vec; }
    const id_set_t& major_river_set() const noexcept { return _major_river_set; }

    bool id_is_valid(uint prov_id) const { return (prov_id > 0 && prov_id <= _max_province_id); }
    bool id_is_seazone(uint prov_id) const;
};


#endif
