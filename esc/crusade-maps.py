#!/usr/bin/env python3

import collections
from ck2parser import rootpath, vanilladir, is_codename, Obj, SimpleParser
from print_time import print_time

modpath = rootpath / 'SWMH-BETA/SWMH'
epoch = 1066, 9, 15

def get_crsdr_grp_map(parser):
    crsdr_grp_map = {}
    for _, tree in parser.parse_files('common/religions/*', modpath):
        for n, v in tree:
            for n2, v2 in v:
                if (isinstance(v2, Obj) and
                    n2.val not in ('male_names', 'female_names') and
                    v2.has_pair('can_call_crusade', 'yes')):
                    crsdr_grp_map[n2.val] = n.val
                    crsdr_grp_map[n.val] = None
    return crsdr_grp_map

def process_landed_titles(parser, crsdr_grp_map):
    def recurse(v, n=None):
        for n2, v2 in v:
            if is_codename(n2.val):
                yield from recurse(v2, n2)
            elif n is not None and n2.val in crsdr_grp_map:
                if crsdr_grp_map[n2.val] is None:
                    for relg in grp_crsdr_map[n2.val]:
                        yield n.val, relg, v2.val
                else:
                    yield n.val, n2.val, v2.val

    grp_crsdr_map = collections.defaultdict(list)
    for k, v in crsdr_grp_map.items():
        grp_crsdr_map[v].append(k)
    for _, tree in parser.parse_files('common/landed_titles/*', modpath):
        yield from recurse(tree)

@print_time
def main():
    parser = SimpleParser()
    crsdr_grp_map = get_crsdr_grp_map()
    relg_weights = {relg: {} for relg in crsdr_grp_map
                             if crsdr_grp_map[relg] is not None}
    weight_counts = collections.Counter()
    for title, relg, weight in process_landed_titles(parser, crsdr_grp_map):
        assert title not in relg_weights[relg]
        relg_weights[relg][title] = weight
        weight_counts[weight] += 1
    
    for weight, count in sorted(weight_counts.items(), reverse=True):
        print('{:6} {:3}'.format(weight, count))

if __name__ == '__main__':
    main()

 # 10000   2
 #  9000   2
 #  8500   2
 #  8000   2
 #  7000   3
 #  4000   8
 #  3000   2
 #  2500   3
 #  2000   1
 #  1500   1
 #  1000  13
 #   800   1
 #   600   1
 #   500  31
 #   400  29
 #   375   2
 #   350  17
 #   300  40
 #   250  27
 #   225   1
 #   200  51
 #   150  24
 #   125   7
 #   120   6
 #   100  44
 #    90   2
 #    75  12
 #    50  12
 #    40   1
 #    30   6
 #    25  71
 #    20   1
 #    15   1
 #    10  12
