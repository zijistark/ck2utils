#!/usr/bin/env python3

import re
from ck2parser import rootpath, get_cultures, Pair, SimpleParser, FullParser
import print_time

MODPATHS = [rootpath / 'SWMH-BETA/SWMH', rootpath / 'EMF/EMF+Vanilla']
FORMAT_ONLY = False

def process_title(title_pair):
    title, tree = title_pair.key.val, title_pair.value
    for pair in tree:
        if re.match('[ekdcb]_', pair.key.val):
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
    if any(p.key.val == 'controls_religion' for p in tree):
        return
    if title == 'e_null':
        return
    if title.startswith('e'):
        trigger_name = 'title_emperor_basic_allow_trigger'
    elif title.startswith('k'):
        trigger_name = 'title_king_basic_allow_trigger'
    else:
        return
    if allow is None:
        allow = Pair('allow')
        tree.contents.append(allow)
    if allow.value.has_pair('always', 'no'):
        print(title)
    if not allow.value.has_pair(trigger_name, 'yes'):
        allow.value.contents.append(Pair(trigger_name, 'yes'))

@print_time.print_time
def main():
    simple_parser = SimpleParser()
    full_parser = FullParser()
    for modpath in MODPATHS:
        simple_parser.moddirs = [modpath]
        cultures = get_cultures(simple_parser, groups=False)
        full_parser.fq_keys = cultures
        for path, tree in full_parser.parse_files('common/landed_titles/*',
                                                  basedir=modpath):
            for title_pair in tree:
                process_title(title_pair)
            with path.open('w', encoding='cp1252', newline='\r\n') as f:
                f.write(tree.str(full_parser))

if __name__ == '__main__':
    main()
