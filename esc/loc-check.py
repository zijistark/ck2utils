#!/usr/bin/env python3

import collections
import csv
import pathlib
import re
import shutil
import tempfile
import ck2parser
import localpaths

rootpath = localpaths.rootpath
vanillapath = localpaths.vanilladir
swmhpath = rootpath / 'SWMH-BETA/SWMH'
outpath = rootpath / 'SWMH-BETA/metadata'

def valid_codename(string):
    try:
        return re.match(r'[ekdcb]_', string)
    except TypeError:
        return False

def get_locs(where, dupe_check=False):
    locs = collections.OrderedDict()
    dupe_lines = []
    for path in ck2parser.files('localisation/*.csv', basedir=where):
        with path.open(newline='', encoding='cp1252',
                       errors='replace') as csvfile:
            reader = csv.reader(csvfile, dialect='ckii')
            for row in reader:
                if row and row[0] and '#' not in row[0]:
                    if dupe_check:
                        if row[0] in locs:
                            line = ('{0!r} localisation at {1!r}:{2} '
                                'overrides {3[1]!r}:{3[2]}\n'.format(row[0],
                                path.name, reader.line_num, locs[row[0]]))
                            dupe_lines.append(line)
                        locs[row[0]] = row[1], path.name, reader.line_num
                    else:
                        locs[row[0]] = row[1]
    if dupe_check:
        locs = collections.OrderedDict((k, v[0]) for k, v in locs.items())
        return locs, dupe_lines
    return locs

def get_province_id(where):
    tree = ck2parser.parse_file(where / 'map/default.map')
    defs = next(v.val for n, v in tree if n.val == 'definitions')
    id_name = {}
    with (where / 'map' / defs).open(newline='', encoding='cp1252') as csvfile:
        for row in csv.reader(csvfile, dialect='ckii'):
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
            prov_id = 'PROV' + number
            province_id[title] = prov_id
            province_title[prov_id] = title
    return province_id, province_title

def get_cultures(where):
    cultures = []
    cult_group = {}
    for path in ck2parser.files('common/cultures/*.txt', where):
        tree = ck2parser.parse_file(path)
        for n, v in tree:
            cultures.append(n.val)
            cult_group[n.val] = n.val
            for n2, v2 in v:
                if n2.val != 'graphical_cultures':
                    cultures.append(n2.val)
                    cult_group[n2.val] = n.val
    return cultures, cult_group

def scan_landed_titles(where, cultures, loc_swmh):
    dynamics = collections.defaultdict(dict)
    undef = collections.defaultdict(list)

    def recurse(v):
        for n1, v1 in v:
            if not valid_codename(n1.val):
                continue
            for n2, v2 in v1:
                if n2.val in cultures:
                    dynamics[n1.val][n2.val] = v2.val
                elif (n2.val in ['title', 'title_female', 'foa',
                                 'title_prefix'] and v2.val not in loc_swmh):
                    undef[v2.val].append((n1.val, n2.val))
            recurse(v1)

    for path in ck2parser.files('common/landed_titles/*.txt', where):
        print(path)
        recurse(ck2parser.parse_file(path))
    return dynamics, undef

