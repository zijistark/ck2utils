#!/usr/bin/env python3

import csv
from itertools import combinations
import networkx as nx
import numpy as np
from PIL import Image
from ck2parser import rootpath, csv_rows, get_localisation, SimpleParser
from print_time import print_time


@print_time
def main():
    parser = SimpleParser(rootpath / 'SWMH-BETA/SWMH')
    rgb_id_map = {}
    id_name_map = {}
    default_tree = parser.parse_file('map/default.map')
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
    rivers = [x.val for x in default_tree['major_rivers']]
    land_or_river = set(id_county_map) | set(rivers)
    province_graph = nx.Graph()
    provinces_path = parser.file('map/' + default_tree['provinces'].val)
    a = np.array(Image.open(str(provinces_path)))
    prov_position = {}
    for n, v in parser.parse_file('map/' + default_tree['positions'].val):
        pos = v['position'].contents
        prov_position[n.val] = int(pos[2].val), a.shape[0] - int(pos[3].val)
    for i, j in np.ndindex(a.shape[0] - 1, a.shape[1] - 1):
        province = rgb_id_map.get(tuple(a[i, j]), 0)
        if province in land_or_river:
            province_graph.add_node(province)
            neighbor_x = rgb_id_map.get(tuple(a[i, j + 1]), 0)
            neighbor_y = rgb_id_map.get(tuple(a[i + 1, j]), 0)
            for neighbor in (neighbor_x, neighbor_y):
                if neighbor != province and neighbor in land_or_river:
                    province_graph.add_edge(province, neighbor)
    river_adjacencies = []
    riverside = set()
    for river in rivers:
        adjacents = [x for x in province_graph.neighbors_iter(river)
                     if x not in rivers]
        riverside.update(adjacents)
        for one, two in combinations(adjacents, 2):
            if not province_graph.has_edge(one, two):
                (x0, y0), (x1, y1) = prov_position[one], prov_position[two]
                steep = abs(y1 - y0) > abs(x1 - x0)
                if steep:
                    x0, y0, x1, y1 = y0, x0, y1, x1
                if x1 < x0:
                    x0, y0, x1, y1 = x1, y1, x0, y0
                dx = x1 - x0
                dy = y1 - y0
                d = 2 * dy - dx
                y = y0
                for x in range(x0, x1):
                    rgb = tuple(a[(x, y) if steep else (y, x)])
                    prov = rgb_id_map.get(rgb, 0)
                    if prov not in (one, two, river):
                        break
                    if d > 0:
                        y += 1 if y0 <= y1 else -1
                        d -= dx
                    d += dy
                else:
                    river_adjacencies.append((one, two, river))
    riverside_no_adj = {x for x in riverside
                        if not any(x in y for y in river_adjacencies)}
    old_adjacencies = []
    for row in csv_rows(parser.file('map/' + default_tree['adjacencies'].val)):
        try:
            if row[2] == 'major_river':
                old_adjacencies.append((int(row[0]), int(row[1]), int(row[3])))
        except ValueError:
            pass
    print('{} probable correct river adjacencies'.format(len(river_adjacencies)))
    false_pos = []
    for one, two, river in old_adjacencies:
        try:
            river_adjacencies.remove((two, one, river)
                                     if two < one else (one, two, river))
        except ValueError:
            false_pos.append((one, two, river))
    if false_pos:
        print('{} probable wrong river adjacencies:'.format(len(false_pos)),
              end='\n\t')
        print(*false_pos, sep='\n\t')
    if river_adjacencies:
        print('{} probable missing river adjacencies:'
              .format(len(river_adjacencies)), end='\n\t')
        print(*river_adjacencies, sep='\n\t')


if __name__ == '__main__':
    main()
