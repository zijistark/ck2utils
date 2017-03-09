#!/usr/bin/env python3

import csv
import networkx as nx
import numpy as np
from PIL import Image
from ck2parser import (rootpath, csv_rows, get_localisation, String, Pair, Obj,
                       TopLevel, SimpleParser)
from print_time import print_time

def duchy_properties(tree):
    for n, v in tree:
        if n.val[:2] in ('e_', 'k_'):
            yield from duchy_properties(v)
        elif n.val[:2] == 'd_':
            counties = [n2.val for n2, _ in v if n2.val[:2] == 'c_']
            yield n.val, v['capital'].val, counties

@print_time
def main():
    parser = SimpleParser(rootpath / 'SWMH-BETA/SWMH')
    rgb_id_map = {}
    id_name_map = {}
    default_tree = parser.parse_file(parser.file('map/default.map'))
    max_provinces = default_tree['max_provinces'].val
    for row in csv_rows(parser.file('map/' + default_tree['definitions'].val)):
        try:
            province = int(row[0])
        except ValueError:
            continue
        if province < max_provinces:
            rgb_id_map[tuple(np.uint8(row[1:4]))] = province
            id_name_map[province] = row[4]
    id_county_map = {}
    for path in parser.files('history/provinces/*'):
        prov_id, prov_name = path.stem.split(' - ')
        prov_id = int(prov_id)
        if id_name_map.get(prov_id) == prov_name:
            try:
                id_county_map[prov_id] = parser.parse_file(path)['title'].val
            except KeyError:
                continue
    province_graph = nx.Graph()
    provinces_path = parser.file('map/' + default_tree['provinces'].val)
    a = np.array(Image.open(str(provinces_path)))
    for i, j in np.ndindex(a.shape[0] - 1, a.shape[1] - 1):
        province = rgb_id_map.get(tuple(a[i, j]), 0)
        if province != 0:
            province_graph.add_node(province)
            neighbor_x = rgb_id_map.get(tuple(a[i, j + 1]), 0)
            neighbor_y = rgb_id_map.get(tuple(a[i + 1, j]), 0)
            for neighbor in (neighbor_x, neighbor_y):
                if neighbor != province and neighbor != 0:
                    province_graph.add_edge(province, neighbor)
    adjacencies_path = parser.file('map/' + default_tree['adjacencies'].val)
    for row in csv_rows(adjacencies_path):
        try:
            province_graph.add_edge(int(row[0]), int(row[1]))
        except ValueError:
            pass
    county_graph = nx.relabel_nodes(province_graph, id_county_map)
    remaining_provs = [x for x in county_graph if isinstance(x, int)]
    county_graph.remove_nodes_from(remaining_provs)
    duchy_capital_map = {}
    duchy_counties_map = {}
    county_duchy_map = {}
    landed_titles_index = {}
    current_index = 0
    for _, tree in parser.parse_files('common/landed_titles/*'):
        for duchy, capital, counties in duchy_properties(tree):
            duchy_capital_map[duchy] = capital
            duchy_counties_map[duchy] = set(counties)
            county_duchy_map.update((county, duchy) for county in counties)
            landed_titles_index[duchy] = current_index
            current_index += 1
            for county in counties:
                landed_titles_index[county] = current_index
                current_index += 1
    duchy_region_map = {}
    for duchy, counties in duchy_counties_map.items():
        capital = id_county_map[duchy_capital_map[duchy]]
        if capital in counties:
            region = counties.copy()
            for neighbor in county_graph[capital]:
                region.update(duchy_counties_map[county_duchy_map[neighbor]])
            duchy_region_map[duchy] = region
    locs = get_localisation(parser.moddirs)
    out_rows = ['#CODE;ENGLISH;FRENCH;GERMAN;;SPANISH;;;;;;;;;x'.split(';')]
    region_pairs = []
    for region_duchy in sorted(duchy_region_map, key=landed_titles_index.get):
        region_codename = 'arles_region_tradezone_{}'.format(region_duchy)
        capital_loc = locs['PROV{}'.format(duchy_capital_map[region_duchy])]
        region_name = 'Potential {} Trade Zone'.format(capital_loc)
        out_rows.append([region_codename, region_name] + [''] * 12 + ['x'])
        counties = duchy_region_map[region_duchy]
        duchies = set()
        for filter_duchy, filter_counties in duchy_counties_map.items():
            if filter_counties and filter_counties <= counties:
                counties -= filter_counties
                duchies.add(filter_duchy)
        region_pair = Pair(region_codename)
        if duchies:
            duchies = sorted(duchies, key=landed_titles_index.get)
            duchies_obj = Obj([String(duchy) for duchy in duchies])
            region_pair.value.contents.append(Pair('duchies', duchies_obj))
        if counties:
            counties = sorted(counties, key=landed_titles_index.get)
            counties_obj = Obj([String(county) for county in counties])
            region_pair.value.contents.append(Pair('counties', counties_obj))
        region_pairs.append(region_pair)
    region_tree = TopLevel(region_pairs)
    
    regions_out_path = rootpath / 'arles-regions.txt'
    with regions_out_path.open('w', encoding='cp1252') as fp:
        print(region_tree.str(parser), file=fp)
    events_out_path = rootpath / 'arles-events.txt'
    with events_out_path.open('w', encoding='cp1252') as fp:
        print(events_tree.str(parser), file=fp)
    loc_out_path = rootpath / 'arles-locs.csv'
    with loc_out_path.open('w', encoding='cp1252', newline='') as fp:
        csv.writer(fp, dialect='ckii').writerows(out_rows)

if __name__ == '__main__':
    main()
