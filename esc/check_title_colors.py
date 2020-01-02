#!/usr/bin/env python3

from collections import defaultdict
from ck2parser import rootpath, is_codename, SimpleParser
from print_time import print_time


@print_time
def main():
    parser = SimpleParser(rootpath / 'SWMH-BETA/SWMH')
    color_title_map = {}
    color_duplicates = defaultdict(set)
    for path, tree in parser.parse_files('common/landed_titles/*.txt'):
        dfs = list(reversed(tree))
        while dfs:
            n, v = dfs.pop()
            if is_codename(n.val):
                color = v.get('color')
                if color:
                    color = tuple(x.val for x in color)
                    existing = color_title_map.get(color)
                    if existing:
                        color_duplicates[color] |= {existing, n.val}
                    else:
                        color_title_map[color] = n.val
                dfs.extend(reversed(v))

    with (rootpath / 'check_title_colors.txt').open('w') as fp:
        if color_duplicates:
            print('Colors used by multiple titles:', file=fp)
            for color, titles in sorted(color_duplicates.items()):
                print('\t', end='', file=fp)
                print(color, *sorted(titles), sep='\n\t\t', file=fp)

if __name__ == '__main__':
    main()
