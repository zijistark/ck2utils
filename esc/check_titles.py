#!/usr/bin/env python3

import collections
import csv
import pathlib
import re
import shutil
import tempfile
import localpaths
import ck2parser

rootpath = localpaths.rootpath
vanilladir = localpaths.vanilladir
swmhpath = rootpath / 'SWMH-BETA/SWMH'

results = collections.defaultdict(list)

def check_title(v, path, titles):
    if not isinstance(v, str):
        v = v.val
    if ck2parser.is_codename(v) and v not in titles:
        results[path].append(v)
        return False
    return True

def check_titles(path, titles):
    def recurse(tree):
        if tree.has_pairs:
            try:
                for n, v in tree:
                    check_title(n, path, titles)
                    try:
                        check_title(v, path, titles)
                    except AttributeError:
                        recurse(v)
            except TypeError:
                for x in tree:
                    if isinstance(x, ck2parser.String):
                        print(x.val)
                raise
        else:
            for v in tree:
                check_title(v, path, titles)

    try:
        recurse(ck2parser.parse_file(path))
    except:
        print(path)
        raise

def check_province_history(titles):
    tree = ck2parser.parse_file(swmhpath / 'map/default.map')
    defs = next(v.val for n, v in tree if n.val == 'definitions')
    id_name = {}
    with (swmhpath / 'map' / defs).open(newline='',
                                        encoding='cp1252') as csvfile:
        for row in csv.reader(csvfile, dialect='ckii'):
            try:
                id_name[int(row[0])] = row[4]
            except (IndexError, ValueError):
                continue
    for path in ck2parser.files('history/provinces/*.txt', swmhpath):
        number, name = path.stem.split(' - ')
        id_number = int(number)
        if id_name[id_number] == name:
            check_titles(path, titles)

def process_landed_titles():
    titles = set()

    def recurse(tree):
        for n, v in tree:
            if ck2parser.is_codename(n.val):
                if n.val in titles:
                    print('Duplicate title {}'.format(n.val))
                titles.add(n.val)
                recurse(v)

    for path in ck2parser.files('common/landed_titles/*.txt', swmhpath):
        recurse(ck2parser.parse_file(path))
    return titles

def main():
    titles = process_landed_titles()
    check_province_history(titles)
    for path in ck2parser.files('history/titles/*.txt', swmhpath):
        tree = ck2parser.parse_file(path)
        if tree.contents:
            good = check_title(path.stem, path.parent, titles)
            if not good and swmhpath not in path.parents:
                newpath = swmhpath / 'history/titles' / path.name
                newpath.open('w').close()
            else:
                check_titles(path, titles)
    globs = [
        'events/*.txt', 'common/decisions/*.txt', 'common/minor_titles/*.txt',
        'common/achievements.txt', 'common/laws/*.txt'
        ]
    for glob in globs:
        for path in ck2parser.files(glob, swmhpath):
            check_titles(path, titles)
    with (rootpath / 'out.txt').open('w', encoding='cp1252') as fp:
        for path, titles in sorted(results.items()):
            if titles:
                if swmhpath in path.parents:
                    rel_path = '<swmh>' / path.relative_to(swmhpath)
                else:
                    rel_path = '<vanilla>' / path.relative_to(vanilladir)
                print(rel_path, *titles, sep='\n\t', file=fp)


if __name__ == '__main__':
    main()
