#!/usr/bin/env python3

from collections import defaultdict
import re
import pprint
import networkx
import numpy
import PIL
import PIL.Image
from ck3parser import SimpleParser, csv_rows, Date, Pair
from print_time import print_time

EARLIEST_DATE = (float('-inf'),) * 3

parser = SimpleParser()

@print_time
def main():
    when = 867, 1, 1
    process_landed_titles(parser.parse_files('common/landed_titles/*.txt'))
    process_title_history(parser.parse_files('history/titles/*.txt'))
    map_data_paths = parse_default_map(parser.file('map_data/default.map'))
    for row in csv_rows(parser.file(map_data_paths['definitions'])):
        process_map_definitions_row(row)
    parse_provinces_map(parser.file(map_data_paths['provinces']))
    for row in csv_rows(parser.file(map_data_paths['adjacencies'])):
        process_map_adjacencies_row(row)
    compute_higher_tier_adjacencies(when)
    duchy_cover(when)


def process_landed_titles(txts):
    def recurse(v, parent_title=None):
            for p2 in v:
                # TODO parser treats "color = hsv{ 0.98 0.9 0.9 }" as a pair followed by an obj.... fix this
                if not isinstance(p2, Pair):
                    continue
                n2, v2 = p2
                if Title.valid_codename(n2.val):
                    title = Title.get(n2.val, create_if_missing=True)
                    if parent_title:
                        title.set_liege(parent_title)
                    recurse(v2, title)
                elif n2.val == 'province':
                    Title.id_title_map[v2.val] = parent_title

    for _, v in txts:
        recurse(v)


def parse_default_map(default_map_path):
    needed = {'definitions', 'provinces', 'adjacencies'}
    paths = {}
    with open(str(default_map_path)) as f:
        for line in f:
            if match := re.match(r'(\w+) = "([^"]*)"', line):
                k, v = match.groups()
                if k in needed:
                    paths[k] = 'map_data/' + v
                    needed.remove(k)
                    if not needed:
                        break
    return paths


def process_map_definitions_row(row):
    try:
        province, red, green, blue = map(int, row[:4])
    except ValueError:
        return
    key = tuple(numpy.uint8(x) for x in (red, green, blue))
    assert key not in Title.rgb_id_map
    Title.rgb_id_map[key] = province


# pre: process map definitions
def parse_provinces_map(path):
    def province_id(rgb):
        return Title.rgb_id_map.get(tuple(rgb), 0)

    image = PIL.Image.open(str(path))
    image = numpy.array(image)
    for i, j in numpy.ndindex(image.shape[0] - 1, image.shape[1] - 1):
        province = province_id(image[i, j])
        if province != 0:
            neighbor_x = province_id(image[i, j + 1])
            neighbor_y = province_id(image[i + 1, j])
            for neighbor in [neighbor_x, neighbor_y]:
                if neighbor != province and neighbor != 0:
                    Title.province_graph.add_edge(province, neighbor)


def process_map_adjacencies_row(row):
    try:
        from_province, to_province = map(int, row[:2])
    except ValueError:
        return
    Title.province_graph.add_edge(from_province, to_province)

# pre: landed titles
def process_title_history(txts):
    for _, v in txts:
        for n2, v2 in v:
            try:
                title = Title.get(n2.val)
            except KeyError:
                continue
            for n3, v3 in v2:
                if isinstance(n3, Date) and (liege := v3.get('de_jure_liege')):
                    title.set_liege(liege.val, from_when=n3.val)


# pre: provinces map, map adjacencies, title history
def compute_higher_tier_adjacencies(when):
    for u, v in Title.province_graph.edges:
        try:
            l_u, l_v = (Title.id_title_map[x].liege(when).codename for x in (u, v))
            if l_u is not l_v:
                Title.county_graph.add_edge(l_u, l_v)
        except KeyError:
            pass
    for u, v in Title.county_graph.edges:
        l_u, l_v = (Title.get(x).liege(when).codename for x in (u, v))
        if l_u is not l_v:
            Title.duchy_graph.add_edge(l_u, l_v)
    for u, v in Title.duchy_graph.edges:
        l_u, l_v = (Title.get(x).liege(when).codename for x in (u, v))
        if l_u is not l_v:
            Title.kingdom_graph.add_edge(l_u, l_v)
    for u, v in Title.kingdom_graph.edges:
        l_u, l_v = (Title.get(x).liege(when).codename for x in (u, v))
        if l_u is not l_v:
            Title.empire_graph.add_edge(l_u, l_v)


