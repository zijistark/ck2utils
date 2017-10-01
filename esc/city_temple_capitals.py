#!/usr/bin/env python3

import collections
import ck2parser
import print_time


@print_time.print_time
def main():
    out_path = ck2parser.rootpath / 'city_temple_capitals.txt'
    parser = ck2parser.SimpleParser(ck2parser.rootpath / 'SWMH-BETA/SWMH')
    id_title = {}
    errors = []
    results = set()
    for number, title, tree in ck2parser.get_provinces(parser):
        id_title[number] = title
        holding = collections.OrderedDict()
        capital = None
        capital_set_today = False
        history = collections.defaultdict(list)
        for n, v in tree:
            try:
                if v.val in ['trade_post', 'family_palace', 'nomad', 'fort',
                             'hospital']:
                    errors.append('ERROR: holding type {} in {}'.format(
                                  v.val, number))
                    continue
                if v.val in ['castle', 'city', 'temple', 'tribal']:
                    holding[n.val] = v.val
                    if not capital:
                        capital_set_today = True
                        capital = n.val
            except AttributeError:
                history[n.val].extend(v)
        if capital and holding[capital] in ['city', 'temple']:
            results.add((number, capital))
        for _, stmts in sorted(history.items()):
            for n, v in stmts:
                if n.val == 'capital':
                    capital_set_today = True
                    capital = v.val
                    try:
                        if holding[capital] in ['city', 'temple']:
                            results.add((number, capital))
                    except KeyError:
                        errors.append('ERROR: unbuilt capital {} in {}'.format(
                                      v.val, number))
                elif n.val == 'remove_settlement':
                    del holding[v.val]
                    if capital == v.val:
                        errors.append('WARNING: removed capital {} in {}'
                                      .format(v.val, number))
                        capital = next(iter(holding)) if holding else None
                        if capital and holding[capital] in ['city', 'temple']:
                            results.add((number, capital))
                        if any(v == 'tribal'
                               for k, v in holding.items() if k != capital):
                            errors.append('ERROR: non-capital tribal in {}'
                                          .format(number))
                elif v.val in ['trade_post', 'family_palace', 'nomad', 'fort',
                             'hospital']:
                    errors.append('ERROR: holding type {} in {}'.format(v.val,
                                                                        number))
                elif v.val in ['castle', 'city', 'temple', 'tribal']:
                    if capital and holding[capital] in ['city', 'temple']:
                        results.add((number, capital))
                    holding[n.val] = v.val
                    if not capital:
                        capital = n.val
            if capital_set_today and any(v == 'tribal'
                   for k, v in holding.items() if k != capital):
                errors.append('ERROR: non-capital tribal in {}'.format(number))
            capital_set_today = False
    with out_path.open('w') as fp:
        for line in errors:
            print(line, file=fp)
        if results:
            print('Provinces with city or temple capitals:', file=fp)
            for number, capital in sorted(results):
                print('\t{} {} {}'.format(number, id_title[number], capital),
                      file=fp)

if __name__ == '__main__':
    main()
