#!/usr/bin/env python3

import collections
import pathlib
import pprint
import re
import shutil
import tempfile
import ck2parser
import print_time

JUST_PRINT_STATS = True

def uncomment_baronies(parser, obj):
    for elem in [n for n, v in obj] + [obj.ker]:
        try:
            result = parser.parse('\n'.join(c.val for c in elem.pre_comments))
            if (result.contents and
                all(n.val.startswith('b_') for n, v in result)):
                elem.pre_comments = []
                yield from result.contents
        except (ck2parser.NoParseError, ValueError):
            pass

@print_time.print_time
def main():
    parser = ck2parser.FullParser(ck2parser.rootpath / 'SWMH-BETA/SWMH')
    outdir = parser.moddirs[0] / 'common/landed_titles'
    simple_parser = ck2parser.SimpleParser(*parser.moddirs)

    cultures = ck2parser.get_cultures(simple_parser, groups=False)
    parser.fq_keys = cultures

    defined_baronies = set()
    county_counter = collections.Counter()

    def scan_for_baronies(tree):
        for n, v in tree:
            if ck2parser.is_codename(n.val):
                if n.val.startswith('b_'):
                    yield n.val
                else:
                    yield from scan_for_baronies(v)

    def update_tree(tree):
        for n, v in tree:
            if ck2parser.is_codename(n.val):
                if n.val.startswith('c_'):
                    old_barony_count = sum(1 for n2, _ in v
                                           if n2.val.startswith('b_'))
                    num = 7 - old_barony_count
                    yield max(num, 0)
                    if old_barony_count < 7:
                        if JUST_PRINT_STATS:
                            continue
                        new_baronies = list(uncomment_baronies(parser, v))
                        rejects = []
                        for barony in reversed(new_baronies):
                            if barony.key.val in defined_baronies:
                                new_baronies.remove(barony)
                                rejects.insert(0, barony)
                        rejects.extend(new_baronies[num:])
                        v.contents.extend(new_baronies[:num])
                        for child in v.contents:
                            if child.key.val == 'allow':
                                if v.contents[-1] != child:
                                    v.contents.remove(child)
                                    v.contents.append(child)
                                post_barony_pair = child
                                break
                        else:
                            post_barony_pair = v.ker
                        for barony in reversed(rejects):
                            b_is, _ = barony.inline_str(parser)
                            comments = [ck2parser.Comment(s)
                                        for s in b_is.split('\n')]
                            post_barony_pair.pre_comments[:0] = comments
                else:
                    yield from update_tree(v)

    with tempfile.TemporaryDirectory() as td:
        tempdir = pathlib.Path(td)
        for inpath, tree in parser.parse_files('common/landed_titles/*'):
            temppath = tempdir / inpath.name
            defined_baronies.update(scan_for_baronies(tree))
            county_counter.update(update_tree(tree))
            if JUST_PRINT_STATS:
                continue
            with temppath.open('w', encoding='cp1252', newline='\r\n') as f:
                f.write(tree.str(parser))
        if not JUST_PRINT_STATS:
            while outdir.exists():
                shutil.rmtree(str(outdir), ignore_errors=True)
            shutil.copytree(str(tempdir), str(outdir))

        print('{} defined baronies'.format(len(defined_baronies)))
        print('[1] counties missing [0] baronies:')
        pprint.pprint(sorted(county_counter.items()))
        print('{} total missing baronies'.format(
            sum(k * v for k, v in county_counter.items())))

if __name__ == '__main__':
    main()
