#!/usr/bin/env python3

import bisect
import ck2parser
from pprint import pprint
from print_time import print_time

rootpath = ck2parser.rootpath
modpath = rootpath / 'SWMH-BETA/SWMH'

INSPECT_LIST = []

@print_time
def main():
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
        if title in INSPECT_LIST:
            pprint(title)
            pprint(list(zip(holder_dates, holders)))
            pprint(list(zip(liege_dates, lieges)))
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
        for i in range(len(lieges) - 1, -1, -1):
            if i > 0 and lieges[i - 1] == lieges[i]:
                del liege_dates[i]
                del lieges[i]
        if title in INSPECT_LIST:
            pprint(title)
            pprint(list(zip(holder_dates, holders)))
            pprint(list(zip(liege_dates, lieges)))
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
                    else:
                        error_end = end_date
                    if errors and errors[-1] == error_start:
                        errors[-1] = error_end
                    else:
                        errors.append(error_start)
                        errors.append(error_end)
        if errors:
            title_errors.append((title, errors))
    with (rootpath / 'check_title_history.txt').open('w') as fp:
        for title, errors in title_errors:
            line = title + ': '
            for i in range(0, len(errors), 2):
                line += '{}.{}.{}'.format(*errors[i])
                if errors[i + 1] is None:
                    line += ' on'
                else:
                    line += ' to {}.{}.{}'.format(*errors[i + 1])
                    if i + 2 < len(errors):
                        line += ', '
            print(line, file=fp)

if __name__ == '__main__':
    main()
