#!/usr/bin/env python3

'''
Scans for:
* unlocalised non-county titles
* localisation keys with unrecognized titles
* localisation keys with unrecognized cultures
'''

import re
import ck2parser
import localpaths

rootpath = localpaths.rootpath
modpath = rootpath / 'CK2Plus/CK2Plus'

def recurse_comments(comments):
    if comments:
        try:
            tree = ck2parser.parse('\n'.join(c.val for c in comments))
            yield from recurse(tree, comment=True)
        except ck2parser.parser.NoParseError:
            pass

def recurse(tree, comment=False):
    try:
        for n, v in tree:
            yield from recurse_comments(n.pre_comments)
            if ck2parser.is_codename(n.val):
                yield n.val, not comment
                yield from recurse(v)
    except ValueError:
        pass
    try:
        yield from recurse_comments(tree.ker.pre_comments)
    except AttributeError:
        try:
            yield from recurse_comments(tree.post_comments)
        except AttributeError:
            pass

def main():
    cultures, cult_groups = ck2parser.cultures(modpath)
    cultures = set(cultures).update(cult_groups)
    defined_titles = []
    commented_out_titles = []
    for _, tree in ck2parser.parse_files('common/landed_titles/*', modpath):
        for title, defined in recurse(tree):
            (defined_titles if defined else commented_out_titles).append(title)
    titles = set(defined_titles) | set(commented_out_titles)
    localisation = ck2parser.localisation(modpath)
    unlocalised_noncounty_titles = [
        t for t in defined_titles
        if not t.startswith('c') and t not in localisation and t != 'e_null']
    unrecognized_nonbarony_keys = []
    unrecognized_barony_keys = []
    unrecognized_culture_keys = []
    for path in ck2parser.files('localisation/*.csv', basedir=modpath):
        for key, *_ in ck2parser.csv_rows(path):
            match = re.match(r'[ekdcb]_((?!_adj).)*', key)
            if match:
                if match.group() not in titles:
                    if key.startswith('b'):
                        unrecognized_barony_keys.append(key)
                    else:
                        unrecognized_nonbarony_keys.append(key)
                match = re.search(r'_adj_(.*)', key)
                if match:
                    if match.group(1) not in cultures:
                        unrecognized_culture_keys.append(key)
    with (rootpath / 'loc-check-2.txt').open('w') as f:
        if unlocalised_noncounty_titles:
            print('Unlocalised non-county titles:',
                  *unlocalised_noncounty_titles, sep='\n\t', file=f)
        if unrecognized_nonbarony_keys:
            print('Localisation keys with unrecognized non-barony titles:',
                  *unrecognized_nonbarony_keys, sep='\n\t', file=f)
        if unrecognized_barony_keys:
            print('Localisation keys with unrecognized barony titles:',
                  *unrecognized_barony_keys, sep='\n\t', file=f)
        if unrecognized_culture_keys:
            print('Localisation keys with unrecognized cultures:',
                  *unrecognized_culture_keys, sep='\n\t', file=f)

if __name__ == '__main__':
    main()
