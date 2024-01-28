from collections import defaultdict
import itertools
import math
import pickle
import re
import sys
import PIL.Image
import networkx
import numpy as np
from ck3parser import Pair, rootpath, SimpleParser, Obj, Date, Number, String, csv_rows
from print_time import print_time


EARLIEST_DATE = (float('-inf'),) * 3


class Title:
    instances = {}
    id_title_map = {}

    @classmethod
    def valid_codename(cls, string):
        try:
            return re.match(r'[ekdcb]_', string)
        except TypeError:
            return False

    @classmethod
    def get(cls, title, create_if_missing=False):
        if title == 0:
            return None
        if isinstance(title, Title):
            return title
        if create_if_missing and title not in Title.instances:
            Title(title)
        return Title.instances[title]

    def __init__(self, codename):
        self.codename = codename
        self.liege = None
        self.vassals = []
        Title.instances[codename] = self


def read_game_data(parser):
    def parse_default_map(default_map_path):
        needed = {'definitions', 'provinces', 'adjacencies'}
        paths = {}
        province_types = defaultdict(list)
        with open(str(default_map_path)) as f:
            for line in f:
                if match := re.match(r'(\w+)\s*=\s*"([^"]*)"', line):
                    k, v = match.groups()
                    if k in needed:
                        paths[k] = 'map_data/' + v
                elif match := re.match(r'(\w+)\s*=\s*(\w+)\s*\{\s*(\d+(?:\s*\d+)*)\s*\}', line):
                    k, kind, contents = match.groups()
                    if kind == 'RANGE':
                        start, stop = (int(x) for x in contents.split())
                        ids = list(range(start, stop + 1))
                    else:  # LIST
                        ids = [int(x) for x in contents.split()]
                    province_types[k].extend(ids)
        province_types['skip'] = set().union(*(
            v for k, v in province_types.items() if k not in ['land', 'sea_zones']))

        return paths, province_types

    def process_map_definitions_row(row):
        try:
            province, red, green, blue = map(int, row[:4])
        except ValueError:
            return
        key = tuple(np.uint8(x) for x in (red, green, blue))
        rgb_id_map[key] = province
        id_name_map[province] = row[4]
        name_id_map[row[4]] = province

    def parse_provinces_map(path, width, province_types):
        def province_id(rgb):
            return rgb_id_map.get(tuple(rgb), 0)

        skip_provinces = province_types['skip']
        coords = defaultdict(lambda: [0, 0, 0])
        image = PIL.Image.open(str(path))
        image = image.crop((0, 0, width, image.height))
        image = np.array(image)
        for i, j in np.ndindex(image.shape[0] - 1, image.shape[1] - 1):
            province = province_id(image[i, j])
            coords[province][0] += j
            coords[province][1] += i
            coords[province][2] += 1
            if province != 0 and province not in skip_provinces:
                neighbor_x = province_id(image[i, j + 1])
                neighbor_y = province_id(image[i + 1, j])
                for neighbor in [neighbor_x, neighbor_y]:
                    if neighbor != province and neighbor != 0:
                        if neighbor not in skip_provinces:
                            province_graph.add_edge(province, neighbor)
                        elif province in province_types['land']:
                            if neighbor in province_types['river_provinces']:
                                province_graph.nodes[province]['riverside'] = 'yes'
                            elif neighbor in province_types['sea_zones']:
                                province_graph.nodes[province]['coastal'] = 'yes'

        a = np.array(image).view(dtype='u1,u1,u1')[..., 0]
        b = np.vectorize(lambda x: rgb_id_map[tuple(x)], otypes=[np.uint16])(a)
        for p in province_graph:
            c = coords[p]
            province_graph.nodes[p]['center'] = c[0] // c[2], c[1] // c[2]
        return b

    def process_map_adjacencies_row(row):
        try:
            from_province, to_province = map(int, row[:2])
        except ValueError:
            return
        if from_province > 0 and to_province > 0:
            province_graph.add_edge(from_province, to_province)

    def process_terrain(tree, province_types):
        default_land = tree['default_land'].val
        default_sea = tree['default_sea'].val
        default_coastal_sea = tree['default_coastal_sea'].val
        seas = province_types['sea_zones']
        for prov in province_graph:
            if v := tree.get(prov):
                terrain = v.val
            elif prov not in seas:
                terrain = default_land
            elif any(p not in seas for p in province_graph[prov]):
                terrain = default_coastal_sea
            else:
                terrain = default_sea
            province_graph.nodes[prov]['terrain'] = terrain

    rgb_id_map = {}
    id_name_map = {}
    name_id_map = {}
    province_graph = networkx.Graph()
    borders_path = rootpath / 'ck3_borderlayer.png'
    borders = PIL.Image.open(str(borders_path))
    colors = {
        'land': np.uint8((127, 127, 127)),
        'sea_zones': np.uint8((68, 107, 163)),
        'river_provinces': np.uint8((68, 107, 163)),
        'lakes': np.uint8((68, 107, 163)),
        'impassable_seas': np.uint8((68, 107, 163)),
        'impassable_mountains': np.uint8((94, 94, 94)),
    }

    map_data_paths, province_types = parse_default_map(
        parser.file('map_data/default.map'))
    for row in csv_rows(parser.file(map_data_paths['definitions'])):
        process_map_definitions_row(row)
    prov_color_lut = np.full(max(id_name_map) + 1, colors['land'], '3u1')
    for prov_type, provs in province_types.items():
        if prov_type != 'skip':
            prov_color_lut[provs] = colors[prov_type]
    width = parser.parse_file(
        'common/defines/graphic/00_graphics.txt')['NCamera']['PANNING_WIDTH'].val
    province_map = parse_provinces_map(
        parser.file(map_data_paths['provinces']), width, province_types)
    for row in csv_rows(parser.file(map_data_paths['adjacencies'])):
        process_map_adjacencies_row(row)
    for edge in province_graph.edges:
        province_graph.edges[edge]['weight'] = math.dist(
            *(province_graph.nodes[p]['center'] for p in edge))
    process_terrain(parser.parse_file(
        'common/province_terrain/00_province_terrain.txt'), province_types)

    colored_province_map = PIL.Image.fromarray(prov_color_lut[province_map])
    colored_province_map.paste(borders, mask=borders)

    return province_graph, colored_province_map


