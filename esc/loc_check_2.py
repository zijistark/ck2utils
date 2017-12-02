#!/usr/bin/env python3

'''
Scans for:
* unlocalised non-county titles
* localisation keys with unrecognized titles
* localisation keys with unrecognized cultures
'''

import pathlib
import re
from ck2parser import (rootpath, files, csv_rows, get_cultures, is_codename,
                       get_localisation, SimpleParser, FullParser, NoParseError)
from print_time import print_time

modpath = rootpath / 'SWMH-BETA/SWMH'
# modpath = pathlib.Path('/cygdrive/c/Users/Nicholas/Documents/Paradox Interactive/Crusader Kings II/mod/Britannia')

def recurse_comments(parser, comments):
    if comments:
        try:
            tree = parser.parse('\n'.join(c.val for c in comments))
            yield from recurse(parser, tree, comment=True)
        except NoParseError:
            pass

def recurse(parser, tree, comment=False):
    try:
        for n, v in tree:
            yield from recurse_comments(parser, n.pre_comments)
            if is_codename(n.val):
                yield n.val, not comment
                yield from recurse(parser, v)
    except ValueError:
        pass
    try:
        yield from recurse_comments(parser, tree.ker.pre_comments)
    except AttributeError:
        try:
            yield from recurse_comments(parser, tree.post_comments)
        except AttributeError:
            pass

@print_time
def main():
    simple_parser = SimpleParser()
    full_parser = FullParser()
    simple_parser.moddirs = [modpath]
    full_parser.moddirs = [modpath]
    cultures, cult_groups = get_cultures(simple_parser)
    cultures = set(cultures)
    cultures.update(cult_groups)
    defined_titles = []
    commented_out_titles = []
    for _, tree in full_parser.parse_files('common/landed_titles/*.txt'):
        for title, defined in recurse(simple_parser, tree):
            (defined_titles if defined else commented_out_titles).append(title)
    titles = set(defined_titles) | set(commented_out_titles)
    localisation = get_localisation(simple_parser.moddirs)
    unlocalised_noncounty_titles = [
        t for t in defined_titles
        if not t.startswith('c') and t not in localisation and t != 'e_null']
    unrecognized_nonbarony_keys = []
    unrecognized_barony_keys = []
    unrecognized_culture_keys = []
    for path in files('localisation/*.csv', basedir=simple_parser.moddirs[0]):
        for key, *_ in csv_rows(path):
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
    with (rootpath / 'loc_check_2.txt').open('w') as f:
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
