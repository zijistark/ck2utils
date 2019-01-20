#!/usr/bin/env python3

from collections import defaultdict
from pathlib import Path
import re
import sys
from print_time import print_time

# cd ~/mod/modules-alpha
# find -exec sh -c 'cd {} && audit3.py' \;

IGNORE_COMMENTS = False

BINARY = ['.dds', '.tga', '.xac', '.bmp', '.db', '.jpg', '.yml', '.xlsx',
          '.ogg', '.wav', '.xcf', '.psd', '.sublime-workspace', '.rar']

@print_time
def main():
    wd = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    bad_chars = '[\udc80-\udcff]|ï»¿|' + '|'.join(
        re.escape(c.encode().decode('cp1252', errors='surrogateescape'))
        for c in bytes(range(0x80, 0x100)).decode('cp1252', errors='ignore'))
    audit = defaultdict(list)
    for path in sorted(wd.rglob('*')):
        if (path.is_file() and path.suffix not in BINARY and
            '.git' not in path.parts):
            relpath = path.relative_to(wd)
            try:
                with path.open(encoding='cp1252', errors='surrogateescape',
                               newline='') as fp:
                    for i, line in enumerate(fp):
                        if IGNORE_COMMENTS:
                            line = line.split('#', 1)[0]
                        for match in re.findall(bad_chars, line):
                            result = '{}: {!r}'.format(i + 1, match)
                            audit[relpath].append(result)
            except Exception:
                audit[relpath].append(str(sys.exc_info()[1]))
    if audit:
        print(wd)
    for path, results in sorted(audit.items()):
        if results:
            print(path, *results, sep='\n\t')

if __name__ == '__main__':
    main()
