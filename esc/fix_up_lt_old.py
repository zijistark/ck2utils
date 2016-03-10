#!/usr/bin/env python3

import collections
import csv
import pathlib
import re
import shutil
import ck2p as ck2parser

rootpath = pathlib.Path('C:/Users/Nicholas/Documents/CK2')
swmhpath = rootpath / 'SWMH-BETA/SWMH'

def get_cultures():
    cultures = []
    for path in ck2parser.files('common/cultures/*.txt', swmhpath):
        tree = ck2parser.parse_file(path)
        cultures.extend(n2.val for _, v in tree for n2, v2 in v
                        if n2.val != 'graphical_cultures')
    return cultures

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
    for path in ck2parser.files('history/provinces/*.txt', where):
        number, name = path.stem.split(' - ')
        number = int(number)
        if id_name[number] == name:
            tree = ck2parser.parse_file(path)
            try:
                title = next(v.val for n, v in tree if n.val == 'title')
            except StopIteration:
                continue
            province_id[title] = number
    return province_id

def prepend_post_comment(item, s):
    if item.post_comment:
        s += ' ' + str(item.post_comment)
    item.post_comment = ck2parser.Comment(s)

kingdoms_for_barony_swap = [
    'k_bulgaria', 'k_serbia', 'k_bosnia', 'k_croatia', 'k_hungary',
    'k_denmark', 'k_norway', 'k_finland', 'k_pomerania', 'k_terra',
    'k_lithuania', 'k_taurica', 'k_khazaria' 'k_alania', 'k_volga_bulgaria',
    'k_bjarmia', 'k_perm']

def main():
    build = swmhpath / 'build'
    build_lt = build / 'common/landed_titles'
    while build.exists():
        print('Removing old build...')
        shutil.rmtree(str(build), ignore_errors=True)
    build_lt.mkdir(parents=True)

    province_id = get_province_id(swmhpath)
    localisation = ck2parser.localisation(swmhpath)
    cultures = get_cultures()
    ck2parser.fq_keys = cultures

    def update_tree(v, swap_baronies=False):
        for n2, v2 in v:
            if isinstance(n2, ck2parser.String):
                if ck2parser.is_codename(n2.val):
                    for n3, v3 in v2:
                        if n3.val == 'capital':
                            prov_key = 'PROV{}'.format(v3.val)
                            capital_name = localisation[prov_key]
                            if not v3.post_comment:
                                v3.post_comment = ck2parser.Comment(
                                    capital_name)
                            break
                    _, (nl, _) = v2.inline_str(0)
                    if nl >= 36:
                        comment = 'end ' + n2.val
                        v2.ker.post_comment = None
                        prepend_post_comment(v2.ker, comment)
                    if re.match(r'[ekd]_', n2.val):
                        if n2.val.startswith('k_'):
                            swap_baronies = n2.val in kingdoms_for_barony_swap
                        try:
                            prepend_post_comment(v2.kel, localisation[n2.val])
                        except KeyError:
                            print('@@@ ' + n2.val)
                    elif n2.val.startswith('c_'):
                        # if v2.kel.post_comment:
                        #     print('c   ' + v2.kel.post_comment.val)
                        if (v2.kel.post_comment and
                            v2.kel.post_comment.val.isdigit()):
                            v2.kel.post_comment = None
                        try:
                            prov_id = province_id[n2.val]
                            comment = '{} ({})'.format(
                                localisation['PROV{}'.format(prov_id)],
                                prov_id)
                            prepend_post_comment(v2.kel, comment)
                        except KeyError:
                            print('!!! ' + n2.val)
                        if swap_baronies:
                            baronies = []
                            for child in reversed(v2.contents):
                                if child.key.val.startswith('b_'):
                                    baronies.append(child)
                                    v2.contents.remove(child)
                            v2.contents.extend(baronies)
                    allow_block = None
                    for child in v2.contents:
                        if child.key.val == 'allow':
                            allow_block = child
                            break
                    if allow_block:
                        v2.contents.remove(allow_block)
                        v2.contents.append(allow_block)
                n2_lower = n2.val.lower()
                if any(n2_lower == s
                       for s in ['not', 'or', 'and', 'nand', 'nor']):
                    n2.val = n2_lower
            if isinstance(v2, ck2parser.Obj) and v2.has_pairs:
                update_tree(v2, swap_baronies)

    for inpath in ck2parser.files('common/landed_titles/*.txt', swmhpath):
        outpath = build_lt / inpath.name
        tree = ck2parser.parse_file(inpath)
        update_tree(tree)
        with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
            f.write(tree.str())

if __name__ == '__main__':
    main()
