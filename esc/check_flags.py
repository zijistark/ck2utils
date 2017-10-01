#!/usr/bin/env python3

import re
from ck2parser import rootpath, vanilladir, is_codename, SimpleParser
from print_time import print_time


@print_time
def main():
    parser = SimpleParser(rootpath / 'SWMH-BETA/SWMH')
    titles = []
    for _, tree in parser.parse_files('common/landed_titles/*'):
        dfs = list(reversed(tree))
        while dfs:
            n, v = dfs.pop()
            if is_codename(n.val):
                if n.val not in titles:
                    titles.append(n.val)
                dfs.extend(reversed(v))
    no_title = []
    for path in parser.files('gfx/flags/*.tga'):
        try:
            titles.remove(path.stem)
        except ValueError:
            if vanilladir not in path.parents:
                no_title.append(path.name)
    no_flag = [t for t in titles if not t.startswith('b')]
    with (rootpath / 'flags.txt').open('w') as f:
        if no_title:
            print('No title for flag:', *no_title, sep='\n\t', file=f)
        if no_flag:
            print('No flag for title:', *no_flag, sep='\n\t', file=f)


if __name__ == '__main__':
    main()
