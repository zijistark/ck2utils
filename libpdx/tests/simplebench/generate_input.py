#!/usr/bin/python3

import sys
from pathlib import Path

out_path = Path('test_input.txt') if len(sys.argv) < 2 else Path(sys.argv[1])
globs = ['common/*/*.txt', 'history/*/*.txt', 'decisions/*.txt', 'events/*.txt']
base_paths = [
    Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings II"),
    Path("C:/cygwin64/home/ziji/g/EMF/EMF"),
    Path("C:/cygwin64/home/ziji/g/EMF/EMF+SWMH"),
    Path("C:/cygwin64/home/ziji/g/EMF/EMF+Vanilla"),
    Path("C:/cygwin64/home/ziji/g/SWMH-BETA/SWMH"),
]

paths = sorted(f for bp in base_paths for g in globs for f in bp.glob(g) if f.parent.name != 'customizable_localisation')

with out_path.open('wb') as of:
    for p in paths:
        with p.open('rb') as f:
            of.write(b'#### BEGIN: ' + bytes(p) + b'\n')
            of.write(f.read())
            of.write(b'\n')
