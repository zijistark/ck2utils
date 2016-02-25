import collections
import csv
import functools
import operator
import pathlib
import re
import sys
from funcparserlib import lexer
from funcparserlib import parser
import localpaths

rootpath = localpaths.rootpath
vanilladir = localpaths.vanilladir

csv.register_dialect('ckii', delimiter=';', doublequote=False,
                     quotechar='\0', quoting=csv.QUOTE_NONE, strict=True)

# these used only to compute long line wrapping
TAB_WIDTH = 4 # minimum 2
CHARS_PER_LINE = 120

fq_keys = []
errors_default = None
_parse_tree_cache = {}

memoize = functools.lru_cache(maxsize=None)

def force_quote(key):
    global fq_keys
    return isinstance(key, String) and key.val in fq_keys

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
                errors=errors_default, cache=False):
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

def chars(line):
    line = str(line)
    try:
        line = line.splitlines()[-1]
    except IndexError: # empty string
        pass
    col = 0
    for char in line:
        if char == '\t':
            col = (col // TAB_WIDTH + 1) * TAB_WIDTH
        else:
            col += 1
    return col

token_specs = [
    ('comment', (r'#(.*\S)?',)),
    ('whitespace', (r'[ \t]+',)),
    ('newline', (r'\r?\n',)),
    ('op', (r'[={}]',)),
    ('date', (r'\d*\.\d*\.\d*',)),
    ('number', (r'\d+(\.\d+)?(?!\w)',)),
    ('quoted_string', (r'"[^"#\r\n]*"',)),
    ('unquoted_string', (r'[^\s"#={}]+',))
]
useless = ['whitespace']
tokenize = lexer.make_tokenizer(token_specs)

def comments_to_str(comments, indent):
    if not comments:
        return ''
    sep = '\n' + indent * '\t'
    try:
        tree = parse('\n'.join(c.val for c in comments))
        if not tree.contents:
            raise ValueError()
    except (parser.NoParseError, ValueError):
        butlast = comments_to_str(comments[:-1], indent)
        if butlast:
            butlast += indent * '\t'
        return butlast + str(comments[-1]) + '\n'
    tree.indent = indent
    s = ''
    for p in tree:
        p_is, _ = p.inline_str(tree.indent_col)
        p_is_lines = p_is.rstrip().splitlines()
        s += '#' + p_is_lines[0] + sep
        s += ''.join('#' + line[indent:] + sep for line in p_is_lines[1:])
    if tree.post_comments:
        s += comments_to_str(tree.post_comments, indent)
    s = s.rstrip('\t')
    return s

class Comment(object):
    def __init__(self, string):
        if string[0] == '#':
            string = string[1:]
        self.val = string.strip()

    def __str__(self):
        return ('# ' if self.val and self.val[0] != '#' else '#') + self.val

class Stringifiable(object):
    def __init__(self):
        self.indent = 0

    @property
    def indent(self):
        return self._indent

    @indent.setter
    def indent(self, value):
        self._indent = value

    @property
    def indent_col(self):
        return self.indent * TAB_WIDTH

class TopLevel(Stringifiable):
    def __init__(self, contents, post_comments):
        self.contents = contents
        self.post_comments = [Comment(s) for s in post_comments]
        self._dictionary = None
        super().__init__()

    def __len__(self):
        return len(self.contents)

    def __contains__(self, item):
        return item in self.contents

    def __iter__(self):
        return iter(self.contents)

    def __getitem__(self, key):
        return self.dictionary[key]

    # assumes keys occur at most once
    def has_pair(self, key_val, val_val):
        return key_val in self.dictionary and self[key_val].val == val_val

    @property
    def indent(self):
        return self._indent

    @property
    def has_pairs(self):
        return not self.contents or isinstance(self.contents[0], Pair)

    @property
    def dictionary(self):
        if self._dictionary is None:
            self._dictionary = {k.val: v for k, v in reversed(self.contents)}
        return self._dictionary

    @indent.setter
    def indent(self, value):
        self._indent = value
        for item in self:
            item.indent = value

    def str(self):
        s = ''.join(x.str() for x in self)
        if self.post_comments:
            s += self.indent * '\t'
            s += comments_to_str(self.post_comments, self.indent)
        return s

class Commented(Stringifiable):
    def __init__(self, pre_comments, string, post_comment):
        self.pre_comments = [Comment(s) for s in pre_comments]
        self.val = self.str_to_val(string)
        self.post_comment = Comment(post_comment) if post_comment else None
        super().__init__()

    @classmethod
    def from_str(cls, string):
        return cls([], string, None)

    @property
    def has_comments(self):
        return self.pre_comments or self.post_comment

    str_to_val = lambda _, x: x

    def val_str(self):
        val_is, _ = self.val_inline_str(self.indent_col)
        return self.indent * '\t' + val_is

    def val_inline_str(self, col):
        s = str(self.val)
        return s, col + chars(s)

    def str(self):
        s = ''
        if self.pre_comments:
            s += self.indent * '\t'
            s += comments_to_str(self.pre_comments, self.indent)
        s += self.indent * '\t' + self.val_str()
        if self.post_comment:
            s += ' ' + str(self.post_comment)
        s += '\n'
        return s

    def inline_str(self, col):
        nl = 0
        sep = '\n' + self.indent * '\t'
        s = ''
        if self.pre_comments:
            if col > self.indent_col:
                s += sep
                nl += 1
            if isinstance(self, Op) and self.val == '}':
                pre_indent = self.indent + 1
                s += '\t'
            else:
                pre_indent = self.indent
            # I can't tell the difference if I'm just after, say, "nor = { "
            # with TAB_WIDTH == 8, but whatever.
            c_s = comments_to_str(self.pre_comments, pre_indent) + sep[1:]
            s += c_s
            nl += c_s.count('\n')
            col = self.indent_col
        val_is, col_val = self.val_inline_str(col)
        s += val_is
        col = col_val
        if self.post_comment:
            s += ' ' + str(self.post_comment) + sep
            nl += 1
            col = self.indent_col
        return s, (nl, col)

class String(Commented):
    def __init__(self, *args):
        super().__init__(*args)
        self.force_quote = False

    def val_inline_str(self, col):
        s = self.val
        if self.force_quote or not re.fullmatch(r'\S+', s):
            s = '"{}"'.format(s)
        return s, col + chars(s)

class Number(Commented):
    def str_to_val(self, string):
        try:
            return int(string)
        except ValueError:
            return float(string)
    
class Date(Commented):
    def str_to_val(self, string):
        return tuple((int(x) if x else 0) for x in string.split('.'))

    def val_inline_str(self, col):
        s = '{}.{}.{}'.format(*self.val)
        return s, col + chars(s)
    
class Op(Commented):
    pass

class Pair(Stringifiable):
    def __init__(self, key, tis, value):
        self.key = key
        self.tis = tis
        self.value = value
        if force_quote(self.key):
            self.value.force_quote = True
        super().__init__()

    @classmethod
    def from_kv(cls, key, value):
        if not isinstance(key, Stringifiable):
            key = String.from_str(key)
        if not isinstance(value, Stringifiable):
            value = String.from_str(value)
        return cls(key, Op.from_str('='), value)

    def __iter__(self):
        yield self.key
        yield self.value

    @property
    def has_comments(self):
        return any(x.has_comments for x in [self.key, self.tis, self.value])

    @property
    def indent(self):
        return self._indent

    @indent.setter
    def indent(self, value):
        self._indent = value
        self.key.indent = value
        self.tis.indent = value
        self.value.indent = value

    def str(self):
        s = self.indent * '\t'
        self_is, _ = self.inline_str(self.indent_col)
        if self_is[-1].isspace():
            if self.indent:
                s += self_is[:-self.indent]
            else:
                s += self_is
        else:
            s += self_is + '\n'
        return s

    def inline_str(self, col):
        s = ''
        nl = 0
        key_is, (nl_key, col_key) = self.key.inline_str(col)
        s += key_is
        nl += nl_key
        col = col_key
        if not s[-1].isspace():
            s += ' '
            col += 1
        tis_is, (nl_tis, col_tis) = self.tis.inline_str(col)
        if col > self.indent_col and col_tis > CHARS_PER_LINE:
            if not s[-2].isspace():
                s = s[:-1]
            tis_s = self.tis.str()
            s += '\n' + tis_s
            nl += 1 + tis_s.count('\n')
            col = self.indent_col
        else:
            if tis_is[0] == '\n':
                s = s[:-1]
                col -= 1
            s += tis_is
            nl += nl_tis
            col = col_tis
        if not s[-1].isspace():
            s += ' '
            col += 1
        val_is, (nl_val, col_val) = self.value.inline_str(col)
        if col > self.indent_col and col_val > CHARS_PER_LINE:
            if not s[-2].isspace():
                s = s[:-1]
            val_s = self.value.str()
            s += '\n' + val_s + self.indent * '\t'
            nl += 1 + val_s.count('\n')
            col = self.indent_col
        else:
            if val_is[0] == '\n':
                s = s[:-1]
                col -= 1
            s += val_is
            nl += nl_val
            col = col_val
        return s, (nl, col)

class Obj(Stringifiable):
    def __init__(self, kel, contents, ker):
        self.kel = kel
        self.contents = contents
        self.ker = ker
        self._dictionary = None
        super().__init__()

    @classmethod
    def from_iter(cls, contents):
        return cls(Op.from_str('{'), list(contents), Op.from_str('}'))

    def __len__(self):
        return len(self.contents)

    def __contains__(self, item):
        return item in self.contents

    def __iter__(self):
        return iter(self.contents)

    def __getitem__(self, key):
        return self.dictionary[key]

    # assumes keys occur at most once
    def has_pair(self, key_val, val_val):
        return key_val in self.dictionary and self[key_val].val == val_val

    @property
    def has_pairs(self):
        return not self.contents or isinstance(self.contents[0], Pair)

    @property
    def dictionary(self):
        if self._dictionary is None:
            self._dictionary = {k.val: v for k, v in reversed(self.contents)}
        return self._dictionary

    @property
    def indent(self):
        return self._indent

    @property
    def post_comment(self):
        return self.ker.post_comment

    @property
    def has_comments(self):
        return (self.kel.has_comments or self.ker.has_comments or
                any(x.has_comments for x in self))

    @indent.setter
    def indent(self, value):
        self._indent = value
        self.kel.indent = value
        for item in self:
            item.indent = value + 1
        self.ker.indent = value

    def str(self):
        s = self.indent * '\t'
        self_is, _ = self.inline_str(self.indent_col)
        if self_is[-1].isspace():
            if self.indent:
                s += self_is[:-self.indent]
            else:
                s += self_is
        else:
            s += self_is + '\n'
        return s

    def might_fit_on_line(self):
        if self.kel.has_comments or self.ker.pre_comments:
            return False
        if self.contents and isinstance(self.contents[0], Pair):
            return len(self) == 1 and not self.contents[0].has_comments
        return all(isinstance(x, Commented) and not x.has_comments
                   for x in self)

    def inline_str(self, col):
        s = ''
        nl = 0
        kel_is, (nl_kel, col_kel) = self.kel.inline_str(col)
        s += kel_is
        nl += nl_kel
        col = col_kel
        if self.might_fit_on_line():
            # attempt one line object
            s_oneline, col_oneline = s, col
            for item in self:
                item_is, (nl_item, col_item) = item.inline_str(1 + col_oneline)
                s_oneline += ' ' + item_is
                col_oneline = col_item
                if nl_item > 0 or col_oneline + 2 > CHARS_PER_LINE:
                    break
            else:
                if self.contents:
                    s_oneline += ' '
                    col_oneline += 1
                ker_is, (nl_ker, col_ker) = self.ker.inline_str(col_oneline)
                if (nl_ker == 0 or
                    chars(ker_is.splitlines()[0]) <= CHARS_PER_LINE):
                    s_oneline += ker_is
                    return s_oneline, (nl_ker, col_ker)
        if self.has_pairs:
            if s[-1].isspace():
                if self.indent:
                    s = s[:-self.indent]
            else:
                s += '\n'
                nl += 1
            for item in self:
                item_s = item.str()
                s += item_s
                nl += item_s.count('\n')
            s += self.indent * '\t'
            col = self.indent_col
        else:
            sep = '\n' + (self.indent + 1) * '\t'
            sep_col = chars(sep)
            if s[-1].isspace():
                s += '\t'
            else:
                s += sep
                nl += 1
            col = sep_col
            for item in self:
                if not s[-1].isspace():
                    s += ' '
                    col += 1
                item_is, (nl_item, col_item) = item.inline_str(col)
                if col > self.indent_col and col_item > CHARS_PER_LINE:
                    if not s[-2].isspace():
                        s = s[:-1]
                    s += sep
                    nl += 1
                    col = sep_col
                    item_is, (nl_item, col_item) = item.inline_str(col)
                s += item_is
                nl += nl_item
                col = col_item
            if not s[-1].isspace():
                s += '\n' + self.indent * '\t'
                nl += 1
                col = self.indent_col
        ker_is, (nl_ker, col_ker) = self.ker.inline_str(col)
        s += ker_is
        nl += nl_ker
        col = col_ker
        return s, (nl, col)

def unquote(string):
    return string[1:-1]

def some(tok_type):
    return (parser.some(lambda tok: tok.type == tok_type) >>
            (lambda tok: tok.value)).named(str(tok_type))

unarg = lambda f: lambda x: f(*x)
many = parser.many
maybe = parser.maybe
skip = parser.skip
fwd = parser.with_forward_decls

nl = skip(many(some('newline')))
end = nl + skip(parser.finished)
comment = some('comment')
commented = lambda x: (many(nl + comment) + nl + x + maybe(comment))

def op(s):
    return (commented(parser.a(lexer.Token('op', s)) >>
            (lambda tok: tok.value)) >> unarg(Op))

unquoted_string = commented(some('unquoted_string')) >> unarg(String)
quoted_string = commented(some('quoted_string') >> unquote) >> unarg(String)
number = commented(some('number')) >> unarg(Number)
date = commented(some('date')) >> unarg(Date)

key = unquoted_string | date | number
value = fwd(lambda: obj | key | quoted_string)
pair = key + op('=') + value >> unarg(Pair)
obj = op('{') + (many(pair | value)) + op('}') >> unarg(Obj)
toplevel = many(pair) + many(nl + comment) + end >> unarg(TopLevel)

def parse(s):
    tokens = [t for t in tokenize(s) if t.type not in useless]
    # try:
    tree = toplevel.parse(tokens)
    # except parser.NoParseError:
    #     from pprint import pprint
    #     pprint(list(enumerate(tokens[:20])))
    #     raise
    return tree

def parse_file(path, encoding='cp1252', errors=errors_default, cache=False):
    global _parse_tree_cache
    if path in _parse_tree_cache:
        #and os.path.getmtime(str(path)) <= _parse_tree_cache[path].mtime):
        return _parse_tree_cache[path]
    with path.open(encoding=encoding, errors=errors) as f:
        try:
            tree = parse(f.read())
            #tree.mtime = time.time()
            if cache:
                _parse_tree_cache[path] = tree
            return tree
        except (lexer.LexerError, parser.NoParseError) as e:
            print(path)
            print(sys.exc_info())
            return e
        except:
            print(path)
            raise
