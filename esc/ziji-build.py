#!/usr/bin/env python3

import csv
import re
import sys
import ck2parser
import localpaths

def get_province_id(where):
    tree = ck2parser.parse_file(where / 'map/default.map')
    defs = next(v.val for n, v in tree if n.val == 'definitions')
    id_name = {}
    for row in ck2parser.csv_rows(where / 'map' / defs):
        try:
            id_name[int(row[0])] = row[4]
        except (IndexError, ValueError):
            continue
    province_id = {}
    province_title = {}
    for path in ck2parser.files('history/provinces/*.txt', where):
        number, name = path.stem.split(' - ')
        if id_name[int(number)] == name:
            tree = ck2parser.parse_file(path)
            try:
                title = next(v.val for n, v in tree if n.val == 'title')
            except StopIteration:
                continue
            the_id = 'PROV' + number
            province_title[the_id] = title
    return province_title

def get_cultures(where):
    cultures = []
    for _, tree in ck2parser.parse_files('common/cultures/*.txt', where):
        cultures.extend(n2.val for _, v in tree for n2, v in v
                        if n2.val != 'graphical_cultures')
    return cultures

def main():
    modpath = localpaths.rootpath / 'SWMH-BETA/SWMH'
    if len(sys.argv) > 1:
        modpath = pathlib.Path(sys.argv[1])
    build = modpath
    if len(sys.argv) > 2:
        build = pathlib.Path(sys.argv[2])
    build_loc = build / 'localisation'
    build_lt = build / 'common/landed_titles'
    build_loc.mkdir(parents=True)
    build_lt.mkdir(parents=True)

    prov_title = get_province_id(modpath)
    cultures = get_cultures(modpath)
    ck2parser.fq_keys = cultures
    lt_keys_to_remove = [
        'title', 'title_female', 'foa', 'title_prefix', 'short_name',
        'name_tier', 'location_ruler_title', 'dynasty_title_names'] + cultures
    titles = set()

    def update_tree(tree, mutate=True):
        for n, v in tree:
            if ck2parser.is_codename(n.val):
                titles.add(n.val)
                if mutate:
                    for p2 in reversed(v.contents):
                        if p2.key.val in lt_keys_to_remove:
                            v.contents.remove(p2)
                update_tree(v)

    # process landed_titles
    mod_lt_files = set()
    for inpath, tree in ck2parser.parse_files('common/landed_titles/*.txt',
                                              basedir=modpath):
        mod_lt_files.add(inpath.name)
        outpath = build_lt / inpath.name
        update_tree(tree)
        with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
            f.write(tree.str())
    for inpath, tree in ck2parser.parse_files('common/landed_titles/*.txt'):
        if inpath not in mod_lt_files:
            update_tree(tree, mutate=False)

    def check_key(key, vanilla=False):
        title_match = re.match(r'[ekdcb]_((?!_adj($|_)).)*', key)
        if title_match is not None:
            title = title_match.group()
            if title not in titles:
                return None
            if re.fullmatch(r'c_((?!_adj($|_)).)*', key) is not None:
                return None
        else:
            prov_match = re.match(r'PROV\d+', key)
            if prov_match is not None:
                try:
                    title = prov_title[prov_match.group()]
                except KeyError:
                    return None
                if title not in titles:
                    return None
            else:
                #TODO
                noble_match = re.match(r'TODO', key):
                if noble_match is not None:
                    pass
                else:
                    return None
        outrow = [''] * 15
        outrow[0] = key
        outrow[-1] = 'x'
        return outrow

    # process localisation
    outrows = [[''] * 15]
    outrows[0][:6] = ['#CODE', 'ENGLISH', 'FRENCH', 'GERMAN', '', 'SPANISH']
    outrows[0][-1] = 'x'

    mod_files = set()
    keys_seen = set()
    for path in files('localisation/*', basedir=modpath):
        mod_files.add(path.name)
        for row in csv_rows(path):
            if len(row) >= 2 and row[0] not in keys_seen:
                keys_seen.add(row[0])
                outrow = check_key(key, vanilla=False):
                if outrow:
                    outrows.append(outrow)
    for path in files('localisation/*'):
        if path.name not in mod_files:
            for row in csv_rows(path):
                if len(row) >= 2 and row[0] not in keys_seen:
                    keys_seen.add(row[0])
                    outrow = check_key(key, vanilla=True):
                    if outrow:
                        outrows.append(outrow)

    outpath = build_loc / 'A AAA testing override.csv'
    with outpath.open('w', encoding='cp1252', newline='') as csvfile:
        csv.writer(csvfile, dialect='ckii').writerows(outrows)

if __name__ == '__main__':
    main()
