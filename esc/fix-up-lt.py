#!/usr/bin/env python3

import collections
import csv
import pathlib
import re
import shutil
import tempfile
import ck2parser
from ck2parser import prepend_post_comment

rootpath = ck2parser.rootpath
modpath = rootpath / 'SWMH-BETA/SWMH-Caucasus-Beta'

# templar castles referenced by vanilla events
mod_titles_to_keep = ['b_beitdejan', 'b_lafeve']

def process_province_history(where):
    def mark_barony(barony, county_set):
        try:
            if barony.val.startswith('b_'):
                county_set.add(barony.val)
        except AttributeError:
            pass

    id_name = ck2parser.province_id_name_map(where)
    province_id = {}
    used_baronies = collections.defaultdict(set)
    max_settlements = {}
    for number, title, tree in ck2parser.provinces(where):
        province_id[title] = number
        max_settlements[title] = int(tree['max_settlements'].val)
        for n, v in tree:
            mark_barony(n, used_baronies[title])
            mark_barony(v, used_baronies[title])
            if isinstance(v, ck2parser.Obj):
                if v.has_pairs:
                    for n2, v2 in v:
                        mark_barony(n2, used_baronies[title])
                        mark_barony(v2, used_baronies[title])
                else:
                    for v2 in v:
                        mark_barony(v2, used_baronies[title])
    return province_id, used_baronies, max_settlements

def main():
    lt = modpath / 'common/landed_titles'
    # province_id, used_baronies, max_settlements = process_province_history()
    # localisation = ck2parser.localisation(modpath)
    cultures = ck2parser.cultures(modpath, groups=False)
    ck2parser.fq_keys = cultures
    # historical_baronies = []

    def update_tree(tree):
        for n, v in tree:
            if ck2parser.is_codename(n.val):
                # for n2, v2 in v:
                #     if n2.val == 'capital':
                #         prov_key = 'PROV{}'.format(v2.val)
                #         capital_name = localisation[prov_key]
                #         if v2.post_comment.val.strip() == capital_name:
                #             v2.post_comment = None
                #         prepend_post_comment(v2, capital_name)
                #         # elif capital_name != v2.post_comment.val:
                #         #     print('{},{},{}'.format(v2.val,
                #         #           v2.post_comment.val, capital_name))
                #         break
                # v.ker.post_comment = None
                # _, (nl, _) = v.inline_str(0)
                # if nl >= 36:
                #     comment = 'end ' + n.val
                #     prepend_post_comment(v.ker, comment)
                # # if re.match(r'[ekd]_', n.val):
                # #     try:
                # #         prepend_post_comment(v.kel, localisation[n.val])
                # #     except KeyError:
                # #         print('@@@ ' + n.val)
                # baronies_to_remove = []
                # if n.val.startswith('c_'):
                #     # if v.kel.post_comment:
                #     #     print('c   ' + v.kel.post_comment.val)
                #     if (not v.kel.post_comment or
                #         re.search(r'\(?\d+\)?', v.kel.post_comment.val)):
                #         prev_1 = None
                #         prev_2 = None
                #         if v.kel.post_comment is not None:
                #             match = re.fullmatch(
                #                 r'([^(]+)\(\d+\)[^#]*(?:#(.+))?',
                #                 v.kel.post_comment.val)
                #             if match:
                #                 prev_1, prev_2 = match.groups()
                #             v.kel.post_comment = None
                #         try:
                #             prov_id = province_id[n.val]
                #             name = localisation['PROV{}'.format(prov_id)]
                #             comment = '{} ({})'.format(name, prov_id)
                #             if prev_1:
                #                 prev_1 = prev_1.strip()
                #                 if prev_1 != name:
                #                     prepend_post_comment(v.kel, prev_1)
                #             if prev_2:
                #                 prev_2 = prev_2.strip()
                #                 if prev_2 != name:
                #                     prepend_post_comment(v.kel, prev_2)
                #             prepend_post_comment(v.kel, comment)
                #         except KeyError:
                #             print('!!! ' + n.val)
                #     num_baronies = 0
                #     for child in v.contents:
                #         if child.key.val.startswith('b_'):
                #             if (child.key.val in historical_baronies or
                #                 child.key.val in used_baronies[n.val] or
                #                 child.key.val in mod_titles_to_keep):
                #                 num_baronies += 1
                #             else:
                #                 baronies_to_remove.append(child)
                #     if (num_baronies + len(baronies_to_remove) <
                #         max_settlements[n.val]):
                #         print(('{} has {} subholdings '
                #                'but {} max_settlements!').format(n.val,
                #                num_baronies + len(baronies_to_remove),
                #                max_settlements[n.val]))
                #     keep = max(0, max_settlements[n.val] - num_baronies)
                #     del baronies_to_remove[:keep]
                #     v.contents[:] = [v2 for v2 in v.contents
                #                       if v2 not in baronies_to_remove]
                allow_block = None
                for child in v.contents:
                    if child.key.val == 'allow':
                        allow_block = child
                        break
                if allow_block:
                    if v.contents[-1] != allow_block:
                        v.contents.remove(allow_block)
                        v.contents.append(allow_block)
                    post_barony_block = allow_block
                # else:
                #     post_barony_block = v.ker
                # for barony in reversed(baronies_to_remove):
                #     b_is, _ = barony.inline_str(0)
                #     comments = [ck2parser.Comment(s)
                #                 for s in b_is.split('\n')]
                #     post_barony_block.pre_comments[0:0] = comments
            n_lower = n.val.lower()
            if any(n_lower == s
                   for s in ('not', 'or', 'and', 'nand', 'nor')):
                n.val = n_lower
            if isinstance(v, ck2parser.Obj) and v.has_pairs:
                update_tree(v)

    # for inpath in ck2parser.files('history/titles/*.txt', modpath):
    #     if inpath.stem.startswith('b_'):
    #         historical_baronies.append(inpath.stem)

    with tempfile.TemporaryDirectory() as td:
        lt_t = pathlib.Path(td)
        for inpath, tree in ck2parser.parse_files('common/landed_titles/*',
                                                  modpath):
            outpath = lt_t / inpath.name
            tree = ck2parser.parse_file(inpath)
            # update_tree(tree)
            # with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
            #     f.write(tree.str())
        # while lt.exists():
        #     print('Removing old landed_titles...')
        #     shutil.rmtree(str(lt), ignore_errors=True)
        # shutil.copytree(str(lt_t), str(lt))

if __name__ == '__main__':
    main()
