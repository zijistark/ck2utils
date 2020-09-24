#!/usr/bin/env python3

from collections import defaultdict
import pprint
import ck3parser
from print_time import print_time

parser = ck3parser.SimpleParser()


@print_time
def main():
    traits = highest_education_traits()
    starts_by_trait = {t: [] for t in traits}
    for date in start_dates():
        titles_by_char = held_titles(date)
        top_titles_by_char = {c: top_tier_titles(l)
                              for c, l in titles_by_char.items()}
        for trait, chars in chars_with_traits(date, traits).items():
            for char in chars:
                titles = top_titles_by_char.get(char)
                if titles:
                    starts_by_trait[trait].append((date, titles))
    output(starts_by_trait)


def highest_education_traits():
    all_traits = ck3parser.traits(parser)
    return [trait for trait, v in all_traits.items()
            if v.has_pair('education', 'yes') and v.has_pair('level', 4)]


def start_dates():
    result = set()
    for _, tree in parser.parse_files('common/bookmarks/*.txt'):
        for n, v in tree:
            result.add(v['start_date'].val)
    return sorted(result)


def chars_with_traits(date, traits):
    result = defaultdict(list)
    for _, tree in parser.parse_files('history/characters/*.txt',
                                      memcache=True):
        for n, v in tree:
            for trait in traits_when(v, date).intersection(traits):
                result[trait].append(str(n.val))
    return result


# XXX assumes we only care about traits with minimum_age = 16
def traits_when(char_history, date):
    life = {'birth': None, 'death': None}
    traits = set()
    tick_history(traits, life, char_history)
    ticks = sorted(((n.val, v) for n, v in char_history
                    if isinstance(n, ck3parser.Date) and n.val <= date),
                   key=lambda x: x[0])
    for tick_date, tick in ticks:
        tick_history(traits, life, tick, tick_date)
    if (life['birth'] is None or life['birth'] > (date[0] - 16, *date[1:]) or
            life['death'] is not None and life['death'] <= date):
        traits.clear()
    return traits


def tick_history(traits, life, tick, date=(0, 0, 0)):
    for n, v in tick:
        if n.val in ('trait', 'add_trait'):
            traits.add(v.val)
        elif n.val == 'remove_trait':
            traits.discard(v.val)
        elif n.val in ('birth', 'death'):
            # deal with death={}, death=asdf, death=1.1.1, and death="1.1.1"
            if isinstance(v, ck3parser.Obj) or '.' not in v.val:
                life[n.val] = date
            else:
                life[n.val] = (v.val if isinstance(v.val, tuple) else
                               date_str_to_tuple(v.val))


def date_str_to_tuple(string):
    return tuple((int(x) if x else 0) for x in string.split('.'))


def held_titles(date):
    result = defaultdict(list)
    for _, tree in parser.parse_files('history/titles/*.txt', memcache=True):
        for n, v in tree:
            holder = title_holder_when(v, date)
            if holder != '0':
                result[holder].append(n.val)
    return result


def top_tier_titles(titles):
    for tier in 'ekdcb':
        subset = sorted(t for t in titles if t.startswith(tier))
        if subset:
            return subset


def title_holder_when(title_history, date):
    holder = '0'
    ticks = sorted(((n.val, v) for n, v in title_history
                    if isinstance(n, ck3parser.Date) and n.val <= date),
                   key=lambda x: x[0])
    for date, tick in ticks:
        for n, v in tick:
            if n.val == 'holder':
                holder = str(v.val)
    return holder


def output(starts_by_trait):
    pprint.pp(starts_by_trait)


if __name__ == '__main__':
    main()
