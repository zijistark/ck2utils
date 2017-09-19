#!/usr/bin/env python3

import re
from ck2parser import rootpath, SimpleParser
from print_time import print_time


@print_time
def main():
    parser = SimpleParser(rootpath / 'SWMH-BETA/SWMH')
    counties = []
    for _, tree in parser.parse_files('common/landed_titles/*'):
        dfs = list(reversed(tree))
        while dfs:
            n, v = dfs.pop()
            if re.match('[ekd]_', n.val):
                dfs.extend(reversed(v))
            elif n.val.startswith('c_'):
                counties.append(n.val)
    for path in parser.files('history/titles/*'):
        try:
            counties.remove(path.stem)
        except ValueError:
            pass
    with (rootpath / 'no_title_history.txt').open('w') as f:
        print(*counties, sep='\n', file=f)


if __name__ == '__main__':
    main()
