#!/usr/bin/env python3

import sys
import ck3parser
from print_time import print_time

parser = ck3parser.SimpleParser()
static_values = ck3parser.static_values(parser)

ai_values = ['ai_boldness', 'ai_compassion', 'ai_greed', 'ai_energy',
             'ai_honor', 'ai_rationality', 'ai_sociability', 'ai_vengefulness',
             'ai_zeal']


@print_time
def main():
    # py -m ck3-event-calc calm humble honest
    # py -m ck3-event-calc -e reading 14 6 6 3 8 1 chaste zealous just
    event, stat, traits = handle_args(sys.argv[1:])

    attr = get_attrs(traits)
    stat.update(attr)
    event_result = handlers.get(event)(event, traits, stat)

    output(attr, event_result)


def handle_args(args):
    args = [x.casefold() for x in args]
    event, stat, traits = None, {}, None
    if args[0] == '-e':
        event = args[1]
        stat = {
            'diplomacy': int(args[2]),
            'martial': int(args[3]),
            'stewardship': int(args[4]),
            'intrigue': int(args[5]),
            'learning': int(args[6]),
            'piety_level': int(args[7])
        }
        traits = args[8:]
    return event, stat, traits


def get_attrs(my_traits):
    all_traits = ck3parser.traits(parser)

    attr = {a: 0 for a in ai_values}

    for trait in my_traits:
        for n, v in all_traits[trait].contents:
            if n.val in attr:
                attr[n.val] += static_values.get(v.val, v.val)

    return attr


def handle_reading(event, traits, stat):
    results = {x: 50 for x in ['religious', 'entertaining', 'informative']}

    results['religious'] += stat['ai_zeal'] * 4
    results['religious'] += stat['ai_honor'] * 2
    results['religious'] += stat['piety_level'] * 25
    results['religious'] += max(0, (
        stat['learning'] - static_values['mediocre_skill_rating']) * 5)

    results['entertaining'] += stat['ai_boldness'] * 2
    results['entertaining'] += stat['ai_greed'] * 2
    results['entertaining'] += stat['ai_sociability'] * 2
    results['entertaining'] += max(0, (
        stat['diplomacy'] - static_values['mediocre_skill_rating']) * 5)
    results['entertaining'] += max(0, (
        stat['martial'] - static_values['mediocre_skill_rating']) * 5)

    results['informative'] += min(0, stat['ai_zeal'] * -2)
    results['informative'] += max(0, (
        stat['stewardship'] - static_values['mediocre_skill_rating']) * 5)
    results['informative'] += (stat['learning'] -
                               static_values['mediocre_skill_rating']) * 10
    if 'arrogant' in traits:
        results['informative'] -= 20
    if 'impatient' in traits:
        results['informative'] -= 20
    if 'dull' in traits:
        results['informative'] -= 20
    if 'shrewd' in traits:
        results['informative'] += 20

    return max(results.items(), key=lambda x: x[1])[0]


def output(attr, event_result):
    if event_result:
        print(event_result)
    for k, v in attr.items():
        print(f'{v:>4} {k[3:]}')


handlers = {
    None: lambda _: None,
    'reading': handle_reading
}

if __name__ == '__main__':
    main()
