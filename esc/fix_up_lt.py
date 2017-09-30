#!/usr/bin/env python3

import collections
import csv
import pathlib
import re
import shutil
import tempfile
import time
from ck2parser import (rootpath, is_codename, get_province_id_name_map,
                       get_provinces, get_localisation, get_cultures,
                       files, prepend_post_comment, Obj, Comment, SimpleParser,
                       FullParser)
from print_time import print_time

PRUNE_BARONIES = False
FORMAT_ONLY = False # don't alter code, just format. overrides PRUNE_BARONIES

# templar castles referenced by vanilla events
mod_titles_to_keep = ['b_beitdejan', 'b_lafeve']

def process_province_history(parser):
    def mark_barony(barony, county_set):
        try:
            if barony.val.startswith('b_'):
                county_set.add(barony.val)
        except AttributeError:
            pass

    id_name = get_province_id_name_map(parser)
    province_id = {}
    used_baronies = collections.defaultdict(set)
    max_settlements = {}
    for number, title, tree in get_provinces(parser):
        province_id[title] = number
        max_settlements[title] = int(tree['max_settlements'].val)
        for n, v in tree:
            mark_barony(n, used_baronies[title])
            mark_barony(v, used_baronies[title])
            if isinstance(v, Obj):
                if v.has_pairs:
                    for n2, v2 in v:
                        mark_barony(n2, used_baronies[title])
                        mark_barony(v2, used_baronies[title])
                else:
                    for v2 in v:
                        mark_barony(v2, used_baronies[title])
    return province_id, used_baronies, max_settlements

@print_time
def main():
    simple_parser = SimpleParser()
    full_parser = FullParser()
    modpath = rootpath / 'SWMH-BETA/SWMH'
    simple_parser.moddirs = [modpath]
    full_parser.moddirs = [modpath]
    lt = modpath / 'common/landed_titles'
    province_id, used_baronies, max_settlements = process_province_history(
        simple_parser)
    localisation = get_localisation(simple_parser.moddirs)
    cultures = get_cultures(simple_parser, groups=False)
    full_parser.fq_keys = cultures
    historical_baronies = []

    def update_tree(tree, is_def=True):
        for n, v in tree:
            if is_codename(n.val) and is_def and not FORMAT_ONLY:
                try:
                    cap = v['capital']
                    prov_key = 'PROV{}'.format(cap.val)
                    capital_name = localisation[prov_key]
                    prepend_post_comment(cap, capital_name)
                    # if '#' in cap.post_comment.val:
                        # if not any(is_codename(n2.val) for n2, _ in v):
                            # prepend_post_comment(cap, 'XXX')
                            # print('??? ' + n.val)
                        # elif cap.post_comment.val.count('#') > 1:
                            # prepend_post_comment(cap, 'XXX')
                            # print('*** ' + n.val)
                    # elif capital_name != cap.post_comment.val:
                    #     print('{},{},{}'.format(cap.val,
                    #           cap.post_comment.val, capital_name))
                except KeyError:
                    pass
                if v.inline_str(full_parser)[1][0] > 1: # only for multi-line
                    v.post_comment = None
                    _, (nl, _) = v.inline_str(full_parser)
                    if nl >= 36:
                        comment = 'end ' + n.val
                        prepend_post_comment(v, comment)
                    if re.match(r'[ekd]_', n.val):
                        try:
                            prepend_post_comment(v.kel, localisation[n.val])
                        except KeyError:
                            print('@@@ ' + n.val)
                baronies_to_remove = []
                if n.val.startswith('c_'):
                    # if v.kel.post_comment:
                    #     print('c   ' + v.kel.post_comment.val)
                    if (not v.kel.post_comment or
                        re.search(r'\(?\d+\)?', v.kel.post_comment.val)):
                        prev_1 = None
                        prev_2 = None
                        if v.kel.post_comment is not None:
                            match = re.fullmatch(
                                r'([^(]+)\(\d+\)[^#]*(?:#(.+))?',
                                v.kel.post_comment.val)
                            if match:
                                prev_1, prev_2 = match.groups()
                            v.kel.post_comment = None
                        try:
                            prov_id = province_id[n.val]
                            name = localisation['PROV{}'.format(prov_id)]
                            comment = '{} ({})'.format(name, prov_id)
                            if prev_1:
                                prev_1 = prev_1.strip()
                                if prev_1 != name:
                                    prepend_post_comment(v.kel, prev_1)
                            if prev_2:
                                prev_2 = prev_2.strip()
                                if prev_2 != name:
                                    prepend_post_comment(v.kel, prev_2)
                            prepend_post_comment(v.kel, comment)
                        except KeyError:
                            print('!!! ' + n.val)
                    if PRUNE_BARONIES:
                        num_baronies = 0
                        for child in v.contents:
                            if child.key.val.startswith('b_'):
                                if (child.key.val in historical_baronies or
                                    child.key.val in used_baronies[n.val] or
                                    child.key.val in mod_titles_to_keep):
                                    num_baronies += 1
                                else:
                                    baronies_to_remove.append(child)
                        if (num_baronies + len(baronies_to_remove) <
                            max_settlements[n.val]):
                            # print(num_baronies, baronies_to_remove,
                            #       len(v.contents))
                            print(('{} has {} subholdings '
                                   'but {} max_settlements!').format(n.val,
                                   num_baronies + len(baronies_to_remove),
                                   max_settlements[n.val]))
                        keep = max(0, max_settlements[n.val] - num_baronies)
                        del baronies_to_remove[:keep]
                        v.contents[:] = [v2 for v2 in v.contents
                                         if v2 not in baronies_to_remove]
                allow_pair = None
                for child in v.contents:
                    if child.key.val == 'allow':
                        allow_pair = child
                        break
                if allow_pair:
                    if v.contents[-1] != allow_pair:
                        v.contents.remove(allow_pair)
                        v.contents.append(allow_pair)
                    post_barony_pair = allow_pair
                else:
                    post_barony_pair = v.ker
                if PRUNE_BARONIES:
                    for barony in reversed(baronies_to_remove):
                        b_is, _ = barony.inline_str(full_parser)
                        comments = [Comment(s) for s in b_is.split('\n')]
                        post_barony_pair.pre_comments[:0] = comments
                is_def_children = True
            else:
                is_def_children = False
            try:
                n_upper = n.val.upper()
                if any(n_upper == s
                       for s in ('NOT', 'OR', 'AND', 'NAND', 'NOR')):
                    n.val = n_upper
            except AttributeError:
                pass
            if isinstance(v, Obj) and v.has_pairs:
                update_tree(v, is_def_children)

    for inpath in full_parser.files('history/titles/*.txt'):
        if inpath.stem.startswith('b_'):
            historical_baronies.append(inpath.stem)

    with tempfile.TemporaryDirectory() as td:
        lt_t = pathlib.Path(td)
        for inpath, tree in full_parser.parse_files('common/landed_titles/*'):
            outpath = lt_t / inpath.name
            update_tree(tree)
            with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
                f.write(tree.str(full_parser))
        while lt.exists():
            print('Removing old landed_titles...')
            shutil.rmtree(str(lt), ignore_errors=True)
        shutil.copytree(str(lt_t), str(lt))

if __name__ == '__main__':
    main()
