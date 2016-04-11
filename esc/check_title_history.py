#!/usr/bin/env python3

from collections import defaultdict, namedtuple
from operator import attrgetter
from intervaltree import Interval, IntervalTree
from ck2parser import (rootpath, vanilladir, is_codename, Date as ASTDate,
                       SimpleParser, FullParser)
from print_time import print_time

CHECK_DEAD_HOLDERS = True # slow; most useful with PRUNE_UNEXECUTED_HISTORY
CHECK_LIEGE_CONSISTENCY = True

LANDED_TITLES_ORDER = True # if false, date order

PRUNE_UNEXECUTED_HISTORY = True # prune all after last playable start
PRUNE_IMPOSSIBLE_STARTS = False # implies PRUNE_UNEXECUTED_HISTORY
PRUNE_NONBOOKMARK_STARTS = False # implies PRUNE_IMPOSSIBLE_STARTS
PRUNE_ALL_BUT_DATE = None # overrides above three
# PRUNE_ALL_BUT_DATE = 1066, 9, 15 # overrides above three

# PRUNE_ALL_BUT_REGION = 'e_britannia'
PRUNE_ALL_BUT_REGION = None

FORMAT_TITLE_HISTORY = False
CLEANUP_TITLE_HISTORY = False # overrides previous


class Date(namedtuple('Date', ['y', 'm', 'd'])):

    def __str__(self):
        return '{}.{}.{}'.format(*self)

    def get_next_day(self):
        y, m, d = self.y, self.m, self.d + 1
        if (d == 29 and m == 2 or
            d == 31 and m in (4, 6, 9, 11) or
            d == 32 and m in (1, 3, 5, 7, 8, 10, 12)):
            m, d = m + 1, 1
            if m == 13:
                y, m = y + 1, 1
        return Date(y, m, d)

Date.EARLIEST = Date(float('-inf'), float('-inf'), float('-inf'))
Date.LATEST = Date(float('inf'), float('inf'), float('inf'))


class Title:
    # ['holder', 'liege', 'law', 'de_jure_liege', 'vice_royalty',
    #  'historical_nomad', 'holding_dynasty', 'active', 'set_global_flag',
    #  'pentarch', 'set_tribute_suzerain', 'clear_tribute_suzerain',
    #  'conquest_culture', 'effect', 'clr_global_flag, 'reset_adjective,
    #  'reset_name, 'name, 'adjective']
    def __init__(self, djl):
        self.attr = {k: [(Date.EARLIEST, v)] for k, v in [
            ('holder', 0),
            ('liege', 0),
            ('de_jure_liege', djl),
            ('vice_royalty', 'no'),
            ('historical_nomad', 'no'),
            ('holding_dynasty', 0),
            ('active', 'yes'),
            ('pentarch', 0),
            ('conquest_culture', 0),
            ('name', ''),
            ('adjective', ''),
            ('suzerain', 0)
        ]}
        self.history = defaultdict(list)

# for monkey patching Node.pop_greatest_child to fix issue 41
# https://github.com/chaimleib/intervaltree/issues/41
def intervaltree_patch_issue_41():
    from intervaltree.node import Node
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

def iv_to_str(iv, end=None):
    if end is not None:
        iv = iv, end
    if iv[1] == Date.LATEST:
        s = '{} on'.format(iv[0])
    elif iv[1] == iv[0].get_next_day():
        s = str(iv[0])
    else:
        s = '{} to {}'.format(iv[0], iv[1])
    if len(iv) > 2 and iv[2] is not None:
        s += ' ({})'.format(iv[2])
    return s

def title_tier(title):
    return 'bcdke'.index(title[0])

def prune_tree(ivt, date_filter, pred=None):
    for filter_iv in date_filter:
        if pred is None or pred(filter_iv):
            ivt.chop(filter_iv.begin, filter_iv.end)

