#!/usr/bin/env python3

import collections
import csv
import pathlib
import re
import shutil
import tempfile
from ck2parser import (rootpath, vanilladir, csv_rows, files, is_codename,
                       SimpleParser)
from print_time import print_time

modpath = rootpath / 'SWMH-BETA/SWMH'
# modpath = rootpath / 'EMF/EMF'

def abbrev_path(path):
    prefix = '<vanilla>' if vanilladir in path.parents else '<mod>'
    return prefix + '/' + path.name

def get_locs():
    locs = collections.OrderedDict()
    dupe_lines = []
    for path in files('localisation/*', modpath, reverse=True):
        vanilla = modpath not in path.parents
        for row, linenum in csv_rows(path, linenum=True):
            if row[0] in locs:
                # don't care about overriding vanilla
                if not vanilla:
                    line = ('{0!r} localisation at {1[1]!r}:{1[2]} '
                        'overrides {2!r}:{3}\n'.format(row[0],
                        locs[row[0]], abbrev_path(path), linenum))
                    dupe_lines.append(line)
            else:
                locs[row[0]] = row[1], abbrev_path(path), linenum
    locs = collections.OrderedDict((k, v[0]) for k, v in locs.items())
    return locs, dupe_lines

def scan_landed_titles(parser, cultures, loc_mod):
    dynamics = collections.defaultdict(dict)
    undef = collections.defaultdict(list)

    def recurse(tree):
        for n, v in tree:
            if is_codename(n.val):
                for n2, v2 in v:
                    if n2.val in cultures:
                        dynamics[n.val][n2.val] = v2.val
                    elif (n2.val in ['title', 'title_female', 'foa',
                                     'title_prefix'] and
                          v2.val not in loc_mod):
                        undef[v2.val].append((n.val, n2.val))
                recurse(v)

    for path, tree in parser.parse_files('common/landed_titles/*', modpath):
        print(path)
        recurse(tree)
    return dynamics, undef

@print_time
def main():
    parser = SimpleParser()
    # province_id_mod, province_title_mod = get_province_id(modpath)
    # province_id, province_title = get_province_id(vanilladir)
    # province_id.update(province_id_mod)
    # province_title.update(province_title_mod)
    cultures, cult_group = get_cultures(parser, modpath)
    mod_loc, dupe_lines = get_locs()
    vanilla_loc = get_localisation()
    # localisation = vanilla_loc.copy()
    # localisation.update(mod_loc)
    dynamics, undef = scan_landed_titles(parser, cultures, mod_loc)

    # if not outpath.exists():
    #     outpath.mkdir()

    with (rootpath / 'duplicate_locs.txt').open('w', newline='\r\n') as f:
        f.writelines(dupe_lines)

    with (rootpath / 'undefined_keys.txt').open('w', newline='\r\n') as f:
        print('undefined in mod and vanilla:', file=f)
        for loc_key, cases in sorted(undef.items()):
            if loc_key not in vanilla_loc:
                print('\t{}'.format(loc_key), file=f)
                for title, key in cases:
                    print('\t\t{} {}'.format(title, key), file=f)
        print('defined in vanilla, but not in mod:', file=f)
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
    # # static noun but no static adjective (mod static noun fallback)
    # # static adjective but no static noun (vanilla static noun fallback)
    # # static adjective but no static noun (key fallback)
    # # dynamic noun but no dynamic adjective (mod static adjective fallback)
    # # dynamic noun but no dynamic adjective (vanilla static adjective fallback)
    # # dynamic noun but no dynamic adjective (mod dynamic noun fallback)
    # # dynamic adjective but no dynamic noun (mod static noun fallback)
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

    for key in mod_loc:
        if key.endswith('_adj'):
            title = key[:-4]
            if is_codename(title):
                # static_adjs.add(title)
                if (title not in mod_loc and
                    not (title in province_id and
                         province_id[title] in mod_loc)):
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
            if is_codename(title):
                if culture not in cultures:
                    print('Undefined culture "{}"'.format(culture))
                    continue
                # dynamic_adjs.add((title, culture))
                group = cult_group[culture]
                if (culture not in dynamics[title] and
                    group not in dynamics[title]):
                    if title in mod_loc:
                        add_result(key, 'dyn. noun', mod_loc[title],
                                   'mod static noun')
                    elif (title in province_id and
                          province_id[title] in mod_loc):
                        add_result(key, 'dyn. noun',
                                   mod_loc[province_id[title]],
                                   'mod static noun')
                    elif title in vanilla_loc: 
                        add_result(key, 'dyn. noun', vanilla_loc[title],
                                   'vanilla static noun')
                    else:
                        add_result(key, 'dyn. noun', title, 'key')
        elif is_codename(key) or key in province_title:
            title = key if is_codename(key) else province_title[key]
            # if key in static_nouns:
            #     print('Multiple localisations for {} ({})'.format(
            #           key, province_id[key]))
            # static_nouns.add(title)
            adj_key = '{}_adj'.format(title)
            if adj_key not in mod_loc:
                if adj_key in vanilla_loc:
                    add_result(title, 'static adj.', vanilla_loc[adj_key],
                               'vanilla static adj.')
                else:
                    add_result(title, 'static adj.', mod_loc[key],
                               'mod static noun')
    for title, dyns in dynamics.items():
        for culture in dyns:
            # dynamic_nouns.add((title, culture))
            stat_adj_key = '{}_adj'.format(title)
            dyn_adj_key = '{}_{}'.format(stat_adj_key, culture)
            dyn_grp_adj_key = '{}_{}'.format(stat_adj_key, cult_group[culture])
            if dyn_adj_key not in mod_loc and dyn_grp_adj_key not in mod_loc:
                dyn_id = '{}_{}'.format(title, culture)
                if stat_adj_key in mod_loc:
                    add_result(dyn_id, 'dyn. adj.', mod_loc[stat_adj_key],
                               'mod static adj.')
                elif stat_adj_key in vanilla_loc: 
                    add_result(dyn_id, 'dyn. adj.', vanilla_loc[stat_adj_key],
                               'vanilla static adj.')
                else:
                    add_result(dyn_id, 'dyn. adj.', dyns[culture],
                               'mod dyn. noun')

    def missing_locs_sort_key(row):
        return ('key' not in row[3], 'adj' in row[1], 'dyn' in row[1],
                'ekdcb'.index(row[0][0]), row[0][2:])

    results_ekdc.sort(key=missing_locs_sort_key)
    # results_b.sort()
    headers = ['Existing key', 'Missing type', 'Fallback', 'Fallback source']
    # with (rootpath / 'missing_locs_baronies_1.csv').open(
    #     'w', newline='') as csvfile:
    #     writer = csv.writer(csvfile)
    #     writer.writerow(headers)
    #     writer.writerows(results_b[:len(results_b)//2])
    # with (rootpath / 'missing_locs_baronies_2.csv').open(
    #     'w', newline='') as csvfile:
    #     writer = csv.writer(csvfile)
    #     writer.writerow(headers)
    #     writer.writerows(results_b[len(results_b)//2:])
    with (rootpath / 'missing_locs_nonbaronies.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(results_ekdc)

if __name__ == '__main__':
    main()
