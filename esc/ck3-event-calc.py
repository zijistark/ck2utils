#!/usr/bin/env python3

import sys
from collections.abc import Callable, Container, Iterable, Mapping, Sequence
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
    # py -m ck3-event-calc -e reading 14 6 6 3 8 1
    #     education_diplomacy chaste zealous just diplomacy_lifestyle
    event, stat, traits = handle_args(sys.argv[1:])

    attr = get_attrs(traits)
    stat.update(attr)
    event_result = handlers.get(event)(event, traits, stat)

    output(attr, event_result)


def handle_args(args: Sequence[str]):
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
        traits = set(args[8:])
    else:
        traits = set(args)
    return event, stat, traits


def get_attrs(my_traits: Iterable[str]):
    all_traits = ck3parser.traits(parser)

    attr = dict.fromkeys(ai_values, 0)

    for trait in my_traits:
        if trait_def := all_traits.get(trait):
            for n, v in trait_def.contents:
                if n.val in attr:
                    attr[n.val] += static_values.get(v.val, v.val)

    return attr


def handle_reading(_, traits: Container[str], stat: Mapping[str, int]):
    results = dict.fromkeys(['religious', 'entertaining', 'informative'], 50)

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

    return results


def handle_gift(_, traits: Container[str], stat: Mapping[str, int]):
    results = {x: {True: 75, False: 25} for x in [
        'tapestry', 'horse', 'tailor',
        'embroidery', 'poem', 'woodcarving',
        'jewelry', 'stuffed animal', 'flower',
        'rare book', 'handkerchief', 'object']}

    if not traits.isdisjoint({'family_first', 'arrogant', 'ambitious'}):
        # also if same dynasty
        results['tapestry'][True] += 100
    if not traits.isdisjoint({'humble', 'honest'}):
        # honest only counts if prestige_level < 2
        results['tapestry'][False] += 100

    if not traits.isdisjoint({'lifestyle_hunter', 'strategist', 'overseer',
                              'gallant', 'martial_lifestyle'}):
        results['horse'][True] += 100
    if not traits.isdisjoint({'lazy', 'craven'}):
        results['horse'][False] += 100

    if not traits.isdisjoint({'lifestyle_reveler', 'arrogant'}):
        results['tailor'][True] += 100
    if not traits.isdisjoint({'content', 'chaste'}):
        results['tailor'][False] += 100

    if not traits.isdisjoint({'education_diplomacy', 'diplomacy_lifestyle',
                              'compassionate', 'family_first'}):
        results['embroidery'][True] += 100
    if 'greedy' in traits:
        results['embroidery'][False] += 100

    if not traits.isdisjoint({'education_learning', 'lustful', 'gluttonous',
                              'lifestyle_reveler', 'gregarious', 'diplomat',
                              'august', 'family_first', 'ambitious'}):
        results['poem'][True] += 100
    if not traits.isdisjoint({'chaste', 'temperate', 'content'}):
        results['poem'][False] += 100

    if (not traits.isdisjoint({'education_stewardship', 'architect',
                               'administrator', 'avaricious',
                               'stewardship_lifestyle'}) or
            stat['stewardship'] > 10):
        results['woodcarving'][True] += 100
    if not traits.isdisjoint({'lazy', 'content'}):
        results['woodcarving'][False] += 100

    if not traits.isdisjoint({'greedy', 'beauty_good', 'arrogant', 'lustful'}):
        results['jewelry'][True] += 100
    if not traits.isdisjoint({'temperate', 'generous'}):
        results['jewelry'][False] += 100

    if not traits.isdisjoint({'lifestyle_hunter', 'sadistic', 'torturer',
                              'ambitious', 'deceitful'}):
        results['stuffed animal'][True] += 100
    if not traits.isdisjoint({'compassionate', 'content'}):
        results['stuffed animal'][False] += 100

    if not traits.isdisjoint({'architect', 'administrator', 'avaricious',
                              'seducer', 'diligent', 'beauty_good'}):
        results['flower'][True] += 100
    if 'lazy' in traits:
        results['flower'][False] += 100

    if (stat['learning'] >= 10 or
            not traits.isdisjoint({'scholar', 'whole_of_body', 'theologian'})):
        results['rare book'][True] += 100
    if 'impatient' in traits or stat['learning'] < 10:
        results['rare book'][False] += 100

    # likes: ill, opinion >= 50, prestige level lower, or tier lower
    results['handkerchief'][True] += 100
    # dislikes: prestige level higher or opinion < 50

    # likes: opinion >= 60 or "potential lover" based on earlier interactions,
    # else:
    if 'callous' in traits:
        results['object'][False] += 100

    if not traits.isdisjoint({'architect', 'administrator', 'avaricious',
                              'seducer', 'diligent', 'beauty_good'}):
        results['object'][True] += 100
    if 'lazy' in traits:
        results['object'][False] += 100

    return {k: v[True] / (v[True] + v[False]) for k, v in results.items()}


def output(attr: Mapping[str, int], event_result: Mapping[str, int]):
    for k, v in {**event_result, **attr}.items():
        print(f'{v:7.2f} {k}')


handlers: dict[str | None, Callable[[str, Container[str], Mapping[str, int]],
                                    Mapping[str, int]]] = {
    None: lambda *_: {},
    'reading': handle_reading,
    'gift': handle_gift
}

if __name__ == '__main__':
    main()
