#!/usr/bin/env python3

from collections import defaultdict, OrderedDict
from operator import attrgetter
from ck2parser import (rootpath, is_codename, get_localisation, SimpleParser,
                       get_provinces)
from print_time import print_time

def process_landed_titles(parser):
    titles_list = []
    title_liege_map = {}
    title_vassals_map = defaultdict(set)
    for path, tree in parser.parse_files('common/landed_titles/*.txt'):
        dfs = list(reversed(tree))
        while dfs:
            n, v = dfs.pop()
            if is_codename(n.val):
                if n.val not in titles_list:
                    titles_list.append(n.val)
                for n2, v2 in v:
                    if is_codename(n2.val):
                        title_liege_map[n2.val] = n.val
                        title_vassals_map[n.val].add(n2.val)
                dfs.extend(reversed(v))
    return titles_list, title_liege_map, title_vassals_map

@print_time
def main():
    parser = SimpleParser()
    parser.moddirs = [rootpath / 'SWMH-BETA/SWMH']
    localisation = get_localisation(parser.moddirs)
    localisation.update({t: localisation['PROV{}'.format(num)]
                         for num, t, _ in get_provinces(parser)})
    titles_list, title_liege_map, title_vassals_map = (
        process_landed_titles(parser))
    start_date = parser.parse_file('common/defines.txt')['start_date'].val

    for path, tree in parser.parse_files('history/titles/*.txt'):
        if tree.contents:
            title = path.stem
            for n, v in sorted(tree, key=attrgetter('key.val')):
                if n.val > start_date:
                    break
                for n2, v2 in v:
                    if n2.val == 'de_jure_liege':
                        old_liege = title_liege_map.get(title)
                        if old_liege:
                            title_vassals_map[old_liege].discard(title)
                        title_liege_map[title] = v2.val
                        title_vassals_map[v2.val].add(title)

    duchies_de_jure = [t for t, v in title_vassals_map.items()
                       if t[0] == 'd' and v]
    duchies_de_jure.sort(key=titles_list.index)
    kingdoms = [title_liege_map[x] for x in duchies_de_jure]
    kingdoms.sort(key=titles_list.index)
    output = ''
    output_map = OrderedDict()
    for kingdom in kingdoms:
        output_map[kingdom] = OrderedDict()
    for duchy in duchies_de_jure:
        counties = sorted(title_vassals_map[duchy], key=titles_list.index)
        liege = title_liege_map[duchy]
        output_map[liege][duchy] = counties

    for n, v in output_map.items():
        output += '{} {}\n'.format(n, localisation[n])
        for n2, v2 in v.items():
            output += '    {} {}\n'.format(n2, localisation[n2])
            for n3 in v2:
                output += '        {} {}\n'.format(n3, localisation[n3])

    outpath = rootpath / 'summarize_duchies.txt'
    with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
        print(output, end='', file=f)

if __name__ == '__main__':
    main()
