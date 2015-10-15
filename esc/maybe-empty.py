#!/usr/bin/env python3

import collections
import pathlib
import sys
import ck2parser
import localpaths

def get_modpath():
    if len(sys.argv) <= 1:
        return localpaths.rootpath / 'SWMH-BETA/SWMH'
    return pathlib.Path(sys.argv[1])

def output(provinces):
    print(*provinces, sep='\n')

def process_provinces(where):
    tree = ck2parser.parse_file(where / 'map/default.map')
    defs = next(v.val for n, v in tree if n.val == 'definitions')
    id_name = {}
    for row in ck2parser.csv_rows(where / 'map' / defs):
        try:
            id_name[int(row[0])] = row[4]
        except (IndexError, ValueError):
            continue
    province_id = {}
    tribals = set()
    for path in ck2parser.files('history/provinces/*', where):
        number, name = path.stem.split(' - ')
        number = int(number)
        if id_name[number] == name:
            tree = ck2parser.parse_file(path)
            for n, v in tree:
                if isinstance(v, ck2parser.Obj):
                    if any(v2.val == 'tribal' for _, v2 in v):
                        tribals.add(number)
                elif n.val == 'title':
                    province_id[v.val] = number
                elif v.val == 'tribal':
                    tribals.add(number)
    return province_id, tribals

def process_titles(where):
    nomads = set()
    vassals = collections.defaultdict(set)
    for path, tree in ck2parser.parse_files('history/titles/*', where):
        title = path.stem
        if not title.startswith('b'):
            for n, v in tree:
                for n2, v2 in v:
                    if n2.val == 'liege':
                        liege = v2.val
                        if liege != title:
                            vassals[v2.val].add(title)
                    elif n2.val == 'historical_nomad' and v2.val == 'yes':
                        nomads.add(title)
    return nomads, vassals

def main():
    modpath = get_modpath()
    province_id, tribals = process_provinces(modpath)
    nomads, vassals = process_titles(modpath)
    maybe_empty = set()
    visited = set()

    def check_nomad(title):
        if title not in visited:
            visited.add(title)
            if title.startswith('c'):
                number = province_id[title]
                if number in tribals:
                    maybe_empty.add(number)
            else:
                for vassal in vassals[title]:
                    check_nomad(vassal)

    for title in nomads:
        check_nomad(title)
    output(sorted(maybe_empty))

if __name__ == '__main__':
    main()
