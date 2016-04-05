#!/usr/bin/env python3

# a thought:
#     130: 1066.1.6 to 1066.10.14
#         0 (d_canterbury<-c_kent,c_surrey)
#         122 (k_england<-c_essex,c_middlesex,d_canterbury)
#         5644 (d_hereford<-c_bucks,c_hertford)

from collections import defaultdict, namedtuple
from operator import attrgetter
import intervaltree
from intervaltree import Interval, IntervalTree
from intervaltree.node import Node
from ck2parser import (rootpath, files, is_codename, Date as ASTDate,
                       SimpleParser, FullParser)
from print_time import print_time


CHECK_DEAD_HOLDERS = True # slow; most useful with PRUNE_UNEXECUTED_HISTORY
CHECK_LIEGE_CONSISTENCY = True

LANDED_TITLES_ORDER = True # if false, date order

PRUNE_UNEXECUTED_HISTORY = True # prune all after last playable start
PRUNE_IMPOSSIBLE_STARTS = True # implies PRUNE_UNEXECUTED_HISTORY
PRUNE_NONBOOKMARK_STARTS = False # implies PRUNE_IMPOSSIBLE_STARTS

modpaths = [rootpath / 'SWMH-BETA/SWMH']
# modpaths = [rootpath / 'CK2Plus/CK2Plus']

class Date(namedtuple('Date', ['y', 'm', 'd'])):

    def __str__(self):
        return '{}.{}.{}'.format(*self)

    __slots__ = ()


timeline = Interval(Date(float('-inf'), float('-inf'), float('-inf')),
                    Date(float('inf'), float('inf'), float('inf')))

# monkey patch Node.pop_greatest_child to fix issue 41
# https://github.com/chaimleib/intervaltree/issues/41
def pop_greatest_child(self):
    if self.right_node:
        greatest_child, self[1] = self[1].pop_greatest_child()
        new_self = self.rotate()
        for iv in set(new_self.s_center):
            if iv.contains_point(greatest_child.x_center):
                new_self.s_center.remove(iv)
                greatest_child.add(iv)
        return (greatest_child,
                new_self if new_self.s_center else new_self.prune())
    x_centers = set(iv.end for iv in self.s_center)
    x_centers.remove(max(x_centers))
    x_centers.add(self.x_center)
    new_x_center = max(x_centers)
    child = Node(new_x_center, (iv for iv in self.s_center
                                if iv.contains_point(new_x_center)))
    self.s_center -= child.s_center
    return child, self if self.s_center else self[0]


Node.pop_greatest_child = pop_greatest_child


def get_next_day(day):
    day = Date(y=day.y, m=day.m, d=day.d + 1)
    if (day.d == 29 and day.m == 2 or
        day.d == 31 and day.m in (4, 6, 9, 11) or
        day.d == 32 and day.m in (1, 3, 5, 7, 8, 10, 12)):
        day = Date(y=day.y, m=day.m + 1, d=1)
        if day.m == 13:
            day = Date(y=day.y + 1, m=1, d=day.d)
    return day


def iv_to_str(iv):
    if iv.end == timeline.end:
         return '{} on'.format(iv.begin)
    if iv.end == get_next_day(iv.begin):
        return str(iv.begin)
    return '{} to {}'.format(iv.begin, iv.end)


def prune_tree(ivt, date_filter, pred=None, data_iv=True):
    def normalize_data(iv, islower):
        if islower:
            return iv.data[:1] + (filter_iv.begin,) + iv.data[2:]
        return (filter_iv.end,) + iv.data[1:]
    for filter_iv in date_filter:
        if pred is None or pred(filter_iv):
            ivt.chop(filter_iv.begin, filter_iv.end,
                     normalize_data if data_iv else None)


