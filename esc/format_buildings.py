#!/usr/bin/env python3

import pathlib
import shutil
import tempfile
import ck2parser
import print_time

@print_time.print_time
def main():
    modpath = ck2parser.rootpath / 'SWMH-BETA/SWMH'
    out = modpath / 'common/buildings'
    parser = ck2parser.FullParser(modpath)
    # parser.fq_keys = ['from_dynasty_prefix', 'male_patronym',
    #     'female_patronym', 'bastard_dynasty_prefix', 'from_dynasty_suffix']
    parser.newlines_to_depth = 1

    with tempfile.TemporaryDirectory() as td:
        temp = pathlib.Path(td)
        for inpath, tree in parser.parse_files('common/buildings/*',
                                               basedir=modpath):
            outpath = temp / inpath.name
            with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
                f.write(tree.str(parser))
        while out.exists():
            shutil.rmtree(str(out), ignore_errors=True)
        shutil.copytree(str(temp), str(out))

if __name__ == '__main__':
    main()