def process_landed_titles(parser):
    def recurse(v, parent_title=None):
        for p2 in v:
            # TODO parser treats "color = hsv{ 0.98 0.9 0.9 }" as a pair followed by an obj.... fix this
            if not isinstance(p2, Pair):
                continue
            n2, v2 = p2
            if Title.valid_codename(n2.val):
                title = Title.get(n2.val, create_if_missing=True)
                if parent_title:
                    if n2.val.startswith('b') and not hasattr(parent_title, 'capital'):
                        parent_title.capital = title
                    title.liege = parent_title
                    parent_title.vassals.append(title)
                recurse(v2, title)
            elif n2.val == 'province':
                Title.id_title_map[v2.val] = parent_title
                parent_title.province = v2.val

    for _, v in parser.parse_files('common/landed_titles/*.txt'):
        recurse(v)

# probably make two maps? one with no culture/religion-locked special buildings, and one with them
# also, each era?
# some way to represent dev growth as well?
# also produce mean & median for each terrain type (+coastal/non-coastal? skipping special buildings?)
# return value has keys: next_building, prev_building, type, flag, constructible, province_modifier, county_modifier, duchy_capital_county_modifier, provinces


def process_buildings(parser):
    # need to read special building slots too
    buildings = defaultdict(lambda: {'type': 'regular'})
    for f, tree in parser.parse_files('common/buildings/*.txt'):
        for n, v in tree:
            if not isinstance(v, Obj):
                continue
            seen = set()
            dupes = {n2.val for n2,
                     _ in v if n2.val in seen or seen.add(n2.val)}
            dupes -= {'asset', 'province_modifier', 'province_terrain_modifier',
                      'province_culture_modifier', 'county_culture_modifier', 'next_building'}
            if dupes:  # validation
                print(f, n.val, dupes, sep='\n')
                assert False
            for n2, v2 in v:
                match n2.val:
                    case 'is_graphical_background':
                        if v2.val == 'yes':
                            if n.val in buildings:
                                del buildings[n.val]
                            break  # skip whole building
                    case ('levy' | 'max_garrison' | 'garrison_reinforcement_factor' | 'construction_time' | 'asset' | 'show_disabled' | 'cost_gold' | 'cost_prestige' | 'cost_piety' | 'effect_desc' | 'character_modifier' | 'character_culture_modifier' | 'character_dynasty_modifier' | 'province_culture_modifier' | 'province_terrain_modifier' | 'province_dynasty_modifier' | 'county_culture_modifier' | 'duchy_capital_county_culture_modifier' | 'county_dynasty_modifier' | 'county_holder_character_modifier' | 'on_complete' | 'ai_value' | 'type_icon'):
                        pass  # skip, manually verified to not have any tax-related effects in 1.9.2
                    case 'next_building':
                        buildings[n.val]['next_building'] = v2.val
                        buildings[v2.val]['prev_building'] = n.val
                    case 'type':
                        # regular, special, duchy_capital
                        buildings[n.val]['type'] = v2.val
                    case 'flag':
                        match v2.val:
                            case 'castle' | 'city' | 'temple':
                                buildings[n.val]['flag'] = v2.val
                            case _:  # validation
                                assert (v2.val == 'fully_upgraded_duchy_capital_building' or
                                        v2.val.startswith('travel_point_of_interest_'))
                        # tribal building is set in history(?)
                    case ('is_enabled' | 'can_construct_potential' | 'can_construct_showing_failures_only' | 'can_construct'):
                        if not (x := buildings[n.val].get('constructible')):
                            buildings[n.val]['constructible'] = x = []
                        x.extend(v2.contents)
                        # in_enabled:
                        #   county.holder = {} for duchy capitals,
                        #   is_county_capital = yes for dev buildings,
                        #   building_requirement_tribal = no (weird, include this building),
                        #   building_requirement_tribal = yes (base tribal building)
                        #   anything else (ignore this building)
                    case ('province_modifier' | 'county_modifier' | 'duchy_capital_county_modifier'):
                        if not (x := buildings[n.val].get(n2.val)):
                            buildings[n.val][n2.val] = x = []
                        x.extend(v2.contents)
                    case _:
                        print(f, n.val, n2.val, sep='\n')
                        assert False
    for f, tree in parser.parse_files('history/provinces/*.txt'):
        # todo
        # need to respect history for initial castle/city/temple too?
        # test all valid combinations of city/temple for max tax?
        # if game logic for feudalizing always makes some baronies cities or temples,
        #   need to respect this too?
        # walls of lugo are weird, consider these i guess
        # c'ple has duchy_capital_building = theodosian_walls_01
        # sicilian parliament is weird too, ignore?
        for n, v in tree:
            # assume all special_building/special_building_slots are <= 867.1.1
            # assume that history doesn't build buildings contrary to requirements?
            pairs = [p2 for p2 in v if isinstance(p2.value, String)]
            pairs += [p3 for n2, v2 in v if isinstance(
                n2, Date) or isinstance(n2, Number) for p3 in v2]
            for n2, v2 in pairs:
                if n2.val.startswith('special_building'):
                    if not (x := buildings[v2.val].get('provinces')):
                        buildings[v2.val]['provinces'] = x = set()
                    x.add(n.val)
    return buildings


