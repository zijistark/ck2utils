import collections
import csv
import functools
import operator
import pathlib
import re
import sys
from antlr4 import *
from CK2Lexer import CK2Lexer
from CK2Parser import CK2Parser
from ck2classes import *
import localpaths

rootpath = localpaths.rootpath
vanilladir = localpaths.vanilladir

csv.register_dialect('ckii', delimiter=';', doublequote=False,
                     quotechar='\0', quoting=csv.QUOTE_NONE, strict=True)

errors_default = None
cache_default = False
_parse_tree_cache = {}

memoize = functools.lru_cache(maxsize=None)

def set_fq_keys(keys):
    ck2classes._fq_keys = list(keys)

def csv_rows(path, linenum=False, comments=False):
    with open(str(path), newline='', encoding='cp1252', errors='replace') as f:
        gen = ((r, i + 1) if linenum else r
               for i, r in enumerate(csv.reader(f, dialect='ckii'))
               if (len(r) > 1 and r[0] and
                   (comments or not r[0].startswith('#'))))
        yield from gen

# give mod dirs in descending lexicographical order of mod name (Z-A),
# modified for dependencies as necessary.
def files(glob, *moddirs, basedir=vanilladir, reverse=False):
    result_paths = {p.relative_to(d): p
                    for d in (basedir,) + moddirs for p in d.glob(glob)}
    for _, p in sorted(result_paths.items(), key=lambda t: t[0].parts,
                       reverse=reverse):
        yield p

def parse_files(glob, *moddirs, basedir=vanilladir, encoding='cp1252',
                errors=errors_default, cache=None):
    if cache is None:
        cache = cache_default
    for path in files(glob, *moddirs, basedir=basedir):
        yield path, parse_file(path, encoding, errors, cache)

def flush(path=None):
    global _parse_tree_cache
    if path is None:
        _parse_tree_cache = {}
    else:
        del _parse_tree_cache[path]

@memoize
def cultures(*moddirs, groups=True):
    cultures = []
    culture_groups = []
    for _, tree in parse_files('common/cultures/*', *moddirs):
        for n, v in tree:
            culture_groups.append(n.val)
            cultures.extend(n2.val for n2, v2 in v
                            if n2.val != 'graphical_cultures')
    return (cultures, culture_groups) if groups else cultures

@memoize
def religions(*moddirs, groups=True):
    religions = []
    religion_groups = []
    for _, tree in parse_files('common/religions/*', *moddirs):
        for n, v in tree:
            religion_groups.append(n.val)
            religions.extend(n2.val for n2, v2 in v
                             if (isinstance(v2, Obj) and
                                 n2.val not in ('male_names', 'female_names')))
    return (religions, religion_groups) if groups else religions

_max_provinces = None

@memoize
def province_id_name_map(where):
    global _max_provinces
    _, tree = next(parse_files('map/default.map', where))
    defs = tree['definitions'].val
    _max_provinces = int(tree['max_provinces'].val)
    id_name_map = {}
    defs_path = next(files('map/' + defs, where))
    for row in csv_rows(defs_path):
        try:
            id_name_map[int(row[0])] = row[4]
        except (IndexError, ValueError):
            continue
    return id_name_map

def max_provinces(where):
    if _max_provinces is None:
        province_id_name_map(where)
    return _max_provinces

def provinces(where):
    id_name = province_id_name_map(where)
    for path in files('history/provinces/*', where):
        number, name = path.stem.split(' - ')
        number = int(number)
        if number in id_name and id_name[number] == name:
            tree = parse_file(path)
            try:
                title = tree['title'].val
            except KeyError:
                continue
            yield number, title, tree

def localisation(*moddirs, basedir=vanilladir, ordered=False):
    locs = collections.OrderedDict() if ordered else {}
    loc_glob = 'localisation/*'
    for path in files(loc_glob, *moddirs, basedir=basedir, reverse=True):
        for row in csv_rows(path):
            try:
                if row[0] not in locs:
                    locs[row[0]] = row[1]
            except IndexError:
                continue
    return locs

def first_post_comment(item):
    if item.post_comment:
        return item.post_comment.val.split('#', 1)[0].strip()
    return None

def prepend_post_comment(item, s, force=False):
    if force or first_post_comment(item) != s:
        if item.post_comment:
            s += ' ' + str(item.post_comment)
        item.post_comment = Comment(s)

def is_codename(string):
    try:
        return re.match(r'[ekdcb]_', string) is not None
    except TypeError:
        return False

class MyFileStream(InputStream):
    def __init__(self, fileName, encoding, errors):
        super().__init__(self.readDataFrom(fileName, encoding, errors))
        self.fileName = fileName

    def readDataFrom(self, fileName, encoding, errors):
        with open(fileName, 'r', encoding=encoding, errors=errors) as f:
            return f.read()

def parse_file(path, encoding='cp1252', errors=errors_default, cache=None):
    global _parse_tree_cache
    if cache is None:
        cache = cache_default
    if path in _parse_tree_cache:
        #and os.path.getmtime(str(path)) <= _parse_tree_cache[path].mtime):
        return _parse_tree_cache[path]
    filestream = MyFileStream(str(path), encoding=encoding, errors=errors)
    lexer = CK2Lexer(filestream)
    stream = CommonTokenStream(lexer)
    parser = CK2Parser(stream)
    tree = parser.StartRule()
    if cache:
        _parse_tree_cache[path] = tree
    return tree
