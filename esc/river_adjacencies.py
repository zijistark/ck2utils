#!/usr/bin/env python3

from collections import defaultdict
import csv
from itertools import combinations
from pathlib import Path
import sys
import networkx as nx
import numpy as np
from PIL import Image
from ck2parser import rootpath, csv_rows, SimpleParser
from print_time import print_time


@print_time
def main():
    modpath = (Path(sys.argv[1])
               if len(sys.argv) > 1 else rootpath / 'SWMH-BETA/SWMH')
    parser = SimpleParser(modpath)
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
    for path in parser.files('history/provinces/* - *.txt'):
        prov_id, prov_name = path.stem.split(' - ')
        prov_id = int(prov_id)
        if id_name_map.get(prov_id) == prov_name:
            try:
                id_county_map[prov_id] = parser.parse_file(path)['title'].val
            except KeyError:
                continue
    rivers = {x.val: ([], []) for x in default_tree['major_rivers']}
    land_or_river = set(id_county_map) | set(rivers)
    province_graph = nx.Graph()
    provinces_path = parser.file('map/' + default_tree['provinces'].val)
    a = np.array(Image.open(str(provinces_path)))
    for i, j in np.ndindex(a.shape[0] - 1, a.shape[1] - 1):
        province = rgb_id_map.get(tuple(a[i, j]))
        if province in land_or_river:
            province_graph.add_node(province)
            if province in rivers:
                rivers[province][0].append((i, j))
            for coords in ((i, j + 1), (i + 1, j)):
                neighbor = rgb_id_map.get(tuple(a[coords]))
                if neighbor != province and neighbor in land_or_river:
                    province_graph.add_edge(province, neighbor)
                    if province in rivers and neighbor not in rivers:
                        rivers[province][1].append(coords)
                    if neighbor in rivers and province not in rivers:
                        rivers[neighbor][1].append((i, j))
    river_adjacencies = defaultdict(set)
    for river, (river_px, border_px) in rivers.items():
        if not river_px:
            print('WARNING: no area for {}'.format(river))
            continue
        if not border_px:
            print('WARNING: no border for {}'.format(river))
            continue
        for i0, j0 in river_px:
            min_item, min_val = None, float('inf')
            for i1, j1 in border_px:
                sqdist = (i1 - i0) * (i1 - i0) + (j1 - j0) * (j1 - j0)
                if sqdist < min_val:
                    min_val = sqdist
                    min_item = i1, j1
            px = a[min_item]
            a[i0, j0] = px
            province = rgb_id_map[tuple(px)]
            for coords in [(i0 - 1, j0), (i0, j0 - 1),
                           (i0, j0 + 1), (i0 + 1, j0)]:
                neighbor = rgb_id_map.get(tuple(a[coords]))
                if (neighbor != province and neighbor in id_county_map and
                    not province_graph.has_edge(province, neighbor)):
                    if neighbor < province:
                        river_adjacencies[neighbor, province].add(river)
                    else:
                        river_adjacencies[province, neighbor].add(river)
    old_adjacencies = []
    for row in csv_rows(parser.file('map/' + default_tree['adjacencies'].val)):
        try:
            if row[2] == 'major_river':
                one, two, river = int(row[0]), int(row[1]), int(row[3])
                if two < one:
                    one, two = two, one
                if river in river_adjacencies[one, two]:
                    river_adjacencies[one, two] = {river}
                old_adjacencies.append((river, one, two))
        except ValueError:
            pass
    for (one, two), rivers in river_adjacencies.items():
        if len(rivers) > 1:
            print('Multiple adjacency for {} ({}) and {} ({}) across {}'
                .format(id_name_map[one], one, id_name_map[two], two, rivers))
    river_adjacencies = sorted(
        (r, a, b) for (a, b), rs in river_adjacencies.items() for r in rs)
    for r, a, b in river_adjacencies:
        print('{};{};major_river;{};-1;-1;-1;-1;{}-{}{}'.format(a, b, r,
              id_name_map[a], id_name_map[b],
              '*' if (r, a, b) not in old_adjacencies else ''))
    num_adj = len(river_adjacencies)
    false_pos = []
    for r, a, b in old_adjacencies:
        try:
            river_adjacencies.remove((r, a, b))
        except ValueError:
            false_pos.append((r, '{} ({})'.format(id_name_map[a], a),
                              '{} ({})'.format(id_name_map[b], b)))
    print('{} probable correct river adjacencies'
          .format(num_adj - len(river_adjacencies)))
    if false_pos:
        print('{} probable wrong river adjacencies:'.format(len(false_pos)),
              end='\n\t')
        print(*false_pos, sep='\n\t')
    if river_adjacencies:
        print('{} probable missing river adjacencies'
              .format(len(river_adjacencies)))


if __name__ == '__main__':
    main()
