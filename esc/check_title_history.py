#!/usr/bin/env python3

from bisect import bisect_left, bisect, insort
from collections import defaultdict
from ck2parser import (rootpath, files, is_codename, Date, SimpleParser,
                       FullParser)
from pprint import pprint
from print_time import print_time

# DEBUG_INSPECT_LIST = ['c_javakheti']

CHECK_DEAD_HOLDERS = True # slow; most useful with PRUNE_UNEXECUTED_HISTORY
CHECK_LIEGE_CONSISTENCY = True

LANDED_TITLES_ORDER = True # if false, date order

PRUNE_UNEXECUTED_HISTORY = True # prune all after last playable start
PRUNE_IMPOSSIBLE_STARTS = True # implies PRUNE_UNEXECUTED_HISTORY
PRUNE_NONBOOKMARK_STARTS = False # implies PRUNE_IMPOSSIBLE_STARTS

modpaths = [rootpath / 'SWMH-BETA/SWMH']
# modpaths = [rootpath / 'CK2Plus/CK2Plus']

time_beginning = (float('-inf'),) * 3
time_end = (float('inf'),) * 3

def get_next_day(day):
    day = day[0], day[1], day[2] + 1
    if (day[2] == 29 and day[1] == 2 or
        day[2] == 31 and day[1] in (4, 6, 9, 11) or
        day[2] == 32 and day[1] in (1, 3, 5, 7, 8, 10, 12)):
        day = day[0], day[1] + 1, 1
    if day[1] == 13:
        day = day[0] + 1, 1, day[2]
    return day


def iv_to_str(begin, end):
    s = '{}.{}.{}'.format(*begin)
    if end != get_next_day(begin):
        if end == time_end:
            s += ' on'
        else:
            s += ' to {}.{}.{}'.format(*end)
    return s


