#!/usr/bin/env python3


# USAGE:
# log_province_setup.py
# mkdir -p $REPO_ROOT/SWMH-BETA/SWMH/localisation/customizable_localisation
# cp $REPO_ROOT/{EMF/EMF,SWMH-BETA/SWMH}/localisation/customizable_localisation/emf_debug_custom_loc.txt
# cp $REPO_ROOT/{EMF/EMF,SWMH-BETA/SWMH}/localisation/1_emf_debug.csv
# rm $REPO_ROOT/SWMH-BETA/SWMH/common/province_setup/*
# hipinstall.sh --swmh
# ~/common/Crusader\ Kings\ II/CK2game.exe -debug -debugscripts
# # console "run province_setup.txt", quit
# cp ~/win/Documents/Paradox\ Interactive/Crusader\ Kings\ II/logs/game.log $REPO_ROOT/province_setup_data.txt
# province_setup.py # run this file
# git -C $REPO_ROOT/SWMH-BETA clean -df


import re
import ck2parser
from print_time import print_time


NEW_DATA_FROM_FILE = ck2parser.rootpath / 'province_setup_data.txt'
# NEW_DATA_FROM_FILE = None # format only


@print_time
def main():
    parser = ck2parser.FullParser(ck2parser.rootpath / 'SWMH-BETA/SWMH')
    if NEW_DATA_FROM_FILE:
        output_tree = parser.parse('')
        with NEW_DATA_FROM_FILE.open(encoding='cp1252') as f:
            for line in f:
                match = re.search(r'<(.*?)> (.*)', line)
                if match is None:
                    continue
                prov_type, pairs = match.groups()
                data = dict(x.split('=') for x in pairs.split(', '))
                to_parse = '{} = {{\n'.format(data['id'])
                if data.get('title'):
                    to_parse += 'title = {}\n'.format(data['title'])

                to_parse += 'max_settlements = {}\n'.format(
                    data['max_settlements'] if prov_type == 'LAND' else 7)
                to_parse += 'terrain = {}\n'.format(data['terrain'])
                to_parse += '}\n'
                try:
                    parsed = parser.parse(to_parse)
                except:
                    print(repr(to_parse))
                    raise
                output_tree.contents.extend(parsed)
        parsed = parser.parse('# -*- ck2.province_setup -*-')
        output_tree.pre_comments[:0] = parsed.post_comments
    else:
        output_tree = parser.parse_file('common/province_setup/'
                                        '00_province_setup.txt')
    outpath = parser.moddirs[0] / 'common/province_setup/00_province_setup.txt'
    parser.write(output_tree, outpath)


if __name__ == '__main__':
    main()