@print_time
def main():
    parser = SimpleParser()
    parser.moddirs = [rootpath / 'SWMH-BETA/SWMH']
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
    for _, tree in parser.parse_files('common/landed_titles/*'):
        recurse(tree)
    date_filter = IntervalTree()
    if (PRUNE_UNEXECUTED_HISTORY or PRUNE_IMPOSSIBLE_STARTS or
        PRUNE_NONBOOKMARK_STARTS):
        date_filter.add(timeline)
        last_start_date = timeline.begin
        for _, tree in parser.parse_files('common/bookmarks/*', *modpaths):
            for _, v in tree:
                date = Date(*v['date'].val)
                date_filter.chop(date, get_next_day(date))
                last_start_date = max(date, last_start_date)
        if not PRUNE_NONBOOKMARK_STARTS:
            defines = parser.parse_file(next(files('common/defines.txt',
                                                   *modpaths)))
            first = Date(*defines['start_date'].val)
            last = Date(*defines['last_start_date'].val)
            date_filter.chop(first, get_next_day(last))
            last_start_date = max(last, last_start_date)
            if not PRUNE_IMPOSSIBLE_STARTS:
                date_filter.clear()
                date_filter.addi(get_next_day(last_start_date), timeline.end)
    title_holders = defaultdict(IntervalTree)
    title_lieges = defaultdict(IntervalTree)
    char_titles = defaultdict(IntervalTree)
    char_life = {}
    title_dead_holders = []
    if CHECK_DEAD_HOLDERS:
        for _, tree in parser.parse_files('history/characters/*'):
            for n, v in tree:
                birth = next((Date(*n2.val) for n2, v2 in v
                              if (isinstance(n2, ASTDate) and
                                  'birth' in v2.dictionary)), timeline.end)
                death = next((Date(*n2.val) for n2, v2 in v
                              if (isinstance(n2, ASTDate) and
                                  'death' in v2.dictionary)), timeline.end)
                if birth <= death:
                    char_life[n.val] = birth, death
    for path, tree in parser.parse_files('history/titles/*'):
        title = path.stem
        if not len(tree) > 0 or title not in landed_titles_index:
            continue
        holders = [(timeline.begin, 0)]
        lieges = [(timeline.begin, 0)]
        for n, v in sorted(tree, key=attrgetter('key.val')):
            date = Date(*n.val)
            for n2, v2 in v:
                if n2.val == 'holder':
                    holder = 0 if v2.val == '-' else int(v2.val)
                    if holders[-1][1] != holder:
                        if holders[-1][0] == date:
                            holders[-1] = date, holder
                        else:
                            holders.append((date, holder))
                elif n2.val == 'liege':
                    liege = 0 if v2.val in ('0', '-', title) else v2.val
                    if lieges[-1][1] != liege:
                        if lieges[-1][0] == date:
                            lieges[-1] = date, liege
                        else:
                            lieges.append((date, liege))
        dead_holders = []
        # if title == 'c_ostfriesland':
        #     import pdb; pdb.set_trace()
        for i, (begin, holder) in enumerate(holders):
            try:
                end = holders[i + 1][0]
            except IndexError:
                end = timeline.end
            if CHECK_DEAD_HOLDERS and holder != 0:
                birth, death = char_life.get(holder,
                                             (timeline.end, timeline.end))
                if begin < birth or death < end:
                    error_begin = death if birth <= begin < death else begin
                    error_end = birth if begin < birth <= end else end
                    if dead_holders and dead_holders[-1][1] == error_begin:
                        dead_holders[-1] = dead_holders[-1][0], error_end
                    else:
                        dead_holders.append((error_begin, error_end))
            title_holders[title][begin:end] = holder
            if holder != 0:
                char_titles[holder][begin:end] = title
        for i, (begin, liege) in enumerate(lieges):
            try:
                end = lieges[i + 1][0]
            except IndexError:
                end = timeline.end
            title_lieges[title][begin:end] = liege
        if dead_holders:
            dead_holders = IntervalTree(Interval(begin, end, (begin, end))
                                        for begin, end in dead_holders)
            title_dead_holders.append((title, dead_holders))
    title_liege_errors = []
    for title, lieges in title_lieges.items():
        errors = []
        for liege_begin, liege_end, liege in lieges:
            if liege == 0:
                continue
            if liege not in title_holders:
                title_holders[liege][timeline.begin:timeline.end] = 0
            holders = title_holders[liege][liege_begin:liege_end]
            for holder_begin, holder_end, holder in holders:
                if holder == 0:
                    begin = max(liege_begin, holder_begin)
                    end = min(liege_end, holder_end)
                    if errors and errors[-1][1] == begin:
                        errors[-1] = errors[-1][0], end
                    else:
                        errors.append((begin, end))
        # not an error if title is also unheld
        if errors:
            errors = IntervalTree(Interval(begin, end, (begin, end))
                                        for begin, end in errors)
            prune_tree(errors, title_holders[title], lambda x: x.data == 0)
            if errors:
                title_liege_errors.append((title, errors))
    if CHECK_LIEGE_CONSISTENCY:
        liege_consistency_errors = []
        for char, titles in char_titles.items():
            liege_chars = IntervalTree()
            for holder_begin, holder_end, title in titles:
                lieges = title_lieges[title][holder_begin:holder_end]
                for liege_begin, liege_end, liege in lieges:
                    liege_begin = max(liege_begin, holder_begin)
                    liege_end = min(liege_end, holder_end)
                    if liege not in title_holders:
                        liege_chars[liege_begin:liege_end] = 0, title, liege
                        continue
                    liege_holders = title_holders[liege][liege_begin:liege_end]
                    for begin, end, liege_holder in liege_holders:
                        begin = max(begin, liege_begin)
                        end = min(end, liege_end)
                        if liege_holder == char:
                            liege_holder = 0
                        liege_chars[begin:end] = liege_holder, title, liege
            prune_tree(liege_chars, date_filter, data_iv=False)
            if liege_chars:
                liege_chars = sorted(liege_chars)
                low = liege_chars[0]
                for high in liege_chars[1:]:
                    # overlapping different-liege-holder
                    if high.begin < low.end and low.data[0] != high.data[0]:
                        error = ((char, high.begin, min(low.end, high.end)) +
                                 low.data + high.data)
                        liege_consistency_errors.append(error)
                    low = high
    if date_filter:
        for title, errors in reversed(title_liege_errors):
            prune_tree(errors, date_filter)
            if not errors:
                title_liege_errors.remove((title, errors))
        for title, dead_holders in reversed(title_dead_holders):
            prune_tree(dead_holders, date_filter)
            if not dead_holders:
                title_dead_holders.remove((title, dead_holders))
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
            line += ', '.join(iv_to_str(iv) for iv in sorted(errors))
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
                line += ', '.join(iv_to_str(iv) for iv in sorted(dead_holders))
                print(line, file=fp)
                prev_region = region
        if CHECK_LIEGE_CONSISTENCY:
            print('Liege inconsistency:', file=fp)
            if not liege_consistency_errors:
                print('\t(none)', file=fp)
            for char, start, end, *data in liege_consistency_errors:
                line = ('\t{}: {}, {} ({}->{}) vs. {} ({}->{})'
                        .format(char, iv_to_str(Interval(start, end)), *data))
                print(line, file=fp)


if __name__ == '__main__':
    main()