def duchy_cover(when):
    duchies = sorted(d.codename for d in Title.by_tier('d'))
    literals = list(range(1, 1 + len(duchies)))
    duchy_literal_map = dict(zip(duchies, literals))
    literal_duchy_map = dict(zip(literals, duchies))
    clauses = compute_clauses(when, duchy_literal_map)
    output_clauses('sat-clauses.txt', clauses)


# finding minimal set of duchies that is adjacent to every kingdom
# this is SORTA NOT REALLY the binate covering problem, a special case of maxsat & of mincostsat
# partial maxsat
#     hard clauses
#         at least one node in or adjacent to every kingdom
#             (CNF clauses: [[nodes in or adjacent] for each kingdom])
#             (for each duchy edge, count both duchies for both kingdoms (+ each node's own))
#         nodes connected... within reason...
#             count sea adjacencies until the whole map is connected?
#                     detect all sea/sailable provinces (not rivers)
#                     all provinces adjacent to them are adjacent to each other
#                     then propagate existing logic for counties, duchies, etc
#                 and exclude iceland, etc.
#             or... add kent <-> flanders as a special case and then exclude iceland etc?
#             [if node, then at least one adjacent node <=== NOT CORRECT]
#                 [(CNF clauses: [[not-node] + [adjacent nodes] for each node])]
#     soft clauses
#         (CNF clauses: [[not-node] for each node])
# maybe just try without connectivity just to see what we get since that might be all i can get
def compute_clauses(when, duchy_literal_map):
    duchies_near_kingdom = defaultdict(set)
    for d, adj in Title.duchy_graph.adjacency():
        k = Title.get(d).liege(when).codename
        duchies_near_kingdom[k] |= {d} | set(adj)
    kingdom_clauses = [[duchy_literal_map[d] for d in s]
                       for s in duchies_near_kingdom.values()] # undefined sort order
    connectivity_clauses = [] # :(
    duchy_count_clauses = [[-duchy_literal_map[d]] for d in Title.duchy_graph] # undefined sort order
    return {
        'literals': sorted(duchy_literal_map.values()),
        'hard': kingdom_clauses + connectivity_clauses,
        'soft': duchy_count_clauses,
        'duchy_literal_map': duchy_literal_map
    }


def output_clauses(path, clauses):
    with open(path, 'w') as f:
        pprint.pprint(clauses, f)


class Title:
    instances = {}
    id_title_map = {}
    rgb_id_map = {}
    graphs = [networkx.Graph() for _ in range(5)]
    empire_graph = graphs[0]
    kingdom_graph = graphs[1]
    duchy_graph = graphs[2]
    county_graph = graphs[3]
    province_graph = graphs[4]
    graph_by_tier = dict(zip('ekdc', graphs))

    @classmethod
    def valid_codename(cls, string):
        try:
            return re.match(r'[ekdcb]_', string)
        except TypeError:
            return False

    @classmethod
    def all(cls):
        return Title.instances.values()

    @classmethod
    def by_tier(cls, tier):
        return (title for title in Title.all()
                if title.codename.startswith(tier + '_'))

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
        self.lieges = {}
        Title.instances[codename] = self
        if g := Title.graph_by_tier.get(codename[0]):
            g.add_node(codename)

    def set_liege(self, liege, from_when=EARLIEST_DATE):
        liege = Title.get(liege)
        self.lieges[from_when] = liege

    def liege(self, when=EARLIEST_DATE):
        try:
            return self.lieges[max(date for date in self.lieges if
                                   date <= when)]
        except ValueError:
            return None


if __name__ == '__main__':
    main()
