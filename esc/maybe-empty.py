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
    no_castles_or_cities = set()
    for path in ck2parser.files('history/provinces/*', where):
        number, name = path.stem.split(' - ')
        number = int(number)
        if id_name[number] == name:
            tree = ck2parser.parse_file(path)
            castles_and_cities = set()
            changes_by_date = {}
            for n, v in tree:
                if n.val == 'title':
                    province_id[v.val] = number
                elif (isinstance(n, ck2parser.Date) and
                      isinstance(v, ck2parser.Obj)):
                    changes_by_date[n.val] = v.contents
                elif v.val == 'castle' or v.val == 'city':
                    castles_and_cities.add(n.val)
            if not castles_and_cities:
                no_castles_or_cities.add(number)
                continue
            for _, changes in sorted(changes_by_date.items()):
                for n, v in changes:
                    if n.val == 'remove_settlement':
                        castles_and_cities.discard(v.val)
                    elif v.val == 'castle' or v.val == 'city':
                        castles_and_cities.add(n.val)
                if not castles_and_cities:
                    no_castles_or_cities.add(number)
                    break
    return province_id, no_castles_or_cities

def process_titles(where):
    nomads = set()
    vassals = collections.defaultdict(set)
    for path in ck2parser.files('history/titles/*', where):
        title = path.stem
        if not title.startswith('b'):
            tree = ck2parser.parse_file(path)
            for n, v in tree:
                for n2, v2 in v:
                    if isinstance(v2, ck2parser.String):
                        if n2.val == 'liege':
                            liege = v2.val
                            if liege != title:
                                vassals[v2.val].add(title)
                        elif n2.val == 'historical_nomad' and v2.val == 'yes':
                            nomads.add(title)
    return nomads, vassals

def main():
    modpath = get_modpath()
    province_id, no_castles_or_cities = process_provinces(modpath)
    nomads, vassals = process_titles(modpath)
    maybe_empty = set()

    def check_nomad(title):
        if title.startswith('c'):
            number = province_id[title]
            if number in no_castles_or_cities:
                maybe_empty.add(number)
        else:
            for vassal in vassals[title]:
                check_nomad(vassal)

    for title in nomads:
        check_nomad(title)
    output(sorted(maybe_empty))

if __name__ == '__main__':
    main()
