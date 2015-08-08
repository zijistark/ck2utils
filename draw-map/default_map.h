
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
    std::string   _definitions_filename;
    std::string   _provinces_filename;
    id_pair_vec_t _seazone_vec;
    id_set_t      _major_river_set;

public:
    default_map(const std::string& path);

    uint max_province_id() const noexcept { return _max_province_id; }
    const std::string& definitions_filename() const noexcept { return _definitions_filename; }
    const std::string& provinces_filename() const noexcept { return _provinces_filename; }
    const id_pair_vec_t& seazone_vec() const noexcept { return _seazone_vec; }
    const id_set_t& major_river_set() const noexcept { return _major_river_set; }
};


#endif
