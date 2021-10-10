#!/usr/bin/env python3

from collections import defaultdict
from pathlib import Path
import re
import sys
from print_time import print_time

LINE_ENDINGS = False
IGNORE_COMMENTS = False

BINARY = ['.dds', '.tga', '.xac', '.bmp', '.db', '.jpg', '.yml', '.xlsx',
          '.ogg', '.wav', '.xcf', '.psd', '.sublime-workspace', '.rar', '.ttf',
          '.otf', '.pdf', '.cur', '.png', '.mesh', '.anim', '.swatch', '.bank']


@print_time
def main():
    wd = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    bad_chars = '[\udc80-\udcff]|ï»¿|' + '|'.join(
        re.escape(c.encode().decode('cp1252', errors='surrogateescape'))
        for c in bytes(range(0x80, 0x100)).decode('cp1252', errors='ignore'))
    audit = defaultdict(list)
    crlfs = []
    lfs = []
    for path in sorted(wd.rglob('*')):
        if (path.is_file() and path.suffix not in BINARY and
            '.git' not in path.parts):
            relpath = path.relative_to(wd)
            try:
                try:
                    with path.open(encoding='utf_8_sig', newline='') as fp:
                        text = fp.read() # just make sure it decodes
                except UnicodeDecodeError:
                    with path.open(encoding='cp1252', newline='') as fp:
                        text = fp.read()
                    for i, line in enumerate(text.splitlines()):
                        if IGNORE_COMMENTS:
                            line = line.split('#', 1)[0]
                        for match in re.findall(bad_chars, line):
                            audit[relpath].append(f'{i + 1}: {match!r}')
                if LINE_ENDINGS:
                    crlf = '\r\n' in text
                    lf = bool(re.search(r'[^\r]\n', text))
                    if crlf and not lf:
                        crlfs.append(relpath)
                    if not crlf and lf:
                        lfs.append(relpath)
                    if crlf and lf:
                        audit[relpath].append('inconsistent line endings')
            except Exception:
                audit[relpath].append(str(sys.exc_info()[1]))
    if LINE_ENDINGS:
        print(f'LF files', *lfs, sep='\n\t')
        print(f'CRLF files', *crlfs, sep='\n\t')
        print('-' * 20)
    if audit:
        print(wd)
    for path, results in sorted(audit.items()):
        if results:
            print(path, *results, sep='\n\t')

if __name__ == '__main__':
    main()