def main():
    province_id_swmh, province_title_swmh = get_province_id(swmhpath)
    province_id, province_title = get_province_id(vanillapath)
    province_id.update(province_id_swmh)
    province_title.update(province_title_swmh)
    cultures, cult_group = get_cultures(swmhpath)
    swmh_loc, dupe_lines = get_locs(swmhpath, dupe_check=True)
    vanilla_loc = get_locs(vanillapath)
    # localisation = vanilla_loc.copy()
    # localisation.update(swmh_loc)
    dynamics, undef = scan_landed_titles(swmhpath, cultures, swmh_loc)

    if not outpath.exists():
        outpath.mkdir()

    with (outpath / 'duplicate_locs.txt').open('w', newline='\r\n') as f:
        f.writelines(dupe_lines)

    with (outpath / 'undefined_keys.txt').open('w', newline='\r\n') as f:
        print('undefined in SWMH and vanilla:', file=f)
        for loc_key, cases in sorted(undef.items()):
            if loc_key not in vanilla_loc:
                print('\t{}'.format(loc_key), file=f)
                for title, key in cases:
                    print('\t\t{} {}'.format(title, key), file=f)
        print('defined in vanilla, but not in SWMH:', file=f)
        for loc_key, cases in sorted(undef.items()):
            if loc_key in vanilla_loc:
                print('\t{} (vanilla: "{}")'
                      .format(loc_key, vanilla_loc[loc_key]), file=f)
                for title, key in cases:
                    print('\t\t{} {}'.format(title, key), file=f)

    raise SystemExit()

    # static_nouns = set()
    # static_adjs = set()
    # dynamic_nouns = set()
    # dynamic_adjs = set()
    results_ekdc = []
    results_b = []

    # look for:
    # # static noun but no static adjective (vanilla static adjective fallback)
    # # static noun but no static adjective (swmh static noun fallback)
    # # static adjective but no static noun (vanilla static noun fallback)
    # # static adjective but no static noun (key fallback)
    # # dynamic noun but no dynamic adjective (swmh static adjective fallback)
    # # dynamic noun but no dynamic adjective (vanilla static adjective fallback)
    # # dynamic noun but no dynamic adjective (swmh dynamic noun fallback)
    # # dynamic adjective but no dynamic noun (swmh static noun fallback)
    # # dynamic adjective but no dynamic noun (vanilla static noun fallback)
    # # dynamic adjective but no dynamic noun (key fallback)

    # remember: missing dynamic adjective falls back to static adjective
    #               if there is one, otherwise dynamic noun
    #           missing dynamic noun falls back to static noun
    #           missing static adjective falls back to static noun
    #           missing static noun falls back to key

    def add_result(*x):
        if x[0].startswith('b_'):
            results_b.append(x)
        else:
            results_ekdc.append(x)

    for key in swmh_loc:
        if key.endswith('_adj'):
            title = key[:-4]
            if valid_codename(title):
                # static_adjs.add(title)
                if (title not in swmh_loc and
                    not (title in province_id and
                         province_id[title] in swmh_loc)):
                    if title in vanilla_loc:
                        add_result(key, 'static noun', vanilla_loc[title],
                                   'vanilla static noun')
                    elif (title in province_id and
                          province_id[title] in vanilla_loc):
                        add_result(key, 'static noun',
                                   vanilla_loc[province_id[title]],
                                   'vanilla static noun')
                    else:
                        add_result(key, 'static noun', title, 'key')
        elif '_adj_' in key:
            title, culture = key.split('_adj_', maxsplit=1)
            if valid_codename(title):
                if culture not in cultures:
                    print('Undefined culture "{}"'.format(culture))
                    continue
                # dynamic_adjs.add((title, culture))
                group = cult_group[culture]
                if (culture not in dynamics[title] and
                    group not in dynamics[title]):
                    if title in swmh_loc:
                        add_result(key, 'dyn. noun', swmh_loc[title],
                                   'SWMH static noun')
                    elif (title in province_id and
                          province_id[title] in swmh_loc):
                        add_result(key, 'dyn. noun',
                                   swmh_loc[province_id[title]],
                                   'SWMH static noun')
                    elif title in vanilla_loc: 
                        add_result(key, 'dyn. noun', vanilla_loc[title],
                                   'vanilla static noun')
                    else:
                        add_result(key, 'dyn. noun', title, 'key')
        elif valid_codename(key) or key in province_title:
            title = key if valid_codename(key) else province_title[key]
            # if key in static_nouns:
            #     print('Multiple localisations for {} ({})'.format(
            #           key, province_id[key]))
            # static_nouns.add(title)
            adj_key = '{}_adj'.format(title)
            if adj_key not in swmh_loc:
                if adj_key in vanilla_loc:
                    add_result(title, 'static adj.', vanilla_loc[adj_key],
                               'vanilla static adj.')
                else:
                    add_result(title, 'static adj.', swmh_loc[key],
                               'SWMH static noun')
    for title, dyns in dynamics.items():
        for culture in dyns:
            # dynamic_nouns.add((title, culture))
            stat_adj_key = '{}_adj'.format(title)
            dyn_adj_key = '{}_{}'.format(stat_adj_key, culture)
            dyn_grp_adj_key = '{}_{}'.format(stat_adj_key, cult_group[culture])
            if dyn_adj_key not in swmh_loc and dyn_grp_adj_key not in swmh_loc:
                dyn_id = '{}_{}'.format(title, culture)
                if stat_adj_key in swmh_loc:
                    add_result(dyn_id, 'dyn. adj.', swmh_loc[stat_adj_key],
                               'SWMH static adj.')
                elif stat_adj_key in vanilla_loc: 
                    add_result(dyn_id, 'dyn. adj.', vanilla_loc[stat_adj_key],
                               'vanilla static adj.')
                else:
                    add_result(dyn_id, 'dyn. adj.', dyns[culture],
                               'SWMH dyn. noun')

    def missing_locs_sort_key(row):
        return ('key' not in row[3], 'adj' in row[1], 'dyn' in row[1],
                'ekdcb'.index(row[0][0]), row[0][2:])

    results_ekdc.sort(key=missing_locs_sort_key)
    # results_b.sort()
    headers = ['Existing key', 'Missing type', 'Fallback', 'Fallback source']
    # with (outpath / 'missing_locs_baronies_1.csv').open(
    #     'w', newline='') as csvfile:
    #     writer = csv.writer(csvfile)
    #     writer.writerow(headers)
    #     writer.writerows(results_b[:len(results_b)//2])
    # with (outpath / 'missing_locs_baronies_2.csv').open(
    #     'w', newline='') as csvfile:
    #     writer = csv.writer(csvfile)
    #     writer.writerow(headers)
    #     writer.writerows(results_b[len(results_b)//2:])
    with (outpath / 'missing_locs_nonbaronies.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(results_ekdc)

if __name__ == '__main__':
    main()
