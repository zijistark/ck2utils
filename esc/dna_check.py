#!/usr/bin/env python3

from ck2parser import rootpath, SimpleParser
from print_time import print_time

@print_time
def main():
    parser = SimpleParser()
    dna_chars = set()
    for action, moddirs in [(dna_chars.add, []), (dna_chars.discard, [rootpath / 'SWMH-BETA/SWMH'])]:
        for _, tree in parser.parse_files('history/characters/*.txt', moddirs=moddirs):
            for n, v in tree:
                if v.get('dna'):
                    action(n.val)
    with (rootpath / 'dna.txt').open('w') as f:
        print(*sorted(dna_chars), sep='\n', file=f)

if __name__ == '__main__':
    main()
