#!/usr/bin/env python3

import re
from ck2parser import rootpath, get_provinces, SimpleParser
from print_time import print_time

modpath = rootpath / 'SWMH-BETA/SWMH'

def process_landed_titles(parser, prov_title):
    def recurse(tree):
        for n, v in tree:
            if re.match('c_', n.val):
                yield n.val
            elif re.match('[ekd]_', n.val):
                de_jure_counties = tuple(recurse(v))
                error = False
                try:
                    cap_prov = v['capital'].val
                    try:
                        cap_title = prov_title[cap_prov]
                        if (de_jure_counties and
                            cap_title not in de_jure_counties):
                            print('Title {} capital {} ({}) is not de jure'
                                  .format(n.val, cap_title, cap_prov))
                            error = True
                    except KeyError:
                        print('Title {} has invalid capital {}'
                              .format(n.val, cap_prov))
                        error = True
                except KeyError:
                    print('Title {} missing a capital'.format(n.val))
                    error = True
                if error:
                    if len(de_jure_counties) == 1:
                        print('\tMust be {}' .format(de_jure_counties[0]))
                yield from de_jure_counties

    for _, tree in parser.parse_files('common/landed_titles/*'):
        for _ in recurse(tree):
            pass

@print_time
def main():
    parser = SimpleParser()
    parser.moddirs = [rootpath / 'SWMH-BETA/SWMH']
    province_title = {prov: title
                      for prov, title, _ in get_provinces(parser)}
    process_landed_titles(parser, province_title)

if __name__ == '__main__':
    main()
