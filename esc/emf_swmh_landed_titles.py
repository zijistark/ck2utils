#!/usr/bin/env python3

import re
from ck2parser import rootpath, get_cultures, SimpleParser, FullParser
import print_time

FORMAT_ONLY = False
WHITELIST = ['zz_emf_heresy_titles_SWMH.txt']

def keep_condition(pair):
    try:
        if pair.key.val.upper() != 'NOT': return True
        if len(pair.value) != 1: return True
        pair2 = pair.value.contents[0]
        if pair2.key.val != 'liege': return True
        if len(pair2.value) != 1: return True
        pair3 = pair2.value.contents[0]
        if pair3.key.val != 'has_landed_title': return True
        return not re.fullmatch(r'e_\w+', pair3.value.val)
    except AttributeError:
        return True

def update_tree(tree):
    for n, v in tree:
        if n.val.startswith('e_'):
            update_tree(v)
        elif n.val.startswith('k_'):
            try:
                allow = v['allow']
            except KeyError:
                continue
            allow.contents = list(filter(keep_condition, allow.contents))

@print_time.print_time
def main():
    swmhpath = rootpath / 'SWMH-BETA/SWMH'
    minipath = rootpath / 'MiniSWMH/MiniSWMH'
    simple_parser = SimpleParser(swmhpath)
    full_parser = FullParser()
    full_parser.fq_keys = get_cultures(simple_parser, groups=False)
    emf_swmh_lt = rootpath / 'EMF/EMF+SWMH/common/landed_titles'
    emf_mini_lt = rootpath / 'EMF/EMF+MiniSWMH/common/landed_titles'

    for indir, outdir in [(swmhpath, emf_swmh_lt), (minipath, emf_mini_lt)]:
        if not outdir.exists():
            outdir.mkdir(parents=True)
        for inpath, tree in full_parser.parse_files('common/landed_titles/*',
                                                    basedir=indir):
            if inpath.name in WHITELIST:
                continue
            if not FORMAT_ONLY:
                update_tree(tree)
            outpath = outdir / inpath.name
            with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
                f.write(tree.str(full_parser))

if __name__ == '__main__':
    main()
