from collections import OrderedDict
import re
import numpy as np
from PIL import Image
from ck2parser import csv_rows, Pair
from localpaths import cachedir
from eu4.provincelists import terrain_to_provinces
from eu4.eu4lib import Province, Continent, Area, Region, Superregion, \
    TradeCompany, Terrain, ColonialRegion, TradeNode, Eu4Color
from eu4.parser import Eu4Parser
from eu4.cache import disk_cache, cached_property, NumpySerializer


class Eu4MapParser(Eu4Parser):
    """
        parse eu4 files and get all kinds of map related information
    """

    # override capitalization of supplies to match the wiki
    localizationOverrides = {'naval_supplies': 'Naval supplies'}

    def __init__(self):
        super().__init__()

        self.default_tree = self.parser.parse_file('map/default.map')
        self.random_only = {n.val for n in self.default_tree['only_used_for_random']}
        self.max_provinces = self.default_tree['max_provinces'].val
        self.provinces_rgb_map = None
        self.regionColors = None
        if cachedir:
            self.cachedir = cachedir / self.__class__.__name__
            self.cachedir.mkdir(parents=True, exist_ok=True)

    def map_path(self, key):
        return self.parser.file('map/' + self.default_tree[key].val)

    def _get_provinces_rgb_map(self):
        if not self.provinces_rgb_map:
            self.provinces_rgb_map = {}
            for row in csv_rows(self.map_path('definitions')):
                try:
                    number = int(row[0])
                except ValueError:
                    continue
                if number < self.max_provinces:
                    rgb = tuple(np.uint8(row[1:4]))
                    self.provinces_rgb_map[rgb] = np.uint16(number)

        return self.provinces_rgb_map

    @cached_property
    @disk_cache(NumpySerializer)
    def positions_to_provinceID_array(self):
        """create a two-dimensional array which contains the province id for
        each point of the provinces.bmp
        """
        # the code is valid, because Image implements __array_interface__
        # noinspection PyTypeChecker
        pa = np.array(Image.open(str(self.map_path('provinces'))))
        pa = pa.view('u1,u1,u1')[..., 0]
        pa = np.vectorize(lambda x: self._get_provinces_rgb_map()[tuple(x)],
                          otypes=[np.uint16])(pa)
        return pa

    @cached_property
    @disk_cache()
    def all_provinceIDs(self):
        """all ids including water and wasteland, but not provinces in the RNW"""
        province_positions = self.positions_to_provinceID_array
        provinceIDs = []
        for i in range(1, self.max_provinces):
            if i in self.random_only:
                continue
            # check if province exists in the province map
            prov_indices = np.nonzero(province_positions == i)
            if not len(prov_indices[0]):
                continue
            provinceIDs.append(i)
        return provinceIDs

    @cached_property
    def all_provinces(self):
        """OrderedDict of provinceIDs to Province objects.

        The Province objects are prefilled with data from the history
        files.They use the mapparser to dynamically load other data.
        """
        provinces = {provinceID: Province(provinceID, parser=self)
                     for provinceID in self.all_provinceIDs}
        for provinceID, province_data in self._province_attributes.items():
            for k, v in province_data.items():
                provinces[provinceID][k] = v
        return provinces

    @cached_property
    def all_land_provinces(self):
        return {provinceID: province
                for provinceID, province in self.all_provinces.items()
                if province.type == 'Land'}

    @cached_property
    @disk_cache()
    def _inland_sea_provinces(self):
        """ only used by get_province_type. this is not accurate,
        because it contains open seas which are marked as inland seas
        get_province_type fixes the inaccuracy by checking which ones
        are open seas
        """
        inland_sea_names = set()
        # dict of provinceIDs to booleans
        is_inland_sea = {}
        terrain_tree = self.parser.parse_file(self.map_path('terrain_definition'))
        for n, v in terrain_tree['categories']:
            inland_sea = v.has_pair('inland_sea', 'yes')
            if inland_sea:
                inland_sea_names.add(n.val)
            if 'terrain_override' in v.dictionary:
                # we save all terrain overrides, because they could override
                # a province which is an inland see in terrain.bmp
                is_inland_sea.update((n2.val, inland_sea) for n2 in v['terrain_override'])

        inland_sea_nums = set()
        for n, v in terrain_tree['terrain']:
            if v['type'].val in inland_sea_names:
                inland_sea_nums.update(n2.val for n2 in v['color'])

        pa = self.positions_to_provinceID_array
        # the code is valid, because Image implements __array_interface__
        # noinspection PyTypeChecker
        ta = np.array(Image.open(str(self.map_path('terrain'))))

        for number in self.all_provinceIDs:
            if number in is_inland_sea:
                # skip provinces which were already set by a terrain override
                continue
            prov_indices = np.nonzero(pa == number)
            if len(prov_indices[0]):
                terrain_num = np.argmax(np.bincount(ta[prov_indices]))
                is_inland_sea[number] = terrain_num in inland_sea_nums
        return [provinceID
                for provinceID, province_is_inland_sea in is_inland_sea.items()
                if province_is_inland_sea]

    @cached_property
    def terrains(self):
        terrains = {}
        terrain_tree = self.parser.parse_file(self.map_path('terrain_definition'))
        for n, v in terrain_tree['categories']:
            name = n.val
            if name == 'impassable_mountains' or name == 'pti':  # permanent terra incognita
                continue
            color = Eu4Color.new_from_parser_obj(v['color'])
            if name == 'ocean':
                provinces = [provinceID for provinceID in self.all_provinceIDs
                             if self.get_province_type(provinceID) == 'Sea']
            elif name == 'inland_ocean':
                provinces = [provinceID for provinceID in self.all_provinceIDs
                             if self.get_province_type(provinceID) == 'Inland sea']
            else:
                provinces = terrain_to_provinces[name]

            terrains[name] = Terrain(name, self.localize(name), provinceIDs=provinces, parser=self, color=color)

        # not really terrains which the game uses
        terrains['lake'] = Terrain('lake', 'Lake',
                                   provinceIDs=[provinceID for provinceID in self.all_provinceIDs
                                                if self.get_province_type(provinceID) == 'Lake'],
                                   parser=self, color=terrains['ocean'].color)
        terrains['open_sea'] = Terrain('open_sea', 'Open sea',
                                       provinceIDs=[provinceID for provinceID in self.all_provinceIDs
                                                    if self.get_province_type(provinceID) == 'Open sea'],
                                       parser=self, color=terrains['ocean'].color)

        return terrains

    def _get_open_seas(self, province_types):
        """return provinceIDs which don't border any land,
        but which are classified as 'Inland sea' or 'Sea' in the parameter province_types
        """
        open_seas = []
        for provinceID in self.all_provinceIDs:
            if province_types[provinceID] in ['Inland sea', 'Sea']:
                borders_land = False
                for border_prov in self.get_adjacent_provinces(provinceID):
                    if province_types[border_prov] in ['Land', 'Wasteland']:
                        borders_land = True
                        break
                if not borders_land:
                    open_seas.append(provinceID)
        return open_seas

    @cached_property
    def province_to_province_type_mapping(self):
        province_types = {}
        for n in self.all_provinceIDs:
            province_types[n] = 'Land'

        for n in self.parser.parse_file(self.map_path('climate'))['impassable']:
            if n.val in province_types:
                province_types[n.val] = 'Wasteland'
        for n in self.default_tree['sea_starts']:
            if n.val in province_types:
                if n.val in self._inland_sea_provinces:
                    province_types[n.val] = 'Inland sea'
                else:
                    province_types[n.val] = 'Sea'
        for n in self.default_tree['lakes']:
            if n.val in province_types:
                province_types[n.val] = 'Lake'
        for open_seas_provinceID in self._get_open_seas(province_types):
            province_types[open_seas_provinceID] = 'Open sea'
        return province_types

    def get_province_type(self, provinceID):
        """return the province type as a string

        The options are: 'Land', 'Sea', 'Inland sea', 'Open sea', 'Lake' and  'Wasteland'
        """
        return self.province_to_province_type_mapping[provinceID]

    @cached_property
    def all_continents(self):
        """return a dict between the script name of a continent and a Continent object"""
        continents = {}
        for n, v in self.parser.parse_file(self.map_path('continent')):
            if n.val == 'island_check_provinces':
                continue
            provinces = []
            for n2 in v:
                if n2.val in self.all_provinces:
                    provinces.append(self.all_provinces[n2.val])
            continents[n.val] = Continent(n.val, self.localize(n.val), provinces=provinces)
        return continents

    @cached_property
    def province_to_continent_mapping(self):
        province_to_continent_mapping = {}
        for c in self.all_continents.values():
            province_to_continent_mapping.update({p.id: c for p in c.provinces})
        return province_to_continent_mapping

    def get_continent(self, province):
        if province.id in self.province_to_continent_mapping:
            return self.province_to_continent_mapping[province.id]
        else:
            return Continent('', '', [])

    @cached_property
    def all_areas(self):
        """return a dict between the script name of an area and an Area object"""
        areas = OrderedDict()
        for n, v in self.parser.parse_file(self.map_path('area')):
            if len(v) > 0:
                provinceIDs = []
                color = None
                for n2 in v:
                    if isinstance(n2, Pair):
                        if n2.key.val == 'color':
                            color = Eu4Color.new_from_parser_obj(n2.value)
                    else:
                        provinceIDs.append(n2.val)
                areas[n.val] = Area(n.val, self.localize(n.val), provinceIDs=provinceIDs, parser=self, color=color)
        return areas

    @cached_property
    def province_to_area_mapping(self):
        """mapping between province ids and areas"""
        province_to_area_mapping = {}
        for area in self.all_areas.values():
            for provinceID in area.provinceIDs:
                province_to_area_mapping[provinceID] = area
        return province_to_area_mapping

    def get_area(self, province):
        if province.id in self.province_to_area_mapping:
            return self.province_to_area_mapping[province.id]
        else:
            return Area('', '')

    @cached_property
    def all_regions(self):
        """return a dict between the script name of a region and a Region object"""
        regions = OrderedDict()
        for n, v in self.parser.parse_file(self.map_path('region')):
            if 'areas' in v.dictionary:
                area_names = [n2.val for n2 in v['areas']]
                regions[n.val] = Region(n.val, self.localize(n.val), area_names=area_names, parser=self)
        return regions

    @cached_property
    def area_to_region_mapping(self):
        area_to_region_maping = {}
        for region in self.all_regions.values():
            for areaName in region.area_names:
                area_to_region_maping[areaName] = region
        return area_to_region_maping

    def get_region(self, area_name):
        if area_name in self.area_to_region_mapping:
            return self.area_to_region_mapping[area_name]
        else:
            return Region('', '')

    @cached_property
    def all_superregions(self):
        """return a dict between the script name of a superregion and a Superregion object"""
        superregions = OrderedDict()
        for n, v in self.parser.parse_file(self.map_path('superregion')):
            if len(v) > 0:
                region_names = [n2.val for n2 in v if n2.val != 'restrict_charter']
                superregions[n.val] = Superregion(n.val, self.localize(n.val), region_names=region_names, parser=self)
        return superregions

    @cached_property
    def region_to_superregion_mapping(self):
        region_to_superregion_mapping = {}
        for superregion in self.all_superregions.values():
            for regionName in superregion.region_names:
                region_to_superregion_mapping[regionName] = superregion
        return region_to_superregion_mapping

    def get_superregion(self, region_name):
        if region_name in self.region_to_superregion_mapping:
            return self.region_to_superregion_mapping[region_name]
        else:
            return Superregion('', '')

    @cached_property
    def all_trade_nodes(self):
        all_trade_nodes = OrderedDict()
        nodecounter = 0
        for _, tree in self.parser.parse_files('common/tradenodes/*'):
            for trade_node_name, data in tree:
                nodecounter += 1
                provinces = [prov.val for prov in data['members'] if prov.val in self.all_land_provinces]
                if 'color' in data.dictionary:
                    color = Eu4Color.new_from_parser_obj(data['color'])
                else:
                    color = self.color_list[nodecounter]
                all_trade_nodes[trade_node_name.val] = TradeNode(trade_node_name.val,
                                                                 self.localize(trade_node_name.val),
                                                                 provinceIDs=provinces, color=color, parser=self)
        return all_trade_nodes

    @cached_property
    def province_to_trade_node_mapping(self):
        province_to_trade_node_mapping = {}
        for trade_node in self.all_trade_nodes.values():
            for province in trade_node.provinces:
                province_to_trade_node_mapping[province.id] = trade_node
        return province_to_trade_node_mapping

    def get_trade_node(self, province):
        if province.id in self.province_to_trade_node_mapping:
            return self.province_to_trade_node_mapping[province.id]
        else:
            return ''

    @cached_property
    def all_trade_companies(self):
        all_tc = {}
        for _, tree in self.parser.parse_files('common/trade_companies/*'):
            for tc_name, data in tree:
                provinces = [prov.val for prov in data['provinces'] if prov.val in self.all_land_provinces]
                color = Eu4Color.new_from_parser_obj(data['color'])
                all_tc[tc_name.val] = TradeCompany(tc_name.val, self.localize(tc_name.val), provinceIDs=provinces,
                                                   color=color, parser=self)
        return all_tc

    @cached_property
    def all_colonial_regions(self):
        colonial_regions = {}
        for _, tree in self.parser.parse_files('common/colonial_regions/*'):
            for region_name, data in tree:
                if region_name.val.startswith('colonial_placeholder'):
                    continue
                provinces = [prov.val for prov in data['provinces'] if prov.val in self.all_land_provinces]
                color = Eu4Color.new_from_parser_obj(data['color'])
                colonial_regions[region_name.val] = ColonialRegion(region_name.val, self.localize(region_name.val),
                                                                   provinceIDs=provinces, color=color, parser=self)
        return colonial_regions

    @cached_property
    def color_list(self):
        """these colors are used by the game in some map modes"""
        color_list = []
        for _, tree in self.parser.parse_files('common/region_colors/*'):
            for _, color in tree:
                color_list.append(Eu4Color.new_from_parser_obj(color))
        return color_list

    @cached_property
    def region_colors(self):
        region_colors = {}
        # start with 1, because 0 is random_new_world_region which gets ignored because it doesn't have areas
        region_counter = 1
        for r in self.all_regions:
            region_colors[r] = self.color_list[region_counter]
            region_counter += 1
        return region_colors

    @cached_property
    def estuary_map(self):
        """returns a dict. keys are the estuary modifier names and the values are province lists"""
        estuaries = {}
        for name, data in self.parser.merge_parse('common/event_modifiers/*'):
            if 'picture' in data and data['picture'] == 'estuary_icon':
                provinces = [p for p in self.all_provinces.values() if 'Modifiers' in p and name in p['Modifiers']]
                if len(provinces) > 0:
                    estuaries[name] = provinces

        return estuaries

    @cached_property
    @disk_cache()
    def _province_attributes(self):
        """return a dictionary of province data

        the attributes are acquired from the history files and
        all changes till the 1444-11-11 start date are considered

        this method is used to set up the Province objects in all_provinces
        and it should not be called directly
        """
        provinces_data = {}
        for path in self.parser.files('history/provinces/*'):
            match = re.match(r'\d+', path.stem)
            if not match:
                continue
            number = int(match.group())
            if number >= self.max_provinces:
                continue
            history = {}
            values = {}
            modifiers = []
            for n, v in self.parser.parse_file(path):
                if isinstance(n.val, tuple):
                    if n.val <= (1444, 11, 11):
                        history[n.val] = {}, []
                        for n2, v2 in v:
                            if n2.val == 'add_permanent_province_modifier':
                                history[n.val][1].append(v2['name'].val)
                            elif n2.val == 'add_province_triggered_modifier':
                                history[n.val][1].append(v2.val)
                            else:
                                history[n.val][0][n2.val] = v2

                elif n.val == 'add_permanent_province_modifier':
                    modifiers.append(v['name'].val)
                elif n.val == 'add_province_triggered_modifier':
                    modifiers.append(v.val)
                else:
                    values[n.val] = v

            for _, (history_values, history_modifiers) in sorted(history.items()):
                values.update(history_values)
                modifiers.extend(history_modifiers)

            dev = [values[x].val if x in values else 0 for
                   x in ['base_tax', 'base_production', 'base_manpower']]
            province = {}
            province['Development'] = int(sum(dev)) if sum(dev) else ''
            province['BT'] = int(dev[0]) if dev[0] else ''
            province['BP'] = int(dev[1]) if dev[1] else ''
            province['BM'] = int(dev[2]) if dev[2] else ''
            if 'center_of_trade' in values:
                province['center_of_trade'] = values['center_of_trade'].val
            province['Modifiers'] = modifiers
            if 'owner' in values:
                province['Owner'] = values['owner'].val
            if 'tribal_owner' in values:
                province['tribal_owner'] = values['tribal_owner'].val

            # sometimes uncolonized provinces have a trade good in the history file,
            # but that doesn't seem to have an impact on the game
            if 'trade_goods' in values and 'owner' in values:
                province['Trade good'] = values['trade_goods'].val
            elif self.get_province_type(number) == 'Land':
                province['Trade good'] = 'unknown'
            if 'religion' in values:
                province['Religion'] = values['religion'].val
            if 'culture' in values:
                culture = values['culture'].val
                province['Culture'] = culture
                province['Culture Group'] = self.culture_to_culture_group_mapping[culture]
            if 'latent_trade_goods' in values:
                if len(values['latent_trade_goods']) > 1:
                    raise Exception('Provinces with multiple latent trade goods are not handled')
                else:
                    for n in values['latent_trade_goods']:
                        province['latent trade good'] = n.val
                        break

            provinces_data[number] = province
        return provinces_data

    def get_adjacent_provinces(self, provinceID):
        """return a set of provinces which are adjacent to provinceID

        does not consider adjacency via strait
        """
        return self.adjacency_map[provinceID]

    @cached_property
    @disk_cache()
    def adjacency_map(self):
        """dictionary between provinceIDs and a set of adjacent provinceIDs"""
        id_map = self.positions_to_provinceID_array
        max_x = len(id_map[0])
        max_y = len(id_map)
        adjacency_map = {provinceID: set() for provinceID in self.all_provinceIDs}
        for x in range(max_x):
            for y in range(max_y):
                provinceID = id_map[y][x]
                if x > 0:
                    adjacency_map[provinceID].add(id_map[y][x - 1])
                if y > 0:
                    adjacency_map[provinceID].add(id_map[y - 1][x])
                if x < max_x - 1:
                    adjacency_map[provinceID].add(id_map[y][x + 1])
                if y < max_y - 1:
                    adjacency_map[provinceID].add(id_map[y + 1][x])
                # tests indicate that diagonal pixels don't count as adjacent
                # examples:
                # Halmaheran Sea(1400) - Flores Sea(1357)
                # Stadacona (994) - Pekuakamiulnuatsh (2579)

        return adjacency_map
