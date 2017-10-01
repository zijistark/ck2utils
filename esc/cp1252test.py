#!/usr/bin/env python3

import collections
import pathlib

root = pathlib.Path('../SWMH-BETA/SWMH')

globs = [
    'common/**/*.*',
    'events/*.*',
    'history/**/*.*',
    'interface/*.gui',
    'localisation/*.*',
    'map/*.csv',
    'map/*.map',
    'map/*.txt'
]

charlocs = collections.defaultdict(list)
for glob in globs:
    for path in sorted(root.glob(glob)):
        with path.open('rb') as f:
            for i, line in enumerate(f):
                for char in line:
                    if char in range(0x80, 0xA0):
                        charlocs[char].append((path.name, i))
for char, locs in sorted(charlocs.items()):
    print('{:x}:'.format(char))
    for loc in locs:
        print('\tFile "{}", line {}'.format(*loc))
