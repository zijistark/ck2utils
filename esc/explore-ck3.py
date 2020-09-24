#!/usr/bin/env python3

from ck3parser import rootpath, ck3dir, SimpleParser
from print_time import print_time

@print_time
def main():
    parser = SimpleParser()
    for path, tree in parser.parse_files('*/**/*.txt'):
        print(path.relative_to(ck3dir))  # see if it parses

if __name__ == '__main__':
    main()
