#!/usr/bin/env python3

import hashlib
import re
from ck2parser import rootpath, vanilladir, is_codename, SimpleParser
from print_time import print_time


@print_time
def main():
    parser = SimpleParser(rootpath / 'SWMH-BETA/SWMH')
    placeholder_md5 = '5c9d144af032f709172c564dc1d641b9'
    titles = []
    for _, tree in parser.parse_files('common/landed_titles/*.txt'):
        dfs = list(reversed(tree))
        while dfs:
            n, v = dfs.pop()
            if is_codename(n.val):
                if n.val not in titles:
                    titles.append(n.val)
                dfs.extend(reversed(v))
    no_title = []
    placeholders = []
    for path in parser.files('gfx/flags/*.tga'):
        with path.open('rb') as f:
            if hashlib.md5(f.read()).hexdigest() == placeholder_md5:
                placeholders.append(path.stem)
        try:
            titles.remove(path.stem)
        except ValueError:
            if vanilladir not in path.parents:
                no_title.append(path.name)
    no_flag = [t for t in titles if not t.startswith('b')]
    with (rootpath / 'flags.txt').open('w') as f:
        if no_flag:
            print('No flag for title:', *no_flag, sep='\n\t', file=f)
        if placeholders:
            print('Placeholder flag for title:', *placeholders, sep='\n\t',
                  file=f)
        if no_title:
            print('No title for flag:', *no_title, sep='\n\t', file=f)


if __name__ == '__main__':
    main()
