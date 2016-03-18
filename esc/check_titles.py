#!/usr/bin/env python3

import collections
import csv
import pathlib
import pprint
import re
import sys
import shutil
import tempfile
from ck2parser import (rootpath, vanilladir, is_codename, files, Obj, csv_rows,
                       SimpleParser)
from print_time import print_time

modpath = rootpath / 'SWMH-BETA/SWMH'
minipath = rootpath / 'MiniSWMH/MiniSWMH'

MINISWMH = False

VANILLA_HISTORY_WARN = True

source_paths = (modpath, minipath) if MINISWMH else (modpath,)

results = {True: collections.defaultdict(list),
           False: collections.defaultdict(list)}

def check_title(v, path, titles, lhs=False, line=None):
    if isinstance(v, str):
        v_str = v
    else:
        v_str = v.val
    if is_codename(v_str) and v_str not in titles:
        if line is None:
            line = '<file>'
        else:
            line.indent = 0
            v_lines = line.inline_str(0)[0].splitlines()
            line = next((l for l in v_lines if not re.match(r'\s*#', l)),
                        v_lines[0])
        results[lhs][path].append(line)
        return False
    return True

def check_titles(parser, path, titles):
    def recurse(tree):
        if tree.has_pairs:
            for p in tree:
                n, v = p
                v_is_obj = isinstance(v, Obj)
                check_title(n, path, titles, v_is_obj, p)
                if v_is_obj:
                    recurse(v)
                else:
                    check_title(v, path, titles, line=p)
        else:
            for v in tree:
                check_title(v, path, titles, line=v)

    recurse(parser.parse_file(path, errors='replace'))

def check_regions(parser, titles, titles_de_jure, duchies_de_jure):
    bad_titles = []
    missing_duchies = list(duchies_de_jure)

    path = (minipath if MINISWMH else modpath) / 'map/geographical_region.txt'
    tree = parser.parse_file(path)
    for n, v in tree:
        world = n.val.startswith('world_')
        for n2, v2 in v:
            for v3 in v2:
                if is_codename(v3.val):
                    check_title(v3, path, titles, line=v3)
                    if v3.val not in titles_de_jure:
                        bad_titles.append(v3.val)
                    elif world and v3.val in missing_duchies:
                        missing_duchies.remove(v3.val)

    return bad_titles, missing_duchies

def check_province_history(parser, titles):
    tree = parser.parse_file(modpath / 'map/default.map')
    defs = tree['definitions'].val
    _max_provinces = int(tree['max_provinces'].val)
    id_name_map = {}
    for row in csv_rows((minipath if MINISWMH else modpath) / 'map' / defs):
        try:
            id_name_map[int(row[0])] = row[4]
        except (IndexError, ValueError):
            continue
    for path in files('history/provinces/*', *source_paths):
        number, name = path.stem.split(' - ')
        number = int(number)
        if number in id_name_map and id_name_map[number] == name:
            check_titles(parser, path, titles)

def process_landed_titles(parser):
    titles = set()
    titles_de_jure = []
    misogyny = []

    def recurse(tree):
        parent_is_titular = True
        for n, v in tree:
            if is_codename(n.val):
                if n.val in titles:
                    print('Duplicate title {}'.format(n.val))
                titles.add(n.val)
                if ('title' in v.dictionary and
                    'title_female' not in v.dictionary):
                    misogyny.append(n.val)
                if n.val.startswith('b_'):
                    titles_de_jure.append(n.val)
                    parent_is_titular = False
                else:
                    is_titular = recurse(v)
                    if not is_titular:
                        titles_de_jure.append(n.val)
                        parent_is_titular = False
        return parent_is_titular

    for path in files('common/landed_titles/*', *source_paths):
        recurse(parser.parse_file(path))
    # print('{} titles, {} de jure'.format(len(titles), len(titles_de_jure)))
    return titles, titles_de_jure, misogyny

@print_time
def main():
    global modpath
    if len(sys.argv) > 1:
        modpath = pathlib.Path(sys.argv[1])
        parser = SimpleParser()
    titles, titles_de_jure, misogyny = process_landed_titles(parser)
    duchies_de_jure = [t for t in titles_de_jure if t.startswith('d_')]
    check_province_history(parser, titles)
    bad_region_titles, missing_duchies = check_regions(
        parser, titles, titles_de_jure, duchies_de_jure)
    for path, tree in parser.parse_files('history/titles/*.txt',
                                         *source_paths, errors='replace',
                                         cache=True):
        if tree.contents:
            good = check_title(path.stem, path, titles)
            if (VANILLA_HISTORY_WARN and not good and
                modpath not in path.parents and
                not (MINISWMH and minipath in path.parents)):
                newpath = modpath / 'history/titles' / path.name
                # newpath.open('w').close()
                print('Should override {} with blank file'.format(
                      '<vanilla>' / path.relative_to(vanilladir)))
            else:
                check_titles(parser, path, titles)
        parser.flush(path)
    for _ in parser.parse_files('history/characters/*.txt', *source_paths):
        pass # just parse it to see if it parses
    globs = [
        'events/*.txt',
        'decisions/*.txt',
        'common/laws/*.txt',
        'common/objectives/*.txt',
        'common/minor_titles/*.txt',
        'common/job_titles/*.txt',
        'common/job_actions/*.txt',
        'common/religious_titles/*.txt',
        'common/cb_types/*.txt',
        'common/scripted_triggers/*.txt',
        'common/scripted_effects/*.txt',
        'common/achievements.txt'
        ]
    for glob in globs:
        for path in parser.files(glob, *source_paths):
            check_titles(parser, path, titles)
    with (rootpath / 'check_titles.txt').open('w', encoding='cp1252') as fp:
        if bad_region_titles:
            print('Invalid or titular titles in regions:\n\t', end='', file=fp)
            print(*bad_region_titles, sep=' ', file=fp)
        if missing_duchies:
            print('De jure duchies not found in "world_" regions:\n\t', end='',
                  file=fp)
            print(*missing_duchies, sep=' ', file=fp)
        for lhs in [True, False]:
            if results[lhs]:
                if lhs:
                    print('Undefined references as SCOPE:', file=fp)
                else:
                    print('Undefined references:', file=fp)
            for path, titles in sorted(results[lhs].items()):
                if titles:
                    if modpath in path.parents:
                        rel_path = '<mod>' / path.relative_to(modpath)
                    elif MINISWMH and minipath in path.parents:
                        rel_path = '<mod>' / path.relative_to(minipath)
                    else:
                        rel_path = '<vanilla>' / path.relative_to(vanilladir)
                    print('\t' + str(rel_path), *titles, sep='\n\t\t', file=fp)
        if misogyny:
            print('Title defines title but not title_female:\n\t', end='',
                  file=fp)
            print(*misogyny, sep=' ', file=fp)

if __name__ == '__main__':
    main()
