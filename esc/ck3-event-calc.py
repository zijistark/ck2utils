#!/usr/bin/env python3

import sys
import ck3parser
from print_time import print_time

parser = ck3parser.SimpleParser()


@print_time
def main():
    args = [x.casefold() for x in sys.argv[1:]]
    traits = args

    attr = get_attrs(traits)
    output(attr)


def get_attrs(my_traits):
    all_traits = ck3parser.traits(parser)
    static_values = ck3parser.static_values(parser)

    attr = {a: 0 for a in ('ai_honor', 'ai_rationality', 'ai_vengefulness',
                           'ai_compassion', 'ai_sociability')}

    for trait in my_traits:
        for n, v in all_traits[trait].contents:
            if n.val in attr:
                attr[n.val] += static_values.get(v.val, v.val)

    return attr


def output(attr):
    for k, v in attr.items():
        print(f'{v:>4} {k}')


if __name__ == '__main__':
    main()
