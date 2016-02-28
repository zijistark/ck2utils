#!/usr/bin/env python3

import re
import ck2parser
from print_time import print_time

rootpath = ck2parser.rootpath
modpath = rootpath / 'SWMH-BETA/SWMH'

def process_landed_titles(where, prov_title):
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

    for _, tree in ck2parser.parse_files('common/landed_titles/*', modpath):
        for _ in recurse(tree):
            pass

@print_time
def main():
    province_title = {prov: title
                      for prov, title, _ in ck2parser.provinces(modpath)}
    process_landed_titles(modpath, province_title)

if __name__ == '__main__':
    main()
