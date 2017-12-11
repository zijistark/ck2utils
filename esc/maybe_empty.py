#!/usr/bin/env python3

import collections
import pathlib
import sys
from ck2parser import rootpath, get_provinces, is_codename, Obj, SimpleParser
from print_time import print_time

def get_modpath():
    if len(sys.argv) <= 1:
        # return rootpath / 'SWMH-BETA/SWMH'
        return []
    return [pathlib.Path(sys.argv[1])]

def output(provinces):
    print(*provinces, sep='\n')

def get_start_interval(parser):
    dates = []
    for _, tree in parser.parse_files('common/bookmarks/*.txt'):
        dates.extend(v['date'].val for _, v in tree)
    tree = parser.parse_file('common/defines.txt')
    dates.append(tree['start_date'].val)
    dates.append(tree['last_start_date'].val)
    return min(dates), max(dates)

def process_landed_titles(parser):
    def recurse(tree):
        for n, v in tree:
            if is_codename(n.val):
                titles.add(n.val)
                recurse(v)

    titles = set()
    for _, tree in parser.parse_files('common/landed_titles/*.txt'):
        recurse(tree)
    return titles

def process_provinces(parser, first_start, last_start):
    province_id = {}
    no_castles_or_cities = set()
    for number, title, tree in get_provinces(parser):
        province_id[title] = number
        castles_and_cities = set()
        changes_by_date = collections.defaultdict(list)
        changes_by_date[first_start] = []
        for n, v in tree:
            if isinstance(v, Obj):
                changes_by_date[n.val].extend(v)
            elif v.val in ['castle', 'city']:
                castles_and_cities.add(n.val)
        for date, changes in sorted(changes_by_date.items()):
            for n, v in changes:
                if n.val == 'remove_settlement':
                    castles_and_cities.discard(v.val)
                elif v.val in ['castle', 'city']:
                    castles_and_cities.add(n.val)
            if date >= first_start:
                if date > last_start:
                    break
                if not castles_and_cities:
                    no_castles_or_cities.add(number)
                    break
    return province_id, no_castles_or_cities

def process_titles(parser, valid_titles, first_start, last_start):
    nomads = set()
    vassals = collections.defaultdict(set)
    for path in parser.files('history/titles/*.txt'):
        title = path.stem
        if title in valid_titles and title[0] != 'b':
            tree = parser.parse_file(path)
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
                        nomad = v.val == 'yes'
                if date >= first_start:
                    if date > last_start:
                        break
                    if liege != '0':
                        vassals[liege].add(title)
                    if nomad:
                        nomads.add(title)
    return nomads, vassals

@print_time
def main():
    parser = SimpleParser()
    parser.moddirs = get_modpath()
    titles = process_landed_titles(parser)
    first_start, last_start = get_start_interval(parser)
    province_id, no_castles_or_cities = process_provinces(
        parser, first_start, last_start)
    nomads, vassals = process_titles(parser, titles, first_start, last_start)
    maybe_empty = set()

    def check_nomad(title):
        if title[0] == 'c':
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