@print_time
def main():
    parser = SimpleParser()
    landed_titles_index = {}
    title_regions = {}
    current_index = 0
    def recurse(tree, region='titular'):
        nonlocal current_index
        for n, v in tree:
            if is_codename(n.val):
                landed_titles_index[n.val] = current_index
                current_index += 1
                child_region = region
                if (region in ['e_null', 'e_placeholder'] or
                    (region == 'titular' and
                     any(is_codename(n2.val) for n2, _ in v))):
                    child_region = n.val
                title_regions[n.val] = child_region
                if region == 'titular':
                    child_region = n.val
                recurse(v, region=child_region)
    for _, tree in parser.parse_files('common/landed_titles/*', *modpaths):
        recurse(tree)
    prune = (PRUNE_UNEXECUTED_HISTORY or PRUNE_IMPOSSIBLE_STARTS or
             PRUNE_NONBOOKMARK_STARTS)
    if prune:
        if PRUNE_NONBOOKMARK_STARTS:
            dates_to_examine = []
        else:
            defines = parser.parse_file(next(files('common/defines.txt',
                                                   *modpaths)))
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
            dates_to_examine[:] = [(time_beginning, dates_to_examine[-1][1])]
        # e.g. [((867, 1, 1), (867, 1, 2)), ((1066, 9, 15), (1337, 1, 2))]
    title_holder_dates = {}
    title_holders = {}
    title_liege_dates = {}
    title_lieges = {}
    char_titles = defaultdict(dict)
    char_life = {}
    title_dead_holders = []
    if CHECK_DEAD_HOLDERS:
        for _, tree in parser.parse_files('history/characters/*', *modpaths):
            for n, v in tree:
                birth = next((n2.val for n2, v2 in v
                              if (isinstance(n2, Date) and
                                  'birth' in v2.dictionary)), time_end)
                death = next((n2.val for n2, v2 in v
                              if (isinstance(n2, Date) and
                                  'death' in v2.dictionary)), time_end)
                if birth <= death:
                    char_life[n.val] = birth, death
    for path, tree in parser.parse_files('history/titles/*', *modpaths):
        title = path.stem
        if not len(tree) > 0 or title not in landed_titles_index:
            continue
        holder_dates = [time_beginning]
        holders = [0]
        liege_dates = [time_beginning]
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
        # if title in DEBUG_INSPECT_LIST:
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
                k = bisect_left(liege_dates, end_date, lo=j)
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
        # if title in DEBUG_INSPECT_LIST:
        #    pprint(title)
        #    pprint(list(zip(holder_dates, holders)))
        #    pprint(list(zip(liege_dates, lieges)))
        title_holder_dates[title] = holder_dates
        title_holders[title] = holders
        title_liege_dates[title] = liege_dates
        title_lieges[title] = lieges
    if CHECK_DEAD_HOLDERS or CHECK_LIEGE_CONSISTENCY:
        for title, holder_dates in title_holder_dates.items():
            holders = title_holders[title]
            dead_holders = []
            for i, holder in enumerate(holders):
                if holder != 0:
                    if CHECK_DEAD_HOLDERS:
                        birth, death = char_life.get(holder,
                                                     (time_end, time_end))
                        if i + 1 < len(holders):
                            if holder_dates[i] < birth:
                                begin = holder_dates[i]
                                end = min(birth, holder_dates[i + 1])
                                if (dead_holders and
                                    dead_holders[-1][1] == begin):
                                    dead_holders[-1] = dead_holders[-1][0], end
                                else:
                                    dead_holders.append((begin, end))
                            if death < holder_dates[i + 1]:
                                begin = max(death, holder_dates[i])
                                end = holder_dates[i + 1]
                                if (dead_holders and
                                    dead_holders[-1][1] == begin):
                                    dead_holders[-1] = dead_holders[-1][0], end
                                else:
                                    dead_holders.append((begin, end))
                        elif death != time_end:
                            begin = max(death, holder_dates[i])
                            if dead_holders and dead_holders[-1][1] == begin:
                                dead_holders[-1] = (dead_holders[-1][0],
                                                    time_end)
                            else:
                                dead_holders.append((begin, time_end))
                    if CHECK_LIEGE_CONSISTENCY and i + 1 < len(holders):
                        begin, end = holder_dates[i:i + 2]
                        char_titles[holder][title] = begin, end
            if dead_holders:
                title_dead_holders.append((title, dead_holders))
            # if CHECK_DEAD_HOLDERS and title in DEBUG_INSPECT_LIST:
            #    pprint(title)
            #    pprint(dead_holders)
    title_liege_errors = []
    for title, lieges in title_lieges.items():
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
                holder_dates = [time_beginning]
                holders = [0]
            holder_start = bisect(holder_dates, start_date) - 1
            if i < len(lieges) - 1:
                end_date = liege_dates[i + 1]
                holder_end = bisect_left(holder_dates, end_date,
                                         lo=holder_start)
            else:
                end_date = time_end
                holder_end = len(holders)
            for j in range(holder_start, holder_end):
                if holders[j] == 0:
                    if j == holder_start:
                        error_start = max(start_date, holder_dates[j])
                    else:
                        error_start = holder_dates[j]
                    if j < len(holders) - 1:
                        error_end = min(end_date, holder_dates[j + 1])
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
        for char, titles in char_titles.items():
            held_title_lieges = []
            for title, (start_date, end_date) in titles.items():
                # if char == 83200 and title == 'd_leinster':
                #     pdb.set_trace()
                lieges = title_lieges[title]
                liege_dates = title_liege_dates[title]
                lo = bisect(liege_dates, start_date) - 1
                hi = bisect_left(liege_dates, end_date, lo=lo)
                for i in range(lo, hi):
                    liege_start = start_date if i == lo else liege_dates[i]
                    liege_end = end_date if i + 1 == hi else liege_dates[i + 1]
                    liege = lieges[i]
                    if liege == 0 or liege not in title_holders:
                        insort(held_title_lieges,
                               (liege_start, liege_end, 0, title, liege))
                        continue
                    liege_holder_dates = title_holder_dates[liege]
                    liege_holders = title_holders[liege]
                    j = bisect(liege_holder_dates, liege_start) - 1
                    k = bisect_left(liege_holder_dates, liege_end, lo=j)
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
                    if start1 < end2 and start2 < end1 and liege1 != liege2:
                        start = max(start1, start2)
                        end = min(end1, end2)
                        if prune:
                            intersection = []
                            for a, b in dates_to_examine:
                                if start < b and a < end:
                                    intersection.append((max(start, a),
                                                         min(end, b)))
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
                    if start < b and a < end:
                        intersection.append((max(start, a), min(end, b)))
                errors[i:i + 1] = intersection
            if not errors:
                title_liege_errors.remove((title, errors))
            #if title in DEBUG_INSPECT_LIST:
            #    pprint(title)
            #    pprint(errors)
        for title, dead_holders in reversed(title_dead_holders):
            for i in range(len(dead_holders) - 1, -1, -1):
                start, end = dead_holders[i]
                intersection = []
                for a, b in dates_to_examine:
                    if start < b and a < end:
                        intersection.append((max(start, a), min(end, b)))
                dead_holders[i:i + 1] = intersection
            if not dead_holders:
                title_dead_holders.remove((title, dead_holders))
            # if CHECK_DEAD_HOLDERS and title in DEBUG_INSPECT_LIST:
            #    pprint(title)
            #    pprint(dead_holders)
    if LANDED_TITLES_ORDER:
        sort_key = lambda x: landed_titles_index[x[0]]
    else:
        sort_key = lambda x: (x[1][0][0], landed_titles_index[x[0]])
    title_liege_errors.sort(key=sort_key)
    title_dead_holders.sort(key=sort_key)
    liege_consistency_errors.sort()
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
            line += ', '.join(iv_to_str(*iv) for iv in errors)
            print(line, file=fp)
            prev_region = region
        if CHECK_DEAD_HOLDERS:
            print('Holder not alive:', file=fp)
            if not title_dead_holders:
                print('\t(none)', file=fp)
            prev_region = None
            for title, dead_holders in title_dead_holders:
                region = title_regions[title]
                if LANDED_TITLES_ORDER and region != prev_region:
                    print('\t# {}'.format(region), file=fp)
                line = '\t{}: '.format(title)
                line += ', '.join(iv_to_str(*iv) for iv in dead_holders)
                print(line, file=fp)
                prev_region = region
        if CHECK_LIEGE_CONSISTENCY:
            print('Liege inconsistency:', file=fp)
            if not liege_consistency_errors:
                print('\t(none)', file=fp)
            for char, start, end, *data in liege_consistency_errors:
                line = ('\t{}: {}, {} ({}->{}) vs. {} ({}->{})'
                        .format(char, iv_to_str(start, end), *data))
                print(line, file=fp)

if __name__ == '__main__':
    main()
