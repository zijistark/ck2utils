#!/usr/bin/env python3

from collections import defaultdict
from ck2parser import (rootpath, is_codename, get_cultures, Comment, Pair,
                       TopLevel, SimpleParser, FullParser)
from print_time import print_time


@print_time
def main():
    modpath = rootpath / 'SWMH-BETA/SWMH'
    simple_parser = SimpleParser(modpath)
    full_parser = FullParser(modpath)
    cultures = get_cultures(simple_parser, groups=False)
    full_parser.fq_keys = cultures

    out_path = modpath / 'common/landed_titles/z_holy_sites.txt'
    if out_path.exists():
        out_tree = full_parser.parse_file(out_path)
        del out_tree.header_comment
    else:
        out_tree = TopLevel()
    old_contents = {p.key.val: p for p in out_tree.contents}
    out_tree.contents = []
    for path in full_parser.files('common/landed_titles/*.txt'):
        if path == out_path:
            continue
        tree = full_parser.parse_file(path)
        dfs = list(reversed(tree))
        while dfs:
            n, v = dfs.pop()
            if is_codename(n.val):
                sites = []
                for p2 in reversed(v):
                    if p2.key.val in ['holy_site', 'pentarchy']:
                        v.contents.remove(p2)
                        sites.insert(0, p2)
                pair = old_contents.get(n.val, Pair(n))
                if sites:
                    pair.value.contents.extend(sites)
                if pair.value.contents:
                    pair.value.kel.post_comment = v.kel.post_comment
                    out_tree.contents.append(pair)
                dfs.extend(reversed(v))
        full_parser.write(tree, path)
    out_tree.header_comment = Comment('-*- ck2.landed_titles -*-')
    full_parser.write(out_tree, out_path)


if __name__ == '__main__':
    main()
