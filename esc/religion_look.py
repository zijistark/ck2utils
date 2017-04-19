#!/usr/bin/env python3

import collections
import csv
import pathlib
import re
import shutil
import tempfile
import ck2parser
from ck2parser import (rootpath, vanilladir, files, csv_rows, get_provinces,
                       get_cultures, get_religions, get_localisation,
                       is_codename, Obj, Date, SimpleParser)
from print_time import print_time

swmhpath = ck2parser.rootpath / 'SWMH-BETA/SWMH'
emfpath = ck2parser.rootpath / 'EMF/EMF'
emfswmhpath = ck2parser.rootpath / 'EMF/EMF+SWMH'

def get_religions(parser):
    religions = []
    for _, tree in parser.parse_files('common/religions/*'):
        for n, v in tree:
            for n2, v2 in v:
                if (isinstance(v2, Obj) and
                    n2.val not in ('color', 'male_names', 'female_names')):
                    try:
                        parent = v2['parent'].val
                    except KeyError:
                        parent = ''
                    religions.append((n.val, n2.val, parent))
    return religions

@print_time
def main():
    parser = ck2parser.SimpleParser()
    parser.moddirs = []
    religions_vanilla = ck2parser.get_religions(parser, groups=False)
    parser.moddirs = [swmhpath, emfpath, emfswmhpath]
    religions = get_religions(parser)

    rows = [['Group', 'Religion', 'Parent', 'Vanilla?']]
    for group, religion, parent in religions:
        vanilla = 'Y' if religion in religions_vanilla else 'N'
        rows.append([group, religion, parent, vanilla])

    outpath = ck2parser.rootpath / 'religion_look.csv'

    with outpath.open('w', newline='') as csvfile:
        csv.writer(csvfile).writerows(rows)

if __name__ == '__main__':
    main()