# assumes the province might be a duchy capital
# * ignores holy site buildings for now, generic and unique
def is_valid_building_in_province(province_graph, buildings, province, building, state):
    def has_building(b):
        while True:
            if b in state['buildings']:
                break
            if not (b := buildings[b].get('next_building')):
                return False
        return True
    barony = Title.id_title_map[province]
    prov_attrs = province_graph.nodes[province]
    county_terrains = {
        province_graph.nodes[t.province]['terrain'] for t in barony.liege.vassals}
    if building[1]['type'] == 'special':
        return province in building[1].get('provinces', [])
    for n, v in building[1].get('constructible', []):
        if n.val == 'has_building_or_higher':
            if not has_building(v.val):
                return False
        elif n.val == 'building_requirement_castle_city_church':
            reqs = [next(b for b, bo in buildings.items() if bo.get(
                'flag') == x) for x in ['castle', 'city', 'temple']]
            for _ in range(1, v['LEVEL'].val):
                reqs = [buildings[b].get('next_building') for b in reqs]
            if not any(has_building(b) for b in reqs):
                return False
        elif n.val == 'building_caravanserai_requirement_terrain' and v.val == 'yes':
            if not county_terrains.intersection({'drylands', 'desert', 'oasis', 'floodplains', 'steppe', 'desert_mountains'}):
                return False
        elif n.val == 'building_watermills_requirement_terrain' and v.val == 'yes':
            if not county_terrains.intersection({'mountains', 'wetlands', 'forest', 'taiga', 'jungle'}) and not prov_attrs.get('riverside'):
                return False
        elif n.val == 'building_windmills_requirement_terrain' and v.val == 'yes':
            if not county_terrains.intersection({'farmlands', 'plains', 'hills'}) and not prov_attrs.get('coastal'):
                return False
        elif n.val == 'building_common_tradeport_requirement_terrain' and v.val == 'yes':
            if not prov_attrs.get('coastal') and not prov_attrs.get('riverside'):
                return False
        elif n.val == 'building_pastures_requirement_terrain' and v.val == 'yes':
            pass
            # todo need geographical_regions
            if not prov_attrs.get('coastal') and not prov_attrs.get('riverside'):
                return False
        elif n.val == 'scope:holder.culture':
            for n2, v2 in v:
                if n2.val == 'has_innovation':
                    if v2.val not in state['innovations']:
                        return False
        elif n.val == 'building_requirement_tribal':
            if (v.val == 'yes') != (state['government'] == 'tribal'):
                return False
        elif n.val == 'is_county_capital' and v.val == 'yes':
            # * does it default to the first barony in landed_titles?
            # todo assuming that. ^ check it
            # * should i optimize choice of which county capital? probably not? but what about cagliari...
            # todo: for now, will not change county capital.
            if barony.liege.capital != barony:
                return False
        else:
            print(building[0], n.val)
            sys.exit()
    return True


