#!/usr/bin/env python3

import pathlib
import shutil
import tempfile
import ck2parser
import print_time

@print_time.print_time
def main():
    modpath = pathlib.Path('/cygdrive/c/Program Files (x86)/Steam/SteamApps/'
                           'common/CK2-previous-versions/2.6.1')
    out = ck2parser.rootpath / 'landed_titles-2.6.1'
    simple_parser = ck2parser.SimpleParser()
    full_parser = ck2parser.FullParser(modpath)
    cultures = ck2parser.get_cultures(simple_parser, groups=False)
    full_parser.fq_keys = cultures

    def update_tree(tree):
        for n, v in tree:
            if ck2parser.is_codename(n.val):
                for child in v.contents:
                    if child.key.val == 'allow':
                        if v.contents[-1] != child:
                            v.contents.remove(child)
                            v.contents.append(child)
                        break
                update_tree(v)

    with tempfile.TemporaryDirectory() as td:
        temp = pathlib.Path(td)
        for inpath, tree in full_parser.parse_files('common/landed_titles/*'):
            outpath = temp / inpath.name
            update_tree(tree)
            with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
                f.write(tree.str(full_parser))
        while out.exists():
            shutil.rmtree(str(out), ignore_errors=True)
        shutil.copytree(str(temp), str(out))

if __name__ == '__main__':
    main()
