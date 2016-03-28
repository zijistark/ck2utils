#!/usr/bin/env python3

from bisect import bisect_left, bisect, insort
from collections import defaultdict
from ck2parser import rootpath, is_codename, Date, SimpleParser, FullParser
from pprint import pprint
from print_time import print_time

#DEBUG_INSPECT_LIST = ['d_aswan']

CHECK_DEAD_HOLDERS = True # slow; most useful with PRUNE_UNEXECUTED_HISTORY
CHECK_LIEGE_CONSISTENCY = True

LANDED_TITLES_ORDER = True # if false, date order

PRUNE_UNEXECUTED_HISTORY = True # prune all after last playable start
PRUNE_IMPOSSIBLE_STARTS = True # implies PRUNE_UNEXECUTED_HISTORY
PRUNE_NONBOOKMARK_STARTS = False # implies PRUNE_IMPOSSIBLE_STARTS

modpaths = [rootpath / 'SWMH-BETA/SWMH']

@print_time
def main():
    parser = SimpleParser()
    landed_titles = []
    title_regions = {}
    def recurse(tree, region='titular'):
        for n, v in tree:
            if is_codename(n.val):
                landed_titles.append(n.val)
                child_region = region
                if region == 'e_null' or (region == 'titular' and
                    any(is_codename(n2.val) for n2, _ in v)):
                    child_region = n.val
                title_regions[n.val] = child_region
                if region == 'titular':
                    child_region = n.val
                recurse(v, region=child_region)
    for _, tree in parser.parse_files('common/landed_titles/*', *modpaths):
        recurse(tree)
    def get_next_day(day):
        next_day = day[0], day[1], day[2] + 1
        if (day[2] == 28 and day[1] == 2 or
            day[2] == 30 and day[1] in (4, 6, 9, 11) or
            day[2] == 31 and day[1] in (1, 3, 5, 7, 8, 10, 12)):
            next_day = next_day[0], next_day[1] + 1, 1
        if next_day[1] == 13:
            next_day = next_day[0] + 1, 1, next_day[2]
        return next_day
    prune = (PRUNE_UNEXECUTED_HISTORY or PRUNE_IMPOSSIBLE_STARTS or
             PRUNE_NONBOOKMARK_STARTS)
    if prune:
        if PRUNE_NONBOOKMARK_STARTS:
            dates_to_examine = []
        else:
            _, defines = next(parser.parse_files('common/defines.txt',
                                                 *modpaths))
            dates_to_examine = [(defines['start_date'].val,
                          get_next_day(defines['last_start_date'].val))]
        for _, tree in parser.parse_files('common/bookmarks/*', *modpaths):
            for _, v in tree:
                date = v['date'].val
                if not any(a <= date < b for a, b in dates_to_examine):
                    interval = date, get_next_day(date)
                    insort(dates_to_examine, interval)
        if PRUNE_IMPOSSIBLE_STARTS or PRUNE_NONBOOKMARK_STARTS:
            for i in range(len(dates_to_examine) - 1, 0, -1):
                if dates_to_examine[i - 1][1] == dates_to_examine[i][0]:
                    dates_to_examine[i - 1] = (dates_to_examine[i - 1][0],
                                               dates_to_examine[i][1])
                    del dates_to_examine[i]
        else:
            dates_to_examine[:] = [(0, 0, 0), dates_to_examine[-1][1]]
        # e.g. [((867, 1, 1), (867, 1, 2)), ((1066, 9, 15), (1337, 1, 2))]
    title_holder_dates = {}
    title_holders = {}
    title_liege_dates = {}
    title_lieges = {}
    if CHECK_DEAD_HOLDERS:
        char_death = {}
        for _, tree in parser.parse_files('history/characters/*', *modpaths):
            for n, v in tree:
                try:
                    char_death[n.val] = next(n2.val for n2, v2 in v
                        if isinstance(n2, Date) and
                        'death' in v2.dictionary)
                except StopIteration:
                    pass
    if CHECK_LIEGE_CONSISTENCY:
        char_titles = defaultdict(dict)
    for path, tree in parser.parse_files('history/titles/*', *modpaths):
        title = path.stem
        if not len(tree) > 0:
            continue
        holder_dates = [(0, 0, 0)]
        holders = [0]
        liege_dates = [(0, 0, 0)]
        lieges = [0]
        for n, v in tree:
            date = n.val
            for n2, v2 in v:
                if n2.val == 'holder':
                    # insert in sorted order
                    i = bisect_left(holder_dates, date)
                    if i == len(holders) or holder_dates[i] != date:
                        holder = 0 if v2.val == '-' else int(v2.val)
                        holder_dates.insert(i, date)
                        holders.insert(i, holder)
                elif n2.val == 'liege':
                    # insert in sorted order
                    i = bisect_left(liege_dates, date)
                    if i == len(lieges) or liege_dates[i] != date:
                        liege = 0 if v2.val in ('0', title) else v2.val
                        liege_dates.insert(i, date)
                        lieges.insert(i, liege)
        #if title in DEBUG_INSPECT_LIST:
        #    pprint(title)
        #    pprint(list(zip(holder_dates, holders)))
        #    pprint(list(zip(liege_dates, lieges)))
        # reverse order to allow deletion
        for i in range(len(holders) - 1, -1, -1):
            # delete redundant entries
            if i > 0 and holders[i - 1] == holders[i]:
                del holder_dates[i]
                del holders[i]
                continue
            if holders[i] != 0:
                continue
            # force liege to 0 while holder is 0
            start_date = holder_dates[i]
            j = bisect_left(liege_dates, start_date)
            if i < len(holders) - 1:
                end_date = holder_dates[i + 1]
                k = bisect_left(liege_dates, end_date)
            else:
                k = len(lieges)
            if (0 < k < len(lieges) and lieges[k - 1] != 0 and
                liege_dates[k] != end_date):
                liege_dates[j:k] = [start_date, end_date]
                lieges[j:k] = [0, lieges[k - 1]]
            else:
                liege_dates[j:k] = [start_date]
                lieges[j:k] = [0]
        for i in range(len(lieges) - 1, 0, -1):
            if lieges[i - 1] == lieges[i]:
                del liege_dates[i]
                del lieges[i]
        #if title in DEBUG_INSPECT_LIST:
        #    pprint(title)
        #    pprint(list(zip(holder_dates, holders)))
        #    pprint(list(zip(liege_dates, lieges)))
        title_holder_dates[title] = holder_dates
        title_holders[title] = holders
        title_liege_dates[title] = liege_dates
        title_lieges[title] = lieges
    if CHECK_DEAD_HOLDERS or CHECK_LIEGE_CONSISTENCY:
        if CHECK_DEAD_HOLDERS:
            title_dead_holders = []
        for title, holder_dates in sorted(title_holder_dates.items()):
            holders = title_holders[title]
            if CHECK_DEAD_HOLDERS:
                dead_holders = []
            for i, holder in enumerate(holders):
                if (CHECK_DEAD_HOLDERS and holder != 0 and
                    holder in char_death):
                    death = char_death[holder]
                    if i + 1 < len(holders):
                        if death < holder_dates[i + 1]:
                            dead_holders.append((death, holder_dates[i + 1]))
                    else:
                        dead_holders.append((death, None))
                if CHECK_LIEGE_CONSISTENCY and i + 1 < len(holders):
                    char_titles[holder][title] = tuple(holder_dates[i:i + 2])
            if CHECK_DEAD_HOLDERS and dead_holders:
                title_dead_holders.append((title, dead_holders))
                #if title in DEBUG_INSPECT_LIST:
                #    pprint(title)
                #    pprint(dead_holders)
    title_liege_errors = []
    for title, lieges in sorted(title_lieges.items()):
        errors = []
        liege_dates = title_liege_dates[title]
        for i, liege in enumerate(lieges):
            start_date = liege_dates[i]
            if liege == 0:
                continue
            if liege in title_holders:
                holder_dates = title_holder_dates[liege]
                holders = title_holders[liege]
            else:
                holder_dates = [(0, 0, 0)]
                holders = [0]
            holder_start = bisect(holder_dates, start_date) - 1
            if i < len(lieges) - 1:
                end_date = liege_dates[i + 1]
                holder_end = bisect_left(holder_dates, end_date)
            else:
                end_date = None
                holder_end = len(holders)
            for j in range(holder_start, holder_end):
                if holders[j] == 0:
                    if j == holder_start:
                        error_start = max(start_date, holder_dates[j])
                    else:
                        error_start = holder_dates[j]
                    if j < len(holders) - 1:
                        error_end = holder_dates[j + 1]
                        if end_date is not None:
                            error_end = min(end_date, error_end)
                    else:
                        error_end = end_date
                    if errors and errors[-1][1] == error_start:
                        errors[-1] = errors[-1][0], error_end
                    else:
                        errors.append((error_start, error_end))
        if errors:
            title_liege_errors.append((title, errors))
        #if title in DEBUG_INSPECT_LIST:
        #    pprint(title)
        #    pprint(errors)
    if CHECK_LIEGE_CONSISTENCY:
        liege_consistency_errors = []
        for char, titles in sorted(char_titles.items()):
            held_title_lieges = []
            for title, (start_date, end_date) in sorted(titles.items()):
                lieges = title_lieges[title]
                liege_dates = title_liege_dates[title]
                lo = bisect(liege_dates, start_date) - 1
                hi = bisect_left(liege_dates, end_date) - 1
                for i in range(lo, hi):
                    liege_start = liege_dates[i]
                    try:
                        liege_end = liege_dates[i + 1]
                    except IndexError:
                        liege_end = None
                    liege = lieges[i]
                    if liege == 0:
                        insort(held_title_lieges,
                               (liege_start, liege_end, liege, title, liege))
                        continue
                    if liege not in title_holders:
                        insort(held_title_lieges,
                               (liege_holder_start, liege_holder_end, 0,
                                title, liege))
                        continue
                    liege_holder_dates = title_holder_dates[liege]
                    liege_holders = title_holders[liege]
                    j = bisect(liege_holder_dates, liege_start) - 1
                    if liege_end is None:
                        k = len(liege_holders)
                    else:
                        k = bisect_left(liege_holder_dates, liege_end)
                    for l in range(j, k):
                        liege_holder_start = (liege_start if l == j else
                                              liege_holder_dates[l])
                        liege_holder_end = (liege_end if l + 1 == k else
                                            liege_holder_dates[l + 1])
                        liege_holder = liege_holders[l]
                        if liege_holder == char:
                            liege_holder = 0
                        insort(held_title_lieges,
                               (liege_holder_start, liege_holder_end,
                                liege_holder, title, liege))
            for i, item1 in enumerate(held_title_lieges):
                start1, end1, liege1, title1, liege_title1 = item1
                for item2 in held_title_lieges[i + 1:]:
                    start2, end2, liege2, title2, liege_title2 = item2
                    if ((end2 is None or start1 < end2) and
                        (end1 is None or start2 < end1) and liege1 != liege2):
                        start = max(start1, start2)
                        if end1 is None:
                            end = end2
                        elif end2 is None:
                            end = end1
                        else:
                            end = min(end1, end2)
                        if prune:
                            intersection = []
                            for a, b in dates_to_examine:
                                if start < b and (end is None or a < end):
                                    intersection.append((max(start, a),
                                                         min(end, b)
                                                         if end else b))
                            for s, e in intersection:
                                error = (char, s, e, liege1, title1,
                                    liege_title1, liege2, title2,
                                    liege_title2)
                                liege_consistency_errors.append(error)
                        else:
                            error = (char, start, end, liege1, title1,
                                liege_title1, liege2, title2, liege_title2)
                            liege_consistency_errors.append(error)
    if prune:
        for title, errors in reversed(title_liege_errors):
            for i in range(len(errors) - 1, -1, -1):
                # intersect this interval with the playable intervals,
                # and update, split, or remove errors[i] as necessary
                start, end = errors[i]
                intersection = []
                for a, b in dates_to_examine:
                    if start < b and (end is None or a < end):
                        intersection.append((max(start, a),
                                             min(end, b) if end else b))
                errors[i:i + 1] = intersection
            if not errors:
                title_liege_errors.remove((title, errors))
            #if title in DEBUG_INSPECT_LIST:
            #    pprint(title)
            #    pprint(errors)
        if CHECK_DEAD_HOLDERS:
            for title, dead_holders in reversed(title_dead_holders):
                for i in range(len(dead_holders) - 1, -1, -1):
                    start, end = dead_holders[i]
                    intersection = []
                    for a, b in dates_to_examine:
                        if start < b and (end is None or a < end):
                            intersection.append((max(start, a),
                                                 min(end, b) if end else b))
                    dead_holders[i:i + 1] = intersection
                if not dead_holders:
                    title_dead_holders.remove((title, dead_holders))
                #if title in DEBUG_INSPECT_LIST:
                #    pprint(title)
                #    pprint(dead_holders)
    if LANDED_TITLES_ORDER:
        title_liege_errors.sort(key=lambda x: landed_titles.index(x[0]))
        if CHECK_DEAD_HOLDERS:
            title_dead_holders.sort(key=lambda x: landed_titles.index(x[0]))
    else:
        title_liege_errors.sort(key=lambda x: (x[1][0][0],
                                               landed_titles.index(x[0])))
        if CHECK_DEAD_HOLDERS:
            title_dead_holders.sort(key=lambda x:
                                    (x[1][0][0], landed_titles.index(x[0])))

    with (rootpath / 'check_title_history.txt').open('w') as fp:
        print('Liege has no holder:', file=fp)
        if not title_liege_errors:
            print('\t(none)', file=fp)
        prev_region = None
        for title, errors in title_liege_errors:
            region = title_regions[title]
            if LANDED_TITLES_ORDER and region != prev_region:
                print('\t# {}'.format(region), file=fp)
            line = '\t{}: '.format(title)
            for i, error in enumerate(errors):
                line += '{}.{}.{}'.format(*error[0])
                if error[1] != get_next_day(error[0]):
                    if error[1] is None:
                        line += ' on'
                    else:
                        line += ' to {}.{}.{}'.format(*error[1])
                if i < len(errors) - 1:
                    line += ', '
            print(line, file=fp)
            prev_region = region
        if CHECK_DEAD_HOLDERS:
            print('Holder is dead:', file=fp)
            if not title_dead_holders:
                print('\t(none)', file=fp)
            prev_region = None
            for title, dead_holders in title_dead_holders:
                region = title_regions[title]
                if LANDED_TITLES_ORDER and region != prev_region:
                    print('\t# {}'.format(region), file=fp)
                line = '\t{}: '.format(title)
                for i, dead_holder in enumerate(dead_holders):
                    line += '{}.{}.{}'.format(*dead_holder[0])
                    if dead_holder[1] != get_next_day(dead_holder[0]):
                        if dead_holder[1] is None:
                            line += ' on'
                        else:
                            line += ' to {}.{}.{}'.format(*dead_holder[1])
                    if i < len(dead_holders) - 1:
                        line += ', '
                print(line, file=fp)
                prev_region = region
        if CHECK_LIEGE_CONSISTENCY:
            print('Liege inconsistency:', file=fp)
            if not liege_consistency_errors:
                print('\t(none)', file=fp)
            for item in liege_consistency_errors:
                (char, start, end, liege1, title1, liege_title1, liege2,
                 title2, liege_title2) = item
                line = '\t{}: '.format(char)
                line += '{}.{}.{}'.format(*start)
                if end != get_next_day(start):
                    if end is None:
                        line += ' on'
                    else:
                        line += ' to {}.{}.{}'.format(*end)
                line += ', {} ({}->{}) vs. {} ({}->{})'.format(liege1, title1,
                    liege_title1, liege2, title2, liege_title2)
                print(line, file=fp)

if __name__ == '__main__':
    main()
