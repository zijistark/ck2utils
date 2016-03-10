#!/usr/bin/env python3

'''
Tool to aid exploring unusual keys and values in landed_titles.
Meant to be modified while checking output each time.
Printing '0' means no anomalies found under present definitions.
'''

import pprint
import ck2p as ck2parser

PRINT_CULTURES_RELIGIONS = False

rootpath = ck2parser.rootpath
modpath = rootpath / 'SWMH-BETA/SWMH'
# modpath = rootpath / 'CK2Plus/CK2Plus'

cultures, culture_groups = ck2parser.cultures(modpath)
religions, religion_groups = ck2parser.religions(modpath)
if PRINT_CULTURES_RELIGIONS:
    pprint.pprint(cultures)
    pprint.pprint(culture_groups)
    pprint.pprint(religions)
    pprint.pprint(religion_groups)

interesting = [
    'title', 'title_female', 'foa', 'title_prefix', 'short_name', 'name_tier',
    'location_ruler_title', 'dynasty_title_names', 'male_names'
]

# print(repr('(' + '|'.join(interesting) + ')'))
# sys.exit()

results = set()

def exclude(n, v):
    return (ck2parser.is_codename(n) or n in [
        'religion', 'culture', 'color', 'color2', 'capital', 'coat_of_arms',
        'allow', 'controls_religion', 'dignity', 'creation_requires_capital',
        'rebel', 'landless', 'primary', 'pirate', 'tribe', 'mercenary_type',
        'independent', 'strength_growth_per_century', 'mercenary', 'caliphate',
        'assimilate', 'graphical_culture', 'holy_order', 'monthly_income',
        'holy_site', 'gain_effect', 'pentarchy', 'purple_born_heirs',
        'duchy_revokation', 'has_top_de_jure_capital',
        'used_for_dynasty_names'] or
        n in cultures or n in religions or n in religion_groups or
        n in interesting)

# count = 0

def recurse(tree):
    # global count
    for n, v in tree:
        if ck2parser.is_codename(n):
            for p2 in v:
                n2, v2 = p2
                # count += 1
                # if count % 1000 == 0:
                #     print(count, n2, n1, n, flush=True)
                #     sys.exit()
                # print(count, n2, n1, n, level)
                if not exclude(n2, v2):
                    # try:
                    results.add(p2.inline_str(0).split('\n', 1)[0])
                    # print(ck2parser.to_string((n2, v2)))
                    # except TypeError:
                        # print(n2, v2)
            recurse(v1, n1)
            # except ValueError:
            #     print(n1, v1)
            #     sys.exit()

# print(repr(cultures))
# print(repr(cultural_groups))
# print(repr(religions))
# print(repr(religious_groups))
# raise SystemExit

for path, tree in ck2parser.parse_files('common/landed_titles/*', modpath):
    print(path)
    recurse(tree)

print(len(results))

with (rootpath / 'lt_lest.txt').open('w') as f:
    print(sorted(results), sep='\n', file=f)
