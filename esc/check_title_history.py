#!/usr/bin/env python3

import bisect
import ck2parser
from pprint import pprint
from print_time import print_time

rootpath = ck2parser.rootpath
modpath = rootpath / 'SWMH-BETA/SWMH'

#DEBUG_INSPECT_LIST = ['b_stenkyrka']

LANDED_TITLES_ORDER = False # if false, date order
PRUNE_IMPOSSIBLE_STARTS = True
PRUNE_NONBOOKMARK_STARTS = True # implies PRUNE_IMPOSSIBLE_STARTS

@print_time
def main():
    titles = []
    def recurse(tree):
        for n, v in tree:
            if ck2parser.is_codename(n.val):
                titles.append(n.val)
                recurse(v)
    for _, tree in ck2parser.parse_files('common/landed_titles/*', modpath):
        recurse(tree)
    def next_day(day):
        next_day = day[0], day[1], day[2] + 1
        if (day[2] == 28 and day[1] == 2 or
            day[2] == 30 and day[1] in (4, 6, 9, 11) or
            day[2] == 31 and day[1] in (1, 3, 5, 7, 8, 10, 12)):
            next_day = next_day[0], next_day[1] + 1, 1
        if next_day[1] == 13:
            next_day = next_day[0] + 1, 1, next_day[2]
        return next_day
    if PRUNE_IMPOSSIBLE_STARTS or PRUNE_NONBOOKMARK_STARTS:
        if PRUNE_NONBOOKMARK_STARTS:
            playables = []
        else:
            _, defines = next(ck2parser.parse_files('common/defines.txt',
                                                    modpath))
            playables = [(defines['start_date'].val,
                          next_day(defines['last_start_date'].val))]
        for _, tree in ck2parser.parse_files('common/bookmarks/*', modpath):
            for _, v in tree:
                date = v['date'].val
                if not any(a <= date < b for a, b in playables):
                    interval = date, next_day(date)
                    bisect.insort(playables, interval)
        for i in range(len(playables) - 1, 0, -1):
            if playables[i - 1][1] == playables[i][0]:
                playables[i - 1] = playables[i - 1][0], playables[i][1]
                del playables[i]
        # e.g. [((867, 1, 1), (867, 1, 2)), ((1066, 9, 15), (1337, 1, 2))]
    title_holder_dates = {}
    title_holders = {}
    title_liege_dates = {}
    title_lieges = {}
    for path, tree in ck2parser.parse_files('history/titles/*', modpath):
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
                    i = bisect.bisect_left(holder_dates, date)
                    if i == len(holders) or holder_dates[i] != date:
                        holder = 0 if v2.val == '-' else int(v2.val)
                        holder_dates.insert(i, date)
                        holders.insert(i, holder)
                elif n2.val == 'liege':
                    i = bisect.bisect_left(liege_dates, date)
                    if i == len(lieges) or liege_dates[i] != date:
                        liege = 0 if v2.val in ('0', title) else v2.val
                        liege_dates.insert(i, date)
                        lieges.insert(i, liege)
        #if title in DEBUG_INSPECT_LIST:
        #    pprint(title)
        #    pprint(list(zip(holder_dates, holders)))
        #    pprint(list(zip(liege_dates, lieges)))
        for i in range(len(holders) - 1, -1, -1):
            if i > 0 and holders[i - 1] == holders[i]:
                del holder_dates[i]
                del holders[i]
                continue
            if holders[i] != 0:
                continue
            start_date = holder_dates[i]
            j = bisect.bisect_left(liege_dates, start_date)
            if i < len(holders) - 1:
                end_date = holder_dates[i + 1]
                k = bisect.bisect_left(liege_dates, end_date)
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
    title_errors = []
    for title, liege_dates in sorted(title_liege_dates.items()):
        errors = []
        lieges = title_lieges[title]
        for i in range(len(lieges)):
            start_date = liege_dates[i]
            liege = lieges[i]
            if liege == 0:
                continue
            if liege in title_holders:
                holder_dates = title_holder_dates[liege]
                holders = title_holders[liege]
            else:
                holder_dates = [(0, 0, 0)]
                holders = [0]
            holder_start = bisect.bisect(holder_dates, start_date) - 1
            if i < len(lieges) - 1:
                end_date = liege_dates[i + 1]
                holder_end = bisect.bisect_left(holder_dates, end_date)
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
            title_errors.append((title, errors))
        #if title in DEBUG_INSPECT_LIST:
        #    pprint(title)
        #    pprint(errors)
    if PRUNE_IMPOSSIBLE_STARTS:
        for title, errors in reversed(title_errors):
            for i in range(len(errors) - 1, -1, -1):
                # intersect this interval with the playable intervals,
                # and update, split, or remove errors[i] as necessary
                start, end = errors[i]
                intersection = []
                for a, b in playables:
                    if start < b and (end is None or a < end):
                        intersection.append((max(start, a),
                                             min(end, b) if end else b))
                errors[i:i + 1] = intersection
            if not errors:
                title_errors.remove((title, errors))
            #if title in DEBUG_INSPECT_LIST:
            #    pprint(title)
            #    pprint(errors)
    if LANDED_TITLES_ORDER:
        title_errors.sort(key=lambda x: titles.index(x[0]))
    else:
        title_errors.sort(key=lambda x: (x[1][0][0], titles.index(x[0])))
    with (rootpath / 'check_title_history.txt').open('w') as fp:
        for title, errors in title_errors:
            line = title + ': '
            for i, error in enumerate(errors):
                line += '{}.{}.{}'.format(*error[0])
                if error[1] != next_day(error[0]):
                    if error[1] is None:
                        line += ' on'
                    else:
                        line += ' to {}.{}.{}'.format(*error[1])
                if i < len(errors) - 1:
                    line += ', '
            print(line, file=fp)

if __name__ == '__main__':
    main()
