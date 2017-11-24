#!/usr/bin/env python3

import csv
import os
import shutil
from ck2parser import (rootpath, vanilladir, is_codename, csv_rows, files,
                       SimpleParser)
from print_time import print_time

@print_time
def main():
    parser = SimpleParser()
    modpath = rootpath / 'SWMH-BETA/SWMH'
    parser.moddirs = [modpath]
    # scan all named provinces in definitions.csv for province history
    default_map = next(parser.parse_files('map/default.map'))[1]
    defs_name = default_map['definitions'].val
    # max_provinces = int(default_map['max_provinces'].val)
    prov_num_name_map = {}
    defs_path = parser.file('map/' + defs_name)
    def_rows = list(csv_rows(defs_path))
    defs_change = False
    for def_row in def_rows:
        try:
            num, name = int(def_row[0]), def_row[4]
            hist_name = '{} - {}.txt'.format(num, name)
        except (IndexError, ValueError):
            continue
        if name == '':
            continue
        try:
            hist_path = parser.file('history/provinces/' + hist_name)
        except StopIteration:
            continue
        # if it's a vanilla file, it should be copied to SWMH.
        if vanilladir in hist_path.parents:
            rel_path = hist_path.relative_to(vanilladir)
            print('Copying to ' + str(modpath / rel_path))
            shutil.copy2(str(hist_path), str(modpath / rel_path))
            hist_path = modpath / rel_path
        hist = parser.parse_file(hist_path)
        if len(hist) > 0:
            # if it isn't blank, but has no `title`, note it.
            if 'title' not in hist.dictionary:
                print('WARNING: Missing title in ' + hist_name + 
                      ', should probably be removed')
        else:
            # if it's blank,
            # it should be deleted and the province name blanked.
            print('Deleting (& blanking name of) ' + str(hist_path))
            os.remove(str(hist_path))
            def_row[6] = '#' + def_row[4]
            def_row[4] = ''
            defs_change = True
        prov_num_name_map[num] = name
    if defs_change:
        print('Writing ' + str(defs_path))
        with defs_path.open('w', encoding='cp1252', newline='') as csvfile:
            csv.writer(csvfile, dialect='ckii').writerows(def_rows)
    else:
        print('No change to definition.csv')

    # scan all province history (in mod):
    # if it doesn't match a line in definitions.csv, then it should be deleted.
    for path in files('history/provinces/*.txt', basedir=modpath):
        num, name = path.stem.split(' - ')
        num = int(num)
        if num not in prov_num_name_map or prov_num_name_map[num] != name:
            print('Deleting ' + str(path))
            os.remove(str(path))

    # clean title history
    # build list of defined titles
    titles = set()
    def recurse(tree):
        for n, v in tree:
            if is_codename(n.val):
                titles.add(n.val)
                recurse(v)
    for _, tree in parser.parse_files('common/landed_titles/*.txt'):
        recurse(tree)
    # delete all title history in mod not matching a title definition
    for path in files('history/titles/*.txt', basedir=modpath):
        title = path.stem
        if title not in titles:
            print('Deleting ' + str(path))
            os.remove(str(path))
    # then, for all visible vanilla title history,
    # if it matches a title definition copy it
    # if it doesn't, override it with a blank file
    for path in parser.files('history/titles/*.txt'):
        title = path.stem
        if vanilladir in path.parents:
            new_path = modpath / path.relative_to(vanilladir)
            if title not in titles:
                print('Writing blank ' + str(new_path))
                new_path.open('w').close()
            else:
                print('Copying to ' + str(new_path))
                shutil.copy2(str(path), str(new_path))

if __name__ == '__main__':
    main()
