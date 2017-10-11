#!/usr/bin/env python3

import re
from ck2parser import rootpath, is_codename, get_cultures, Pair, SimpleParser, FullParser
import print_time

FORMAT_ONLY = False

ALWAYS_NO_TITLES = ['e_sunni', 'e_shiite', 'k_avaria', 'k_lombardy']

def process_title(title_pair):
    title, tree = title_pair.key.val, title_pair.value
    for pair in tree:
        if is_codename(pair.key.val):
            process_title(pair)
    allow = None
    try:
        allow = next(p for p in tree if p.key.val == 'allow')
        tree.contents.remove(allow)
        tree.contents.append(allow)
    except StopIteration:
        pass
    if FORMAT_ONLY:
        return
    if tree.has_pair('landless', 'yes'):
        return
    if tree.get('controls_religion'):
        return
    if title == 'e_null' or title in ALWAYS_NO_TITLES:
        return
    if title.startswith('e'):
        trigger_name = 'title_emperor_basic_allow'
    elif title.startswith('k'):
        trigger_name = 'title_king_basic_allow'
    elif title.startswith('d'):
        trigger_name = 'title_duke_basic_allow'
    else:
        return
    if allow is None:
        allow = Pair('allow')
        tree.contents.append(allow)
    for pair in reversed(allow.value):
        if pair.key.val == 'always' and pair.value.val == 'no':
            allow.value.contents.remove(pair)
            print(title)
    if not allow.value.has_pair(trigger_name, 'yes'):
        allow.value.contents.append(Pair(trigger_name, 'yes'))

def annotate_mod(simple_parser, full_parser, modpath):
    simple_parser.moddirs = [modpath]
    cultures = get_cultures(simple_parser, groups=False)
    full_parser.fq_keys = cultures
    for path, tree in full_parser.parse_files('common/landed_titles/*.txt',
                                              modpath):
        for title_pair in tree:
            process_title(title_pair)
        full_parser.write(tree, path)

@print_time.print_time
def main():
    simple_parser = SimpleParser()
    full_parser = FullParser()
    annotate_mod(simple_parser, full_parser, rootpath / 'SWMH-BETA/SWMH')
    full_parser.crlf = False
    full_parser.tab_indents = False
    full_parser.indent_width = 4
    annotate_mod(simple_parser, full_parser, rootpath / 'EMF/EMF+Vanilla')

if __name__ == '__main__':
    main()
