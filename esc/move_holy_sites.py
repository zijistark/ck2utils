#!/usr/bin/env python3

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
        out_path.unlink()
    out_tree = TopLevel()
    for path, tree in full_parser.parse_files('common/landed_titles/*.txt'):
        dfs = list(reversed(tree))
        while dfs:
            n, v = dfs.pop()
            if is_codename(n.val):
                sites = []
                for p2 in reversed(v):
                    if p2.key.val == 'holy_site':
                        v.contents.remove(p2)
                        sites.insert(0, p2)
                if sites:
                    pair = Pair(n, sites)
                    pair.value.kel.post_comment = v.kel.post_comment
                    out_tree.contents.append(pair)
                dfs.extend(reversed(v))
        full_parser.write(tree, path)
    out_tree.pre_comments.insert(0, Comment('-*- ck2.landed_titles -*-'))
    full_parser.write(out_tree, out_path)


if __name__ == '__main__':
    main()