def compute_province_tax(province_graph, province, built_buildings):
    pass


def compute_all_tax(province_graph, buildings):
    # flag, regular, duchy_capital, special
    start_buildings = defaultdict(list)
    for k, v in buildings.items():
        if 'prev_building' not in v:
            if 'flag' in v:
                which_type = 'flag'
                if v['flag'] == 'castle':
                    castle = k, v
            else:
                which_type = v['type']
            start_buildings[which_type].append((k, v))
    # assume castle
    # build set of conditions including culture (innovations -> building slots)
    for prov in province_graph:
        if province_graph.nodes[prov].get('terrain') in [None, 'sea', 'coastal_sea']:
            continue
        # try to upgrade flag building, lock it in
        # get all possible special starts, try to upgrade all, lock those in
        # get all possible regular starts, try to upgrade all
        # if duchy capital, get all possible duchy starts, try to upgrade all
        # only tax ones are marches, royal reserves, tax offices, theodosian walls (cple), aurelian walls (rome)
        # count number of building slots
        # pick best combination of N regular buildings and 1 duchy building if capital
        # * but, technically choice of duchy building couples together taxes in each county
        # * maybe each duchy with all its provinces is a SAT-like problem?
        valid_starts = []
        state = {
            'government': 'feudal',
            'buildings': ['castle_01'],
            'innovations': ['innovation_windmills']
        }
        for building in start_buildings['regular']:
            if is_valid_building_in_province(
                    province_graph, buildings, prov, building, state):
                valid_starts.append(building[0])

        print(prov)
        print(valid_starts)
        break
        # todo
        # prov_data = province_graph[province]
        # [b for b in buildings if is_valid_building_in_province(province_graph, province, b[1], culture)]


@print_time
def main():
    parser = SimpleParser()
    try:
        with open(rootpath / 'ck3_province_graph.pickle', 'rb') as f:
            province_graph = pickle.load(f)
        with open(rootpath / 'ck3_colored_province_map.png') as f:
            colored_province_map = PIL.Image.open(
                str(rootpath / 'ck3_colored_province_map.png'))
    except:
        province_graph, colored_province_map = read_game_data(parser)
        with open(rootpath / 'ck3_province_graph.pickle', 'wb') as f:
            pickle.dump(province_graph, f, pickle.HIGHEST_PROTOCOL)
        colored_province_map.save(
            str(rootpath / 'ck3_colored_province_map.png'))
    buildings = process_buildings(parser)
    process_landed_titles(parser)

    compute_all_tax(province_graph, buildings)

    # provs_with_terrain = defaultdict(list)
    # for p, t in province_graph.nodes.data('terrain'):
    #     provs_with_terrain[t].append(p)

    out_path = rootpath / 'ck3_holding_taxes.png'
    colored_province_map.save(str(out_path))


if __name__ == '__main__':
    main()
