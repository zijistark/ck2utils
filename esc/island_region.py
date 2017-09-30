#!/usr/bin/env python3

from pathlib import Path
import re
import sys
import networkx as nx
import numpy as np
from PIL import Image
from ck2parser import (rootpath, csv_rows, SimpleParser, is_codename, Pair,
                       Number, TopLevel, FullParser)
from print_time import print_time


@print_time
def main():
    parser = SimpleParser()
    if len(sys.argv) > 1:
        parser.moddirs.append(Path(sys.argv[1]))
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
    county_id_map = {}
    for path in parser.files('history/provinces/* - *.txt'):
        prov_id, prov_name = path.stem.split(' - ')
        prov_id = int(prov_id)
        if id_name_map.get(prov_id) == prov_name:
            try:
                county = parser.parse_file(path)['title'].val
            except KeyError:
                continue
            id_county_map[prov_id] = county
            county_id_map[county] = prov_id
    province_graph = nx.Graph()
    provinces_path = parser.file('map/' + default_tree['provinces'].val)
    a = np.array(Image.open(str(provinces_path)))
    for i, j in np.ndindex(a.shape[0] - 1, a.shape[1] - 1):
        province = rgb_id_map.get(tuple(a[i, j]))
        if province in id_county_map:
            province_graph.add_node(province)
            for coords in ((i, j + 1), (i + 1, j)):
                neighbor = rgb_id_map.get(tuple(a[coords]))
                if neighbor != province and neighbor in id_county_map:
                    province_graph.add_edge(province, neighbor)
    for row in csv_rows(parser.file('map/' + default_tree['adjacencies'].val)):
        try:
            one, two = int(row[0]), int(row[1])
        except ValueError:
            continue
        if one in id_county_map and two in id_county_map:
            province_graph.add_edge(one, two)
    regions = [set(c) for c in sorted(nx.connected_components(province_graph),
                                      key=min) if 333 not in c]
    titles = []

    def recurse(tree):
        parent_provs = set()
        for n, v in tree:
            if n.val.startswith('c_'):
                child_provs = {county_id_map[n.val]}
            elif re.match(r'[ekd]_', n.val):
                child_provs = recurse(v)
            else:
                continue
            if child_provs:
                titles.append((n.val, child_provs))
                parent_provs |= child_provs
        return parent_provs

    for _, tree in parser.parse_files('common/landed_titles/*.txt'):
        recurse(tree)
    code = TopLevel()
    for region in regions:
        min_title, min_score = None, float('inf')
        for title, title_provs in reversed(titles):
            score = len(region ^ title_provs)
            if score < min_score:
                min_title = title
                min_score = score
                if score == 0:
                    break
        name = 'region_' + min_title[2:]
        r_def = Pair(name, [Pair('provinces',
                                 [Number(x) for x in sorted(region)])])
        code.contents.append(r_def)
    header_comments = '''
        # -*- ck2 -*-

        # Island regions - no land path from the continent
        # The AI needs these to optimize path finding
        #
        # NOTE: do not add any regions here that are NOT islands

        # Regions can be declared with one or more of the following fields:
        #   duchies = { }, takes duchy title names declared in landed_titles.txt
        #   counties = { }, takes county title names declared in landed_titles.txt
        #   provinces = { }, takes province id numbers declared in /history/provinces
        #   regions = { }, a region can also include other regions, however the subregions needs to be declared before the parent region.
        #       E.g. If the region world_europe contains the region world_europe_west then world_europe_west needs to be declared as a region before (i.e. higher up in this file) world_europe.
        '''
    full_parser = FullParser()
    code.pre_comments[:0] = full_parser.parse(header_comments).post_comments
    path = rootpath
    if parser.moddirs:
        path = parser.moddirs[0] / 'map'
    path = path / 'island_region.txt'
    full_parser.no_fold_to_depth = 0
    full_parser.newlines_to_depth = 0
    full_parser.write(code, path)


if __name__ == '__main__':
    main()
