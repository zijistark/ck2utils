#!/usr/bin/env python3

from bisect import insort
from collections import defaultdict, namedtuple
from operator import attrgetter
from intervaltree import Interval, IntervalTree
from ck2parser import (rootpath, vanilladir, is_codename, TopLevel, Number,
                       Pair, Obj, Date as ASTDate, Comment, SimpleParser,
                       FullParser)
from print_time import print_time

CHECK_LIEGE_CONSISTENCY = True

LANDED_TITLES_ORDER = True # if false, date order

PRUNE_UNEXECUTED_HISTORY = True # prune all after last playable start
PRUNE_IMPOSSIBLE_STARTS = True # implies prev
PRUNE_NONBOOKMARK_STARTS = False # implies prev
PRUNE_NONERA_STARTS = False # implies prev

PRUNE_ALL_BUT_DATES = [] # overrides above

PRUNE_ALL_BUT_REGIONS = []

FORMAT_TITLE_HISTORY = False
CLEANUP_TITLE_HISTORY = False # implies previous, overrides date pruning


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


class TitleHistory:
    keys = [
        'de_jure_liege', 'historical_nomad', 'holding_dynasty',
        'liege', 'holder', 'pentarch', 'law', 'vice_royalty', 'active',
        'clear_tribute_suzerain', 'set_tribute_suzerain', 'conquest_culture',
        'name', 'reset_name', 'adjective', 'reset_adjective',
        'set_global_flag', 'clr_global_flag', 'effect'
    ]
    keys_sort_key = lambda cls, x: (
        x.key.val != 'active' or x.value.val != 'yes',
        cls.keys.index(x.key.val))

    def __init__(self, name, djl):
        self.name = name
        self.has_file = False
        self.attr = {k: [(Date.EARLIEST, v)] for k, v in [
            ('holder', 0),
            ('liege', djl if name.startswith('b') else 0),
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
        self.date_comments = defaultdict(list)
        self.date_ker_comments = defaultdict(list)
        self.attr_comment = {}
        self.post_comments = None
        self.history = defaultdict(list)
        self.tree = None

    def compile(self):
        for k, vs in self.attr.items():
            for i, (date, v) in enumerate(vs):
                if date != Date.EARLIEST:
                    if k == 'suzerain':
                        if v[1] == 0:
                            item = 'clear_tribute_suzerain', v[0]
                        else:
                            if (i > 0 and vs[i - 1][1] != 0 and
                                vs[i - 1][1][0] != v[0]):
                                self.history[date].append(
                                    Pair('clear_tribute_suzerain',
                                         vs[i - 1][1][0]))
                            v = Obj([Pair('who', v[0]),
                                     Pair('percentage', Number(str(v[1])))])
                            item = 'set_tribute_suzerain', v
                    elif k in ('name', 'adjective') and v == '':
                        item = 'reset_{}'.format(k), 'yes'
                    else:
                        item = k, v
                    if isinstance(item[1], int):
                        item = item[0], Number(str(item[1]))
                    pair = Pair(item[0], item[1])
                    if isinstance(item[1], Number):
                        item = item[0], item[1].val
                    if (date, item) in self.attr_comment:
                        pre, post = self.attr_comment[date, item]
                        pair.key.pre_comments = pre
                        pair.value.post_comment = post
                    self.history[date].append(pair)
        contents = []
        for date, items in sorted(self.history.items()):
            items.sort(key=self.keys_sort_key)
            obj = Obj(items)
            obj.ker.pre_comments = self.date_ker_comments[date]
            date = ASTDate(self.date_comments[date], str(date), None)
            date_pair = Pair(date, obj)
            contents.append(date_pair)
        self.tree = TopLevel(contents)
        self.tree.post_comments = self.post_comments

    def remove_dead_holders(self, parser, dead_holders):
        print(self.name)
        if not dead_holders:
            return
        if not self.tree:
            self.compile()
        prevprev_holder = 0
        prev = -1, None, None
        i = 0
        while True:
            last_iter = i == len(self.tree)
            if not last_iter:
                date_pair = self.tree.contents[i]
                date = date_pair.key.val
                obj = date_pair.value
                try:
                    j, holder_pair = next((j, e) for j, e in enumerate(obj)
                                          if e.key.val == 'holder')
                except StopIteration:
                    i += 1
                    continue
                holder = holder_pair.value.val
            else:
                date = Date.LATEST
            prev_i, prev_date_pair, prev_holder_pair = prev
            if prev_date_pair:
                prev_date = prev_date_pair.key.val
                prev_holder = prev_holder_pair.value.val
            else:
                prev = i, date_pair, holder_pair
                i += 1
                continue
            #if self.name == 'c_godwad' and prev_date[0] == 1321:
            #    import pdb; pdb.set_trace()
            if not last_iter and holder == 0:
                if prev_holder == 0:
                    if len(obj) == 1:
                        # remove whole date
                        del self.tree.contents[i]
                    else:
                        del obj.contents[j]
                else:
                    i += 1
                continue
            try:
                begin, end = next((b, e)
                                  for b, e in dead_holders if e > prev_date)
            except StopIteration:
                break
            if begin <= prev_date:
                obj = prev_date_pair.value
                if prevprev_holder == 0:
                    if len(obj) == 1:
                        # remove whole date
                        self.tree.contents.remove(prev_date_pair)
                        pair_is, _ = prev_date_pair.inline_str(0, parser, 0)
                        comments = [Comment(s)
                                    for s in pair_is.split('\n') if s]
                        if prev_i < len(self.tree):
                            # TODO fix how this stacks up comment level
                            next_thing = self.tree.contents[prev_i].key
                            next_thing.pre_comments[:0] = comments
                            i -= 1
                        else:
                            self.post_comments[:0] = comments
                    else:
                        j = obj.contents.index(prev_holder_pair)
                        pair_is, _ = prev_holder_pair.inline_str(0, parser, 0)
                        comments = [Comment(s)
                                    for s in pair_is.split('\n') if s]
                        next_thing = (obj.contents[j + 1].key
                                      if j + 1 < len(obj) else obj.ker)
                        next_thing.pre_comments[:0] = comments
                else:
                    obj.contents.remove(prev_holder_pair)
                    no_holder_pair = Pair('holder', Number(0))
                    pair_is, _ = prev_holder_pair.inline_str(0, parser, 0)
                    comments = [Comment(s)
                                for s in pair_is.split('\n') if s]
                    no_holder_pair.key.pre_comments[:0] = comments
                    obj.contents.append(no_holder_pair)
                    obj.contents.sort(key=self.keys_sort_key)
                # possible redundant holder = 0 from that
                # will be removed next iteration
                if end < date:
                    # re-add holder when he's born
                    if end in self.tree.dictionary:
                        obj = self.tree[end]
                        obj.contents.append(prev_holder_pair)
                        obj.contents.sort(key=self.keys_sort_key)
                    else:
                        self.tree.contents.append(Pair(
                            ASTDate(str(end)), Obj([prev_holder_pair])))
                        self.tree.contents.sort(key=lambda x: x.key.val)
                next_begin = next((b for b, e in dead_holders if b > begin),
                                  Date.LATEST)
                if next_begin < date:
                    no_holder_pair = Pair('holder', Number(0))
                    if end in self.tree.dictionary:
                        obj = self.tree[end]
                        obj.contents.append(no_holder_pair)
                        obj.contents.sort(key=self.keys_sort_key)
                    else:
                        self.tree.contents.append(Pair(
                            ASTDate(str(end)), Obj([no_holder_pair])))
                        self.tree.contents.sort(key=lambda x: x.key.val)
            elif begin < date:
                # no holder when he's dead
                if holder == 0:
                    if len(date_pair.value) == 1:
                        date_pair.key = ASTDate(str(begin))
                    else:
                        date_pair.value.contents.remove(holder_pair)
                        date_pair = Pair(ASTDate(str(begin)),
                                         Obj([holder_pair]))
                        self.tree.contents.append(date_pair)
                    self.tree.contents.sort(key=lambda x: x.key.val)
                    i = self.tree.contents.index(date_pair)
                else:
                    no_holder_pair = Pair('holder', Number(0))
                    if begin in self.tree.dictionary:
                        obj = self.tree[begin]
                        obj.contents.append(no_holder_pair)
                        obj.contents.sort(key=self.keys_sort_key)
                    else:
                        self.tree.contents.append(Pair(
                            ASTDate(str(begin)), Obj([no_holder_pair])))
                        self.tree.contents.sort(key=lambda x: x.key.val)
                        i += 1
                    date = end
            if last_iter:
                break
            if end == date:
                prevprev_holder = 0
            else:
                prevprev_holder = prev_holder
            prev = i, date_pair, holder_pair
            i += 1

    def write(self, parser, folder):
        if not self.tree:
            self.compile()
        path = folder / '{}.txt'.format(self.name)
        parser.write(self.tree, path)

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
    if iv[0] == Date.EARLIEST and iv[1] == Date.LATEST:
        s = 'always'
    elif iv[0] == Date.EARLIEST:
        s = 'till {}'.format(iv[1])
    elif iv[1] == Date.LATEST:
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
    simple_parser = SimpleParser(rootpath / 'SWMH-BETA/SWMH')
    if FORMAT_TITLE_HISTORY or CLEANUP_TITLE_HISTORY:
        history_parser = FullParser(rootpath / 'SWMH-BETA/SWMH')
    else:
        history_parser = simple_parser
    history_parser.no_fold_to_depth = 0
    landed_titles_index = {0: -1}
    title_djls = {}
    histories = {}
    current_index = 0
    def recurse(tree, stack=[]):
        nonlocal current_index
        for n, v in tree:
            if is_codename(n.val):
                histories[n.val] = TitleHistory(n.val,
                                                stack[-1] if stack else 0)
                landed_titles_index[n.val] = current_index
                current_index += 1
                stack.append(n.val)
                title_djls[n.val] = stack.copy()
                recurse(v, stack=stack)
                stack.pop()
    for _, tree in simple_parser.parse_files('common/landed_titles/*'):
        recurse(tree)
    date_filter = IntervalTree()
    if not CLEANUP_TITLE_HISTORY:
        if PRUNE_ALL_BUT_DATES:
            dates = [Date(*d) for d in PRUNE_ALL_BUT_DATES]
            dates.append(Date.LATEST)
            date_filter.addi(Date.EARLIEST, dates[0])
            for i in range(len(dates) - 1):
                date_filter.addi(dates[i].get_next_day(), dates[i + 1])
        elif (PRUNE_UNEXECUTED_HISTORY or PRUNE_IMPOSSIBLE_STARTS or
            PRUNE_NONBOOKMARK_STARTS or PRUNE_NONERA_STARTS):
            date_filter.addi(Date.EARLIEST, Date.LATEST)
            last_start_date = Date.EARLIEST
            for _, tree in simple_parser.parse_files('common/bookmarks/*'):
                for _, v in tree:
                    date = Date(*v['date'].val)
                    if not PRUNE_NONERA_STARTS or v.has_pair('era', 'yes'):
                        date_filter.chop(date, date.get_next_day())
                    last_start_date = max(date, last_start_date)
            if not PRUNE_NONBOOKMARK_STARTS and not PRUNE_NONERA_STARTS:
                defines = simple_parser.parse_file('common/defines.txt')
                first = Date(*defines['start_date'].val)
                last = Date(*defines['last_start_date'].val)
                date_filter.chop(first, last.get_next_day())
                last_start_date = max(last, last_start_date)
                if not PRUNE_IMPOSSIBLE_STARTS:
                    date_filter.clear()
                    date_filter.addi(last_start_date.get_next_day(),
                                     Date.LATEST)
    title_holders = defaultdict(IntervalTree)
    title_unheld = defaultdict(
        lambda: IntervalTree.from_tuples([(Date.EARLIEST, Date.LATEST)]))
    title_lieges = defaultdict(IntervalTree)
    title_lte_tier = []
    char_titles = defaultdict(IntervalTree)
    char_life = {}
    title_dead_holders = []
    title_county_unheld = []
    for _, tree in simple_parser.parse_files('history/characters/*'):
        for n, v in tree:
            birth = next((Date(*n2.val) for n2, v2 in v
                          if (isinstance(n2, ASTDate) and v2.get('birth'))),
                         Date.LATEST)
            death = next((Date(*n2.val) for n2, v2 in v
                          if (isinstance(n2, ASTDate) and v2.get('death'))),
                         Date.LATEST)
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
        histories[title].has_file = True
        histories[title].post_comments = tree.post_comments
        if FORMAT_TITLE_HISTORY and not CLEANUP_TITLE_HISTORY:
            history_parser.write(tree, path)
        try:
            for p in sorted(tree, key=attrgetter('key.val')):
                n, v = p
                date = Date(*n.val)
                date_comments = histories[title].date_comments[date]
                date_comments.extend(str(c) for c in n.pre_comments)
                potentials = [x.post_comment for x in (p.op, v.kel, v.ker)
                              if x.post_comment]
                if not(len(potentials) == 1 and len(v) == 1 and
                       not v.contents[0].value.post_comment):
                    histories[title].date_comments[date].extend(str(c) for c in
                                                                potentials)
                histories[title].date_ker_comments[date].extend(
                    v.ker.pre_comments)
                for p2 in v:
                    n2, v2 = p2
                    if n2.val in ('law', 'set_global_flag', 'clr_global_flag',
                                  'effect'):
                        histories[title].history[date].append(p2)
                        continue
                    attr_vals, value = None, None
                    if n2.val in ('holder', 'liege'):
                        if v2.val in ('0', '-', title):
                            value = 0
                    elif n2.val == 'set_tribute_suzerain':
                        attr_vals = histories[title].attr['suzerain']
                        try:
                            value = v2['who'].val, v2['percentage'].val
                        except KeyError:
                            continue
                    elif n2.val == 'clear_tribute_suzerain':
                        attr_vals = histories[title].attr['suzerain']
                        value = v2.val, 0
                        if attr_vals[-1][1] == 0 or attr_vals[-1][1][0] != v2.val:
                            continue
                    elif n2.val in ('reset_adjective', 'reset_name'):
                        if v2.val != 'yes':
                            continue
                        attr_vals = histories[title].attr[n2.val[6:]]
                        value = ''
                    if attr_vals is None:
                        attr_vals = histories[title].attr[n2.val]
                    if value is None:
                        value = v2.val
                    if attr_vals[-1][0] == date:
                        attr_vals[-1] = date, value
                    elif attr_vals[-1][1] != value:
                        attr_vals.append((date, value))
                    if (len(potentials) == 1 and len(v) == 1 and
                        not v2.post_comment):
                        if isinstance(v2, Obj):
                            v2.kel.post_comment = potentials[0]
                        else:
                            v2.post_comment = potentials[0]
                    if n2.pre_comments or v2.post_comment:
                        histories[title].attr_comment[date, (n2.val, value)] = (
                            n2.pre_comments, v2.post_comment)
        except TypeError:
            print(path)
            raise
        dead_holders = []
        county_unheld = []
        holders = histories[title].attr['holder']
        for i, (begin, holder) in enumerate(holders):
            try:
                end = holders[i + 1][0]
            except IndexError:
                end = Date.LATEST
            if holder != 0:
                birth, death = char_life.get(holder,
                                             (Date.LATEST, Date.LATEST))
                if begin < birth and death < end:
                    if dead_holders and dead_holders[-1][1] == begin:
                        dead_holders[-1] = dead_holders[-1][0], birth
                    else:
                        dead_holders.append((begin, birth))
                    if dead_holders[-1][1] == death:
                        dead_holders[-1] = dead_holders[-1][0], end
                    else:
                        dead_holders.append((death, end))
                elif begin < birth or death < end:
                    error_begin = death if birth <= begin < death else begin
                    error_end = birth if begin < birth <= end else end
                    if dead_holders and dead_holders[-1][1] == error_begin:
                        dead_holders[-1] = dead_holders[-1][0], error_end
                    else:
                        dead_holders.append((error_begin, error_end))
            elif title.startswith('c'):
                if county_unheld and county_unheld[-1][1] == begin:
                    county_unheld[-1] = county_unheld[-1][0], end
                else:
                    county_unheld.append((begin, end))
            title_holders[title][begin:end] = holder
            if holder != 0:
                char_titles[holder][begin:end] = title
                title_unheld[title].chop(begin, end)
        lte_tier = IntervalTree()
        lieges = histories[title].attr['liege']
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
        if county_unheld:
            county_unheld = IntervalTree.from_tuples(county_unheld)
            title_county_unheld.append((title, county_unheld))
    # counties without title histories
    for history in histories.values():
        if not history.has_file and history.name.startswith('c'):
            title_county_unheld.append((history.name,
                                        [(Date.EARLIEST, Date.LATEST)]))
    # possible todo: look for dead lieges,
    # even though redundant with dead holders
    title_liege_errors = []
    for title, lieges in title_lieges.items():
        errors = []
        for liege_begin, liege_end, liege in sorted(lieges):
            # counties are always held by someone
            if liege == 0 or liege.startswith('c'):
                continue
            liege_unhelds = IntervalTree(title_unheld[liege])
            if not title.startswith('c'):
                # don't care if liege is unheld when this title is also unheld
                prune_tree(liege_unhelds, title_unheld[title])
            for liege_unheld in liege_unhelds[liege_begin:liege_end]:
                begin = max(liege_begin, liege_unheld.begin)
                end = min(liege_end, liege_unheld.end)
                if errors and errors[-1][1] == begin:
                    errors[-1] = errors[-1][0], end
                else:
                    errors.append((begin, end))
        if errors:
            errors = IntervalTree.from_tuples(errors)
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
                    items[begin, end][liege_holder][liege].append(title)
                for iv, liege_holders in items.items():
                    if len(liege_holders) > 1:
                        if (PRUNE_ALL_BUT_REGIONS and
                            all(region not in title_djls.get(title, ())
                                for _, ls in liege_holders.items()
                                for l in ls
                                for region in PRUNE_ALL_BUT_REGIONS) and
                            all(region not in title_djls.get(title, ())
                                for _, ls in liege_holders.items()
                                for _, ts in ls.items() for t in ts
                                for region in PRUNE_ALL_BUT_REGIONS)):
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
        for title, errors in reversed(title_county_unheld):
            prune_tree(errors, date_filter)
            if not errors:
                title_county_unheld.remove((title, errors))
        for title, dead_holders in reversed(title_dead_holders):
            prune_tree(dead_holders, date_filter)
            if not dead_holders:
                title_dead_holders.remove((title, dead_holders))
    if LANDED_TITLES_ORDER:
        sort_key = lambda x: landed_titles_index[x[0]]
    else:
        sort_key = lambda x: (x[1].begin(), landed_titles_index[x[0]])
    title_liege_errors.sort(key=sort_key)
    title_county_unheld.sort(key=sort_key)
    title_lte_tier.sort(key=sort_key)
    title_dead_holders.sort(key=sort_key)
    if CLEANUP_TITLE_HISTORY:
        history_folder = history_parser.moddirs[0] / 'history/titles'
        for history in sorted(histories.values(), key=lambda x: x.name):
            if history.has_file:
                dead_holders = next((l for title, l in title_dead_holders
                                     if title == history.name), [])
                dead_holders = [(x[0], x[1]) for x in sorted(dead_holders)]
                history.remove_dead_holders(history_parser, dead_holders)
                history.write(history_parser, history_folder)
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
            if (PRUNE_ALL_BUT_REGIONS and
                all(region not in title_djls[title]
                    for region in PRUNE_ALL_BUT_REGIONS)):
                continue
            region = title_region(title)
            if (not PRUNE_ALL_BUT_REGIONS and LANDED_TITLES_ORDER and
                region != prev_region):
                print('\t# {}'.format(region), file=fp)
            line = '\t{}: '.format(title)
            line += ', '.join(iv_to_str(iv) for iv in sorted(errors))
            print(line, file=fp)
            prev_region = region
        print('County has no holder:', file=fp)
        if not title_county_unheld:
            print('\t(none)', file=fp)
        prev_region = None
        for title, errors in title_county_unheld:
            if (PRUNE_ALL_BUT_REGIONS and
                all(region not in title_djls[title]
                    for region in PRUNE_ALL_BUT_REGIONS)):
                continue
            region = title_region(title)
            if (not PRUNE_ALL_BUT_REGIONS and LANDED_TITLES_ORDER and
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
        print('Holder not alive:', file=fp)
        if not title_dead_holders:
            print('\t(none)', file=fp)
        prev_region = None
        for title, dead_holders in title_dead_holders:
            if (PRUNE_ALL_BUT_REGIONS and
                all(region not in title_djls[title]
                    for region in PRUNE_ALL_BUT_REGIONS)):
                continue
            region = title_region(title)
            if (not PRUNE_ALL_BUT_REGIONS and LANDED_TITLES_ORDER and
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
