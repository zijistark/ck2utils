from collections import defaultdict
import heapq
import itertools
import math
import pickle
import random
import re
import PIL.Image
import PIL.ImageDraw
from evol import Population
import networkx
import numpy as np
from ck3parser import rootpath, SimpleParser, csv_rows
from print_time import print_time


def read_game_data():
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

    def parse_provinces_map(path, width, skip_provinces):
        def province_id(rgb):
            return rgb_id_map.get(tuple(rgb), 0)

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
                    if neighbor != province and neighbor != 0 and neighbor not in skip_provinces:
                        province_graph.add_edge(province, neighbor)

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
            else: # todo andaman sea wrongly marked as non-coastal; has 'impassable terrain' islands next to it
                terrain = default_sea
            province_graph.nodes[prov]['terrain'] = terrain

    parser = SimpleParser()
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
        parser.file(map_data_paths['provinces']), width, province_types['skip'])
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


def draw_path(draw, path, province_graph):
    centers = province_graph.nodes.data('center')
    coords = [centers[p] for p in path]
    draw.line(coords, fill=(192, 0, 0), width=3, joint='curve')


def shortest_path_any_target(G, source, targets):
    paths = {source: [source]}
    dist = {}  # dictionary of final distances
    seen = {}
    fringe = []
    seen[source] = 0
    heapq.heappush(fringe, (0, source))
    while fringe:
        d, v = heapq.heappop(fringe)
        if v in dist:
            continue  # already searched this node
        dist[v] = d
        if v in targets:
            break
        for u, e in G.adj[v].items():
            vu_dist = dist[v] + e['weight']
            if u not in dist and (u not in seen or vu_dist < seen[u]):
                seen[u] = vu_dist
                heapq.heappush(fringe, (vu_dist, u))
                paths[u] = paths[v] + [u]

    return paths[v]


def extend_path(path, edges, part):
    path = path[::]
    for p in part:
        edge = path[-1], p
        if edge in edges:
            index = edges[edge]
            for k, v in list(edges.items()):
                if v >= index:
                    del edges[k]
            path = extend_path(
                path[:index + 1], edges, path[-2:index + 1:-1])
        edges[edge] = len(path) - 1
        path.append(p)
    return path


def ensure_connectivity(path, province_graph):
    pass


def complete_missing_colors():
    pass

def create_candidate_smart(provs_with_terrain, province_graph):
    terrain = province_graph.nodes.data('terrain')
    all_provs = list(province_graph)

    def inner():
        target_terrains = set(provs_with_terrain)
        targets = set(province_graph)
        path = [random.choice(all_provs)]
        # deterministic thenceforth... not random enough?
        target_terrains.discard(terrain[path[-1]])
        targets.difference_update(provs_with_terrain[terrain[path[-1]]])
        edges = {}
        while targets:
            part = shortest_path_any_target(
                province_graph, path[-1], targets)[1:]
            path = extend_path(path, edges, part)
            for p in part:
                if terrain[p] in target_terrains:
                    target_terrains.discard(terrain[p])
                    targets.difference_update(provs_with_terrain[terrain[p]])
        return path

    return inner


def create_candidate(provs_with_terrain, province_graph):
    # todo make conform to spec
    terrain = province_graph.nodes.data('terrain')
    all_provs = list(province_graph)

    def inner():
        target_terrains = set(provs_with_terrain)
        targets = set(province_graph)
        path = [random.choice(all_provs)]
        target_terrains.discard(terrain[path[-1]])
        targets.difference_update(provs_with_terrain[terrain[path[-1]]])
        edges = {}
        while targets:
            part = shortest_path_any_target(
                province_graph, path[-1], targets)[1:]
            path = extend_path(path, edges, part)
            for p in part:
                if terrain[p] in target_terrains:
                    target_terrains.discard(terrain[p])
                    targets.difference_update(provs_with_terrain[terrain[p]])
        return path

    return inner


def func_to_optimize(province_graph):
    def inner(x):
        return sum(province_graph.edges[e]['weight'] for e in itertools.pairwise(x))
    return inner


def find_crossover(dad, mom):
    pds = list(range(len(dad)))
    random.shuffle(pds)
    while pds:
        pd = pds.pop()
        if dad[pd] in mom:
            pm = mom.index(dad[pd])
            return pd, pm
    return None


def pick_random_parents(pop):
    while True:
        dad, mom = random.choices(pop, weights=[i.fitness for i in pop], k=2)
        if find_crossover(dad.chromosome, mom.chromosome):
            return dad, mom
        # theoretical possibility of infinite loop if no chromosomes overlap :(
        # very unlikely


def make_child(cd, cm):
    pd, pm = find_crossover(cd, cm)
    c1 = cd[:pd] + cm[pm:]
    c2 = cm[:pm] + cd[pd:]
    # todo fix c1 and c2
    yield c1
    yield c2

# ok... 2015 GA is low optimality high speed.
# 2018 VNS is medium optimality medium speed.
# 2020 A-GLKH is high optimality medium speed.
# unclear which speed is higher at n=9000, m=23000, k=16
# probably aglkh?
@print_time
def main():
    try:
        with open(rootpath / 'ck3_province_graph.pickle', 'rb') as f:
            province_graph = pickle.load(f)
        with open(rootpath / 'ck3_colored_province_map.png') as f:
            colored_province_map = PIL.Image.open(
                str(rootpath / 'ck3_colored_province_map.png'))
    except:
        province_graph, colored_province_map = read_game_data()
        with open(rootpath / 'ck3_province_graph.pickle', 'wb') as f:
            pickle.dump(province_graph, f, pickle.HIGHEST_PROTOCOL)
        colored_province_map.save(
            str(rootpath / 'ck3_colored_province_map.png'))
    print(len(province_graph.nodes), len(province_graph.edges), 16)

    provs_with_terrain = defaultdict(list)
    for p, t in province_graph.nodes.data('terrain'):
        provs_with_terrain[t].append(p)

    popsize = 5
    pop = Population.generate(
        init_function=create_candidate(provs_with_terrain, province_graph),
        eval_function=func_to_optimize(province_graph),
        size=popsize,
        maximize=False)
    pop = pop.breed(parent_picker=pick_random_parents, combiner=make_child)
    pop = pop.evaluate()
    # pop = pop.survive(n=(popsize-2))

    draw = PIL.ImageDraw.Draw(colored_province_map)
    # for p, d in province_graph.nodes.data():
    #     draw.text(d['center'], d['terrain'])
    draw_path(draw, pop.current_best.chromosome or next(
        pop.chromosomes), province_graph)
    out_path = rootpath / 'ck3_testmap.png'
    colored_province_map.save(str(out_path))


if __name__ == '__main__':
    main()
