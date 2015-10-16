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

def get_start_interval(where):
    dates = []
    for _, tree in ck2parser.parse_files('common/bookmarks/*', where):
        for n, v in tree:
            dates.append(next(v2.val for n2, v2 in v if n2.val == 'date'))
    tree = ck2parser.parse_file(where / 'common/defines.txt')
    dates.append(next(v.val for n, v in tree if n.val == 'start_date'))
    dates.append(next(v.val for n, v in tree if n.val == 'last_start_date'))
    return min(dates), max(dates)

def process_provinces(where, first_start, last_start):
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
            changes_by_date = collections.defaultdict(list)
            changes_by_date[first_start] = []
            for n, v in tree:
                if n.val == 'title':
                    province_id[v.val] = number
                elif isinstance(v, ck2parser.Obj):
                    changes_by_date[n.val].extend(v)
                elif v.val == 'castle' or v.val == 'city':
                    castles_and_cities.add(n.val)
            for date, changes in sorted(changes_by_date.items()):
                for n, v in changes:
                    if n.val == 'remove_settlement':
                        castles_and_cities.discard(v.val)
                    elif v.val == 'castle' or v.val == 'city':
                        castles_and_cities.add(n.val)
                if date >= first_start:
                    if date > last_start:
                        break
                    if not castles_and_cities:
                        no_castles_or_cities.add(number)
                        break
    return province_id, no_castles_or_cities

def process_titles(where, first_start, last_start):
    nomads = set()
    vassals = collections.defaultdict(set)
    for path in ck2parser.files('history/titles/*', where):
        title = path.stem
        if not title.startswith('b'):
            tree = ck2parser.parse_file(path)
            changes_by_date = collections.defaultdict(list)
            changes_by_date[first_start] = []
            for n, v in tree:
                changes_by_date[n.val].extend(v)
            liege = '0'
            nomad = False
            for date, changes in sorted(changes_by_date.items()):
                for n, v in changes:
                    if n.val == 'liege':
                        liege = str(v.val) if v.val != title else '0'
                    elif n.val == 'historical_nomad':
                        nomad = True if v.val == 'yes' else False
                if date >= first_start:
                    if date > last_start:
                        break
                    if liege != '0':
                        vassals[liege].add(title)
                    if nomad:
                        nomads.add(title)
    return nomads, vassals

def main():
    modpath = get_modpath()
    first_start, last_start = get_start_interval(modpath)
    province_id, no_castles_or_cities = process_provinces(modpath, first_start,
                                                          last_start)
    nomads, vassals = process_titles(modpath, first_start, last_start)
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
