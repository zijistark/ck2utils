
#include "default_map.h"

#include "pdx.h"
#include "error.h"

#include <cassert>


default_map::default_map(const fs::path& root_path)
: _max_province_id(0), _root_path(root_path) {

    using namespace pdx;

    const fs::path path = root_path / "map/default.map";
    plexer lex(path.c_str());
    block doc(lex, true);

    for (auto&& s : doc.stmt_list) {
        if (s.key_eq("max_provinces")) {
            int max_provinces = s.val.as_integer();
            assert( max_provinces > 1 );
            _max_province_id = max_provinces - 1;
        }
        else if (s.key_eq("definitions")) {
            _definitions_path = s.val.as_c_str();
        }
        else if (s.key_eq("provinces")) {
            _provinces_path = s.val.as_c_str();
        }
        else if (s.key_eq("sea_zones")) {
            auto&& obj_list = s.val.as_list()->obj_list;
            assert( obj_list.size() == 2 );

            int sea_zone_start = obj_list[0].as_integer();
            int sea_zone_end = obj_list[1].as_integer();
            assert( sea_zone_start > 0 && sea_zone_end > 0 );
            assert( sea_zone_start <= sea_zone_end );

            _seazone_vec.emplace_back(uint(sea_zone_start),
                                      uint(sea_zone_end));
        }
        else if (s.key_eq("major_rivers")) {
            auto&& obj_list = s.val.as_list()->obj_list;

            for (auto&& o : obj_list) {
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
