import collections
import pathlib
import string
import sys

wd = pathlib.Path('C:/Users/Nicholas/Documents/CK2/SWMH-BETA')
# wd = pathlib.Path('C:/Users/Nicholas/Documents/Paradox Interactive/'
                  # 'Crusader Kings II/mod/modules')
glob = '**/*'
out_path = pathlib.Path('out.txt')
binary = ['.dds', '.tga', '.xac', '.bmp', '.db']
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
encoding_exception = {
#    wd / 'SWMH/map/default.map':
#        'utf-8' #XXX
}

def audit_file(fp):
    fs = fp.read()
    for string in somewhat_suspicious:
        if string in fs:
            yield string

audit = collections.defaultdict(list)
for path in sorted(wd.glob(glob)):
    try:
        if (path.is_file() and path.suffix not in binary and
            '.git' not in path.parts):
            encoding = encoding_exception.get(path, 'cp1252')
            with path.open(encoding=encoding) as fp:
                audit[path].extend(audit_file(fp))
    except:
        audit[path].append(str(sys.exc_info()[1]))
with out_path.open('w', encoding='cp1252') as fp:
    for path, results in sorted(audit.items()):
        if results:
            print(path.relative_to(wd), *results, sep='\n\t', file=fp)
