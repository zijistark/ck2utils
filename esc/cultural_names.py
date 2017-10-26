#!/usr/bin/env python3

# script for exploring names in scripted history by culture

from collections import Counter
from pprint import pprint
from ck2parser import rootpath, SimpleParser
from print_time import print_time

@print_time
def main():
    parser = SimpleParser(rootpath / 'SWMH-BETA/SWMH')
    cultures = set()
    for _, tree in parser.parse_files('common/cultures/*.txt'):
        for n, v in tree:
            if n.val == 'italian_group':
                cultures.update(n2.val for n2, v2 in v
                                if n2.val != 'graphical_cultures')
    name_freqs = {c: {False: Counter(), True: Counter()} for c in cultures}
    rulers = set()
    for _, tree in parser.parse_files('history/titles/*.txt'):
        for n, v in tree:
            for n2, v2 in v:
                if n2.val =='holder':
                    rulers.add(v2.val)
    for _, tree in parser.parse_files('history/characters/*.txt'):
        for n, v in tree:
            try:
                char = n.val
                name = v['name'].val
                sex = v.has_pair('female', 'yes')
                culture = v['culture'].val
            except (KeyError, AttributeError):
                continue
            if char in rulers and culture in cultures and name.startswith('N'):
                name_freqs[culture][sex][name] += 1
    pprint(name_freqs)

if __name__ == '__main__':
    main()

# {'umbrian': {False: Counter({'Nerio': 3})},
#  'laziale': {False: Counter({'Nicolo': 3})},
#  'tuscan': {False: Counter({'Neri': 6,
#                             'Nicolò': 4,
#                             'Nello': 3,
#                             'Nicolao': 2,
#                             'Neruccio': 2})},
#  'ligurian': {False: Counter({'Niccolo': 5})},
#  'venetian': {False: Counter({'Niccolo': 6,
#                               'Nicolo': 3,
#                               'Nascinguerra': 2})},
#  'italian': {False: Counter({'Nantelmo': 3})}}



# {'laziale': {False: Counter({'Nicolo': 2})},
#  'sicilian': {False: Counter({'Nicolò': 2})},
#  'tuscan': {False: Counter({'Nello': 2,
#                             'Nicolò': 2,
#                             'Neri': 2})},

