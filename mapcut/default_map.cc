
#include "default_map.h"

#include "pdx/parser.h"
#include "pdx/error.h"

#include <cassert>


default_map::default_map(const pdx::vfs& vfs)
: _max_province_id(0) {

    using namespace pdx;

    parser parse(vfs["map/default.map"]);

    for (auto&& s : *parse.root_block()) {
        if (s.key() == "max_provinces") {
            assert( s.value().is_integer() );
            int max_provinces = s.value().as_integer();
            assert( max_provinces > 1 );
            _max_province_id = max_provinces - 1;
        }
        else if (s.key() == "definitions") {
            assert( s.value().is_string() );
            _definitions_path = s.value().as_string();
        }
        else if (s.key() == "provinces") {
            assert( s.value().is_string() );
            _provinces_path = s.value().as_string();
        }
        else if (s.key() == "geographical_region") {
            assert( s.value().is_string() );
            _georegion_path = s.value().as_string();
        }
        else if (s.key() == "region") {
            assert( s.value().is_string() );
            _island_region_path = s.value().as_string();
        }
        else if (s.key() == "adjacencies") {
            assert( s.value().is_string() );
            _adjacencies_path = s.value().as_string();
        }
        else if (s.key() == "sea_zones") {
            auto&& obj_list = *s.value().as_list();
            assert( obj_list.size() == 2 );

            int sea_zone_start = obj_list[0].as_integer();
            int sea_zone_end = obj_list[1].as_integer();
            assert( sea_zone_start > 0 && sea_zone_end > 0 );
            assert( sea_zone_start <= sea_zone_end );

            _seazone_vec.emplace_back(uint(sea_zone_start),
                                      uint(sea_zone_end));
        }
        else if (s.key() == "major_rivers") {
            auto&& obj_list = *s.value().as_list();

            for (const auto& o : obj_list) {
                assert( o.is_integer() );
                int major_river_id = o.as_integer();
                assert( major_river_id > 0 );
                _major_river_set.insert(major_river_id);
            }
        }
    }

    assert( max_province_id() > 0 );
}


bool default_map::id_is_seazone(uint prov_id) const {
    for (auto&& sea_range : _seazone_vec)
        if (prov_id >= sea_range.first && prov_id <= sea_range.second)
            return true;

    return false;
}
