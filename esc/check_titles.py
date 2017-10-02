#!/usr/bin/env python3

from collections import defaultdict
import csv
from operator import attrgetter
import pathlib
import pprint
import re
import sys
import shutil
import tempfile
import ck2parser
from ck2parser import (rootpath, vanilladir, is_codename, Obj, csv_rows,
                       get_province_id_name_map, SimpleParser)
from print_time import print_time

VANILLA_HISTORY_WARN = True

results = {True: defaultdict(list),
           False: defaultdict(list)}

def check_title(parser, v, path, titles, lhs=False, line=None):
    if isinstance(v, str):
        v_str = v
    else:
        v_str = v.val
    if is_codename(v_str) and v_str not in titles:
        if line is None:
            line = '<file>'
        else:
            v_lines = line.inline_str(parser)[0].splitlines()
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
                check_title(parser, n, path, titles, v_is_obj, p)
                if v_is_obj:
                    recurse(v)
                else:
                    check_title(parser, v, path, titles, line=p)
        else:
            for v in tree:
                check_title(parser, v, path, titles, line=v)

    try:
        recurse(parser.parse_file(path))
    except:
        print(path)
        raise

def check_regions(parser, titles, duchies_de_jure):
    bad_titles = []
    missing_duchies = list(duchies_de_jure)
    region_duchies = defaultdict(list)
    path, tree = next(parser.parse_files('map/geographical_region.txt'))
    for n, v in tree:
        world = n.val.startswith('world_')
        for n2, v2 in v:
            if n2.val == 'regions':
                for v3 in v2:
                    for duchy in region_duchies.get(v3.val, []):
                        try:
                            missing_duchies.remove(duchy)
                        except ValueError:
                            pass
                        region_duchies[n.val].append(duchy)
            elif n2.val == 'duchies':
                for v3 in v2:
                    if is_codename(v3.val):
                        check_title(parser, v3, path, titles, line=v3)
                        region_duchies[n.val].append(v3.val)
                        if v3.val in titles and v3.val not in duchies_de_jure:
                            bad_titles.append(v3.val)
                        elif world and v3.val in missing_duchies:
                            missing_duchies.remove(v3.val)

    return bad_titles, missing_duchies

def check_province_history(parser, titles):
    id_name_map = get_province_id_name_map(parser)
    for path in parser.files('history/provinces/*.txt'):
        number, name = path.stem.split(' - ')
        if id_name_map.get(int(number)) == name:
            check_titles(parser, path, titles)

def process_landed_titles(parser):
    titles_list = []
    title_liege_map = {}
    title_vassals_map = defaultdict(set)
    misogyny = []
    for path, tree in parser.parse_files('common/landed_titles/*.txt'):
        try:
            dfs = list(reversed(tree))
            while dfs:
                n, v = dfs.pop()
                if is_codename(n.val):
                    if n.val not in titles_list:
                        titles_list.append(n.val)
                    if v.get('title') and not v.get('title_female'):
                        misogyny.append(n.val)
                    for n2, v2 in v:
                        if is_codename(n2.val):
                            title_liege_map[n2.val] = n.val
                            title_vassals_map[n.val].add(n2.val)
                    dfs.extend(reversed(v))
        except:
            print(path)
            raise
    return titles_list, title_liege_map, title_vassals_map, misogyny

@print_time
def main():
    # import pdb
    parser = SimpleParser()
    parser.moddirs = [rootpath / 'SWMH-BETA/SWMH']
    titles_list, title_liege_map, title_vassals_map, misogyny = (
        process_landed_titles(parser))
    titles = set(titles_list)
    check_province_history(parser, titles)
    start_date = parser.parse_file('common/defines.txt')['start_date'].val
    for path, tree in parser.parse_files('history/titles/*.txt',
                                         memcache=True):
        if tree.contents:
            title = path.stem
            good = check_title(parser, title, path, titles)
            if (VANILLA_HISTORY_WARN and not good and
                not any(d in path.parents for d in parser.moddirs)):
                # newpath = parser.moddirs[0] / 'history/titles' / path.name
                # newpath.open('w').close()
                print('Should override {} with blank file'.format(
                      '<vanilla>' / path.relative_to(vanilladir)))
            else:
                check_titles(parser, path, titles)
            # update de jure changed before start_date
            for n, v in sorted(tree, key=attrgetter('key.val')):
                if n.val > start_date:
                    break
                for n2, v2 in v:
                    if n2.val == 'de_jure_liege':
                        old_liege = title_liege_map.get(title)
                        if old_liege:
                            title_vassals_map[old_liege].discard(title)
                        title_liege_map[title] = v2.val
                        title_vassals_map[v2.val].add(title)
        parser.flush(path)
    duchies_de_jure = [t for t, v in title_vassals_map.items()
                       if t[0] == 'd' and v]
    bad_region_titles, missing_duchies = check_regions(parser, titles,
                                                       duchies_de_jure)
    for _ in parser.parse_files('history/characters/*.txt'):
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
        for path in parser.files(glob):
            check_titles(parser, path, titles)
    with (rootpath / 'check_titles.txt').open('w') as fp:
        if bad_region_titles:
            print('Titular titles in regions:\n\t', end='', file=fp)
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
                    for modpath in parser.moddirs:
                        if modpath in path.parents:
                            rel_path = '<mod>' / path.relative_to(modpath)
                            break
                    else:
                        rel_path = '<vanilla>' / path.relative_to(vanilladir)
                    print('\t' + str(rel_path), *titles, sep='\n\t\t', file=fp)
        if misogyny:
            print('Title defines title but not title_female:\n\t', end='',
                  file=fp)
            print(*misogyny, sep=' ', file=fp)

if __name__ == '__main__':
    main()