@print_time
def main():
    intervaltree_patch_issue_41()
    simple_parser = SimpleParser()
    simple_parser.moddirs = [rootpath / 'SWMH-BETA/SWMH']
    if FORMAT_TITLE_HISTORY and not CLEANUP_TITLE_HISTORY:
        history_parser = FullParser()
        history_parser.moddirs = [rootpath / 'SWMH-BETA/SWMH']
    else:
        history_parser = simple_parser
    history_parser.no_fold_to_depth = 0
    landed_titles_index = {0: -1}
    title_djls = {}
    titles = {}
    current_index = 0
    def recurse(tree, stack=[]):
        nonlocal current_index
        for n, v in tree:
            if is_codename(n.val):
                titles[n.val] = Title(stack[-1] if stack else 0)
                landed_titles_index[n.val] = current_index
                current_index += 1
                stack.append(n.val)
                title_djls[n.val] = stack.copy()
                recurse(v, stack=stack)
                stack.pop()
    for _, tree in simple_parser.parse_files('common/landed_titles/*'):
        recurse(tree)
    date_filter = IntervalTree()
    if PRUNE_ALL_BUT_DATE is not None:
        date = Date(*PRUNE_ALL_BUT_DATE)
        date_filter.addi(Date.EARLIEST, date)
        date_filter.addi(date.get_next_day(), Date.LATEST)
    elif (PRUNE_UNEXECUTED_HISTORY or PRUNE_IMPOSSIBLE_STARTS or
        PRUNE_NONBOOKMARK_STARTS):
        date_filter.addi(Date.EARLIEST, Date.LATEST)
        last_start_date = Date.EARLIEST
        for _, tree in simple_parser.parse_files('common/bookmarks/*'):
            for _, v in tree:
                date = Date(*v['date'].val)
                date_filter.chop(date, date.get_next_day())
                last_start_date = max(date, last_start_date)
        if not PRUNE_NONBOOKMARK_STARTS:
            defines = next(simple_parser.parse_files('common/defines.txt'))[1]
            first = Date(*defines['start_date'].val)
            last = Date(*defines['last_start_date'].val)
            date_filter.chop(first, last.get_next_day())
            last_start_date = max(last, last_start_date)
            if not PRUNE_IMPOSSIBLE_STARTS:
                date_filter.clear()
                date_filter.addi(last_start_date.get_next_day(), Date.LATEST)
    title_holders = defaultdict(IntervalTree)
    title_lieges = defaultdict(IntervalTree)
    title_lte_tier = []
    char_titles = defaultdict(IntervalTree)
    char_life = {}
    title_dead_holders = []
    if CHECK_DEAD_HOLDERS:
        for _, tree in simple_parser.parse_files('history/characters/*'):
            for n, v in tree:
                birth = next((Date(*n2.val) for n2, v2 in v
                              if (isinstance(n2, ASTDate) and
                                  'birth' in v2.dictionary)), Date.LATEST)
                death = next((Date(*n2.val) for n2, v2 in v
                              if (isinstance(n2, ASTDate) and
                                  'death' in v2.dictionary)), Date.LATEST)
                if birth <= death:
                    char_life[n.val] = birth, death
    for path, tree in history_parser.parse_files('history/titles/*'):
        title = path.stem
        tier = title_tier(title)
        if not len(tree) > 0 or title not in landed_titles_index:
            if (title in landed_titles_index and
                not (vanilladir / 'history/titles' / path.name).exists()):
                if FORMAT_TITLE_HISTORY or CLEANUP_TITLE_HISTORY:
                    path.unlink()
                else:
                    print('unnecessary blank? {}'.format(path.name))
            continue
        if FORMAT_TITLE_HISTORY and not CLEANUP_TITLE_HISTORY:
            with path.open('w', encoding='cp1252', newline='\r\n') as f:
                f.write(tree.str(history_parser))
        for n, v in sorted(tree, key=attrgetter('key.val')):
            date = Date(*n.val)
            for n2, v2 in v:
                if n2.val in ('law', 'set_global_flag', 'clr_global_flag',
                              'effect'):
                    titles[title].history[date].append((n2.val, v2))
                    continue
                attr_vals, value = None, None
                if n2.val in ('holder', 'liege'):
                    if v2.val in ('0', '-', title):
                        value = 0
                elif n2.val == 'set_tribute_suzerain':
                    attr_vals = titles[title].attr['suzerain']
                    try:
                        value = v2['who'], v2['percentage']
                    except KeyError:
                        continue
                elif n2.val == 'clear_tribute_suzerain':
                    attr_vals = titles[title].attr['suzerain']
                    value = 0
                    if attr_vals[-1][1] == 0 or attr_vals[-1][1][0] != v2.val:
                        continue
                elif n2.val in ('reset_adjective', 'reset_name'):
                    if v2.val != 'yes':
                        continue
                    attr_vals = titles[title].attr[n2.val[6:]]
                    value = ''
                if attr_vals is None:
                    attr_vals = titles[title].attr[n2.val]
                if value is None:
                    value = v2.val
                if attr_vals[-1][0] == date:
                    attr_vals[-1] = date, value
                elif attr_vals[-1][1] != value:
                    attr_vals.append((date, value))
        dead_holders = []
        # if title == 'c_ostfriesland':
        #     import pdb; pdb.set_trace()
        holders = titles[title].attr['holder']
        for i, (begin, holder) in enumerate(holders):
            try:
                end = holders[i + 1][0]
            except IndexError:
                end = Date.LATEST
            if CHECK_DEAD_HOLDERS and holder != 0:
                birth, death = char_life.get(holder,
                                             (Date.LATEST, Date.LATEST))
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
        lte_tier = IntervalTree()
        lieges = titles[title].attr['liege']
        for i, (begin, liege) in enumerate(lieges):
            try:
                end = lieges[i + 1][0]
            except IndexError:
                end = Date.LATEST
            if liege != 0 and title_tier(liege) <= tier:
                lte_tier[begin:end] = liege
            title_lieges[title][begin:end] = liege
        if lte_tier:
            title_lte_tier.append((title, lte_tier))
        if dead_holders:
            dead_holders = IntervalTree.from_tuples(dead_holders)
            title_dead_holders.append((title, dead_holders))
    title_liege_errors = []
    for title, lieges in title_lieges.items():
        errors = []
        for liege_begin, liege_end, liege in lieges:
            if liege == 0:
                continue
            if liege not in title_holders:
                title_holders[liege][Date.EARLIEST:Date.LATEST] = 0
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
            errors = IntervalTree.from_tuples(errors)
            prune_tree(errors, title_holders[title], lambda x: x.data == 0)
            if errors:
                title_liege_errors.append((title, errors))
    if CHECK_LIEGE_CONSISTENCY:
        liege_consistency_unamb = defaultdict(dict)
        liege_consistency_amb = defaultdict(dict)
        for char, titles in char_titles.items():
            liege_chars = IntervalTree()
            for holder_begin, holder_end, title in titles:
                # if char == 71823 and title == 'c_roma':
                #     import pdb; pdb.set_trace()
                lieges = title_lieges[title][holder_begin:holder_end]
                for liege_begin, liege_end, liege in lieges:
                    liege_begin = max(liege_begin, holder_begin)
                    liege_end = min(liege_end, holder_end)
                    if liege not in title_holders:
                        liege_chars[liege_begin:liege_end] = 0, liege, title
                        continue
                    liege_holders = title_holders[liege][liege_begin:liege_end]
                    for begin, end, liege_holder in liege_holders:
                        begin = max(begin, liege_begin)
                        end = min(end, liege_end)
                        if liege == title:
                            liege_holder = 0
                        elif liege_holder == char:
                            continue
                        liege_chars[begin:end] = liege_holder, liege, title
            prune_tree(liege_chars, date_filter)
            if liege_chars:
                liege_chars.split_overlaps()
                items = defaultdict(
                    lambda: defaultdict(lambda: defaultdict(list)))
                for begin, end, (liege_holder, liege, title) in liege_chars:
                    items[(begin, end)][liege_holder][liege].append(title)
                for iv, liege_holders in items.items():
                    if len(liege_holders) > 1:
                        if (PRUNE_ALL_BUT_REGION and
                            all(PRUNE_ALL_BUT_REGION not in
                                title_djls.get(title, ())
                                for _, ls in liege_holders.items()
                                for l in ls) and
                            all(PRUNE_ALL_BUT_REGION not in
                                title_djls.get(title, ())
                                for _, ls in liege_holders.items()
                                for _, ts in ls.items() for t in ts)):
                            continue
                        tiers = [max(title_tier(title)
                                     for _, titles in lieges.items()
                                     for title in titles)
                                 for _, lieges in liege_holders.items()]
                        if tiers.count(max(tiers)) == 1:
                            which_dict = liege_consistency_unamb
                        else:
                            which_dict = liege_consistency_amb
                        which_dict[char][iv] = liege_holders
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
    title_lte_tier.sort(key=sort_key)
    title_dead_holders.sort(key=sort_key)
    if CLEANUP_TITLE_HISTORY:
        print('not implemented lols')
    def title_region(title):
        try:
            region = title_djls[title][0]
        except KeyError:
            return 'undefined'
        if region.startswith('e'):
            if region in ('e_null', 'e_placeholder'):
                try:
                    return title_djls[title][1]
                except:
                    pass
            return region
        return 'titular'
    with (rootpath / 'check_title_history.txt').open('w') as fp:
        print('Liege has no holder:', file=fp)
        if not title_liege_errors:
            print('\t(none)', file=fp)
        prev_region = None
        for title, errors in title_liege_errors:
            if (PRUNE_ALL_BUT_REGION and
                PRUNE_ALL_BUT_REGION not in title_djls[title]):
                continue
            region = title_region(title)
            if (not PRUNE_ALL_BUT_REGION and LANDED_TITLES_ORDER and
                region != prev_region):
                print('\t# {}'.format(region), file=fp)
            line = '\t{}: '.format(title)
            line += ', '.join(iv_to_str(iv) for iv in sorted(errors))
            print(line, file=fp)
            prev_region = region
        print('Liege not of higher tier:', file=fp)
        if not title_lte_tier:
            print('\t(none)', file=fp)
        for title, lte_tier in title_lte_tier:
            line = '\t{}: '.format(title)
            line += ', '.join(iv_to_str(iv) for iv in sorted(lte_tier))
            print(line, file=fp)
        if CHECK_DEAD_HOLDERS:
            print('Holder not alive:', file=fp)
            if not title_dead_holders:
                print('\t(none)', file=fp)
            prev_region = None
            for title, dead_holders in title_dead_holders:
                if (PRUNE_ALL_BUT_REGION and
                    PRUNE_ALL_BUT_REGION not in title_djls[title]):
                    continue
                region = title_region(title)
                if (not PRUNE_ALL_BUT_REGION and LANDED_TITLES_ORDER and
                    region != prev_region):
                    print('\t# {}'.format(region), file=fp)
                line = '\t{}: '.format(title)
                line += ', '.join(iv_to_str(iv) for iv in sorted(dead_holders))
                print(line, file=fp)
                prev_region = region
        if CHECK_LIEGE_CONSISTENCY:
            print('Liege inconsistency (unambiguous):', file=fp)
            if not liege_consistency_unamb:
                print('\t(none)', file=fp)
            for char, ivs in sorted(liege_consistency_unamb.items()):
                for iv, liege_holders in sorted(ivs.items()):
                    print('\t{}, {}:'.format(char, iv_to_str(iv)), file=fp)
                    for liege_holder, lieges in sorted(liege_holders.items()):
                        for liege, titles in sorted(lieges.items(),
                            key=lambda x: landed_titles_index[x[0]]):
                            print('\t\t{} ({}) <= {}'.format(
                                liege, liege_holder, ', '.join(sorted(titles,
                                key=lambda x: landed_titles_index[x]))),
                                file=fp)
            print('Liege inconsistency (ambiguous):', file=fp)
            if not liege_consistency_amb:
                print('\t(none)', file=fp)
            for char, ivs in sorted(liege_consistency_amb.items()):
                for iv, liege_holders in sorted(ivs.items()):
                    print('\t{}, {}:'.format(char, iv_to_str(iv)), file=fp)
                    for liege_holder, lieges in sorted(liege_holders.items()):
                        for liege, titles in sorted(lieges.items(),
                            key=lambda x: landed_titles_index[x[0]]):
                            print('\t\t{} ({}) <= {}'.format(
                                liege, liege_holder, ', '.join(sorted(titles,
                                key=lambda x: landed_titles_index[x]))),
                                file=fp)

if __name__ == '__main__':
    main()
