#!/usr/bin/env python3

import collections
import pathlib
import re
import string
import sys
import localpaths

LINE_ENDINGS = False

rootpath = localpaths.rootpath
# wd = rootpath / 'CK2Plus'
# wd = rootpath / 'SWMH-BETA'
# wd = rootpath / 'EMF'
# wd = rootpath / 'Britannia'
wd = pathlib.Path('C:/Users/Nicholas/Documents/Paradox Interactive/Crusader Kings II/mod/modules')

glob = '**/*'
out_path = rootpath / 'audit2.txt'
binary = ['.dds', '.tga', '.xac', '.bmp', '.db', '.jpg', '.yml', '.xlsx',
          '.ogg', '.wav', '.xcf', '.psd']
suspicious = ['Â¡', 'Â¤', 'Â§', 'Â°', 'Â¿', 'Ã€', 'Ã', 'Ã‚', 'Ãƒ', 'Ã„', 'Ã…',
              'Ã†', 'Ã‡', 'Ãˆ', 'Ã‰', 'ÃŠ', 'Ã‹', 'ÃŒ', 'Ã', 'ÃŽ', 'Ã', 'Ã',
              'Ã‘', 'Ã’', 'Ã“', 'Ã”', 'Ã•', 'Ã–', 'Ã˜', 'Ã™', 'Ãš', 'Ãœ', 'Ãž',
              'ÃŸ', 'Ã ', 'Ã¡', 'Ã¢', 'Ã£', 'Ã¤', 'Ã¥', 'Ã¦', 'Ã§', 'Ã¨', 'Ã©',
              'Ãª', 'Ã«', 'Ã¬', 'Ã­', 'Ã®', 'Ã¯', 'Ã°', 'Ã±', 'Ã²', 'Ã³', 'Ã´',
              'Ãµ', 'Ã¶', 'Ã¸', 'Ã¹', 'Ãº', 'Ã»', 'Ã¼', 'Ã½', 'Ã¾', 'Ã¿', 'Å“',
              'Å ', 'Å¡', 'Å½', 'Å¾', 'â€“', 'â€˜', 'â€™', 'â€œ', 'â€', 'â€ ',
              'â€¦']
somewhat_suspicious = [
    'â‚¬', 'â€š', 'Æ’', 'â€ž', 'â€¦', 'â€ ', 'â€¡', 'Ë†', 'â€°', 'Å ', 'â€¹',
    'Å’', 'Å½', 'â€˜', 'â€™', 'â€œ', 'â€', 'â€¢', 'â€“', 'â€”', 'Ëœ', 'â„¢',
    'Å¡', 'â€º', 'Å“', 'Å¾', 'Å¸', 'Â ', 'Â¡', 'Â¢', 'Â£', 'Â¤', 'Â¥', 'Â¦',
    'Â§', 'Â¨', 'Â©', 'Âª', 'Â«', 'Â¬', 'Â­', 'Â®', 'Â¯', 'Â°', 'Â±', 'Â²',
    'Â³', 'Â´', 'Âµ', 'Â¶', 'Â·', 'Â¸', 'Â¹', 'Âº', 'Â»', 'Â¼', 'Â½', 'Â¾',
    'Â¿', 'Ã€', 'Ã', 'Ã‚', 'Ãƒ', 'Ã„', 'Ã…', 'Ã†', 'Ã‡', 'Ãˆ', 'Ã‰', 'ÃŠ',
    'Ã‹', 'ÃŒ', 'Ã', 'ÃŽ', 'Ã', 'Ã', 'Ã‘', 'Ã’', 'Ã“', 'Ã”', 'Ã•', 'Ã–', 'Ã—',
    'Ã˜', 'Ã™', 'Ãš', 'Ã›', 'Ãœ', 'Ã', 'Ãž', 'ÃŸ', 'Ã ', 'Ã¡', 'Ã¢', 'Ã£',
    'Ã¤', 'Ã¥', 'Ã¦', 'Ã§', 'Ã¨', 'Ã©', 'Ãª', 'Ã«', 'Ã¬', 'Ã­', 'Ã®', 'Ã¯',
    'Ã°', 'Ã±', 'Ã²', 'Ã³', 'Ã´', 'Ãµ', 'Ã¶', 'Ã·', 'Ã¸', 'Ã¹', 'Ãº', 'Ã»',
    'Ã¼', 'Ã½', 'Ã¾', 'Ã¿']
regex = '|'.join(['\ufffd'] + somewhat_suspicious)
encoding_exception = {
#    wd / 'SWMH/map/default.map':
#        'utf-8' #XXX
}

crlfs = []
lfs = []

def audit_file(fp, path):
    if LINE_ENDINGS:
        fs = fp.read()
        crlf = '\r\n' in fs
        lf = bool(re.search(r'[^\r]\n', fs))
        if crlf and not lf:
            crlfs.append(path)
        if not crlf and lf:
            lfs.append(path)
        if crlf and lf:
            yield 'Error: Inconsistent line endings'
        fp.seek(0)
    for i, line in enumerate(fp):
        for match in re.findall(regex, line.split('#', 1)[0]):
            yield '{}: {!r}'.format(i + 1, match)

audit = collections.defaultdict(list)
for path in sorted(wd.glob(glob)):
    try:
        if (path.is_file() and path.suffix not in binary and
            '.git' not in path.parts):
            encoding = encoding_exception.get(path, 'cp1252')
            with path.open(encoding=encoding, errors='replace', newline='') as fp:
                path = path.relative_to(wd)
                audit[path].extend(audit_file(fp, path))
    except:
        audit[path].append(str(sys.exc_info()[1]))
if LINE_ENDINGS:
    print('{} CRLF files'.format(len(crlfs)))
    print('{} LF files'.format(len(lfs)))
    if len(crlfs) > len(lfs):
        kind = 'LF'
        files = lfs
    else:
        kind = 'CRLF'
        files = crlfs
with out_path.open('w', encoding='cp1252') as fp:
    if LINE_ENDINGS:
        print(kind + ' files', *files, sep='\n\t', file=fp)
    for path, results in sorted(audit.items()):
        if results:
            print(path, *results, sep='\n\t', file=fp)
