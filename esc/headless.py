#!/usr/bin/env python3

import datetime
import pathlib
import re
import funcparserlib
import funcparserlib.lexer
import funcparserlib.parser
from print_time import print_time

rootpath = pathlib.Path('.')
swmhpath = rootpath / 'SWMH-BETA/SWMH'

def tokenize(string):
    token_specs = [
        ('comment', (r'#.*',)),
        ('whitespace', (r'\s+',)),
        ('op', (r'[={}]',)),
        ('date', (r'\d*\.\d*\.\d*',)),
        ('number', (r'\d+(\.\d+)?',)),
        ('quoted_string', (r'"[^"#]*"',)),
        ('unquoted_string', (r'[^\s"#={}]+',))
    ]
    useless = ['comment', 'whitespace']
    inner_tokenize = funcparserlib.lexer.make_tokenizer(token_specs)
    return (tok for tok in inner_tokenize(string) if tok.type not in useless)

def parse(tokens):
    def unquote(string):
        return string[1:-1]

    def make_number(string):
        try:
            return int(string)
        except ValueError:
            return float(string)

    def make_date(string):
        # CKII appears to default to 0, not 1, but that's awkward to handle
        # with datetime, and it only comes up for b_embriaco anyway
        year, month, day = ((int(x) if x else 1) for x in string.split('.'))
        return datetime.date(year, month, day)

    def some(tok_type):
        return (funcparserlib.parser.some(lambda tok: tok.type == tok_type) >>
                (lambda tok: tok.value))

    def op(string):
        return funcparserlib.parser.skip(funcparserlib.parser.a(
            funcparserlib.lexer.Token('op', string)))

    many = funcparserlib.parser.many
    fwd = funcparserlib.parser.with_forward_decls
    endmark = funcparserlib.parser.skip(funcparserlib.parser.finished)
    unquoted_string = some('unquoted_string')
    quoted_string = some('quoted_string') >> unquote
    number = some('number') >> make_number
    date = some('date') >> make_date
    key = unquoted_string | quoted_string | number | date
    value = fwd(lambda: obj | key)
    pair = fwd(lambda: key + op('=') + value)
    obj = fwd(lambda: op('{') + many(pair | value) + op('}'))
    toplevel = many(pair | value) + endmark
    return toplevel.parse(list(tokens))

def valid_codename(string):
    return re.match(r'[ekdcb]_', string)

def needs_capital(name):
    return re.match(r'[ekd]_', name) and name not in ['e_pirates', 'e_rebels']

def get_headless(where):
    headless = []

    def recurse(v, n=None):
        for n1, v1 in v:
            if valid_codename(n1):
                if (needs_capital(n1) and
                    not any(n2 == 'capital' for n2, _ in v1)):
                    headless.append(n1)
                recurse(v1, n1)

    for path in sorted(where.glob('common/landed_titles/*.txt')):
        with path.open(encoding='cp1252') as f:
            recurse(parse(tokenize(f.read())))
    return headless

@print_time
def main():
    headless = get_headless(pathlib.Path.cwd())
    with (rootpath / 'out.txt').open('w') as f:
        f.write('\n'.join(headless))

if __name__ == '__main__':
    main()
