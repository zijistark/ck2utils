#!/usr/bin/env python3

import csv
import re
from ck2parser import (rootpath, get_cultures, get_religions, files, csv_rows,
                       SimpleParser)
from print_time import print_time

# EMF+Vanilla, EMF+SWMH
MODDIRS = (['EMF/EMF', 'EMF/EMF+Vanilla'],
           ['EMF/EMF', 'SWMH-BETA/SWMH', 'EMF/EMF+SWMH'])
OUTPUT = 'EMF/EMF', 'EMF/EMF+SWMH'

OUT_NAME = 'zz~imperial_titles_unmodified.csv'

def get_localisation_keys(moddirs):
    loc_keys = set()
    for path in files('localisation/*', moddirs):
        if path.name != OUT_NAME:
            for row in csv_rows(path):
                loc_keys.add(row[0])
    return loc_keys

def get_other_titles(parser):
    other_titles = []
    for _, tree in parser.parse_files('common/job_titles/*'):
        other_titles.extend(n.val for n, v in tree)
    for _, tree in parser.parse_files('common/minor_titles/*'):
        other_titles.extend(n.val for n, v in tree)
    return other_titles

def make_noble_title_regex(cultures, religions, other_titles):
    title_re = '|'.join(other_titles)
    culture_re = '|'.join(cultures)
    religion_re = '|'.join(religions)
    noble_regex = ('((vice_royalty_)?((baron|count|duke|king|emperor)|'
                   '((barony|county|duchy|kingdom|empire)(_of)?))_?)?({})?'
                   '(_female)?(_({}|{}))?').format(title_re, culture_re,
                   religion_re)
    return noble_regex

def write_output(out_path, parser, loc_keys, noble_regex):
    seen = set()
    out_rows = ['#CODE;ENGLISH;FRENCH;GERMAN;;SPANISH;;;;;;;;;x'.split(';')]
    viceroy_rows = []
    for path in files('localisation/*', parser.moddirs):
        if path.name == OUT_NAME:
            continue
        out_rows.append(['#' + path.name] + [''] * 13 + ['x'])
        for row in csv_rows(path):
            key = row[0]
            if key in seen or not re.fullmatch(noble_regex, key):
                continue
            if key.startswith('vice_royalty'):
                if not any(x in key for x in
                           ['empire', 'emperor', 'count', 'baron']):
                    imperial_key = 'imperial' + key[len('vice_royalty'):]
                    viceroy_row = ([imperial_key] + row[1:14] +
                                   [''] * (14 - len(row)) + ['x'])
                    if not any(r[0] == viceroy_row[0] for r in viceroy_rows):
                        viceroy_rows.append(viceroy_row)
                continue
            seen.add(key)
            imperial_key = 'imperial_' + key
            if imperial_key not in loc_keys:
                out_row = ([imperial_key] + row[1:14] +
                           [''] * (14 - len(row)) + ['x'])
                out_rows.append(out_row)
    for out_row in out_rows:
        for i, row in enumerate(viceroy_rows):
            if row[0] == out_row[0]:
                viceroy_rows.pop(i)
                out_row[:] = row
                break
    if viceroy_rows:
        out_rows.append(['#[extra vice_royalty keys]'] + [''] * 13 + ['x'])
        out_rows.extend(viceroy_rows)
    with out_path.open('w', encoding='cp1252', newline='') as csvfile:
        csv.writer(csvfile, dialect='ckii').writerows(out_rows)

def run_with_mod_set(parser, moddirs, output):
    parser.moddirs = moddirs
    loc_keys = get_localisation_keys(parser.moddirs)
    cultures, cult_groups = get_cultures(parser)
    religions, rel_groups = get_religions(parser)
    other_titles = get_other_titles(parser)
    noble_regex = make_noble_title_regex(
        cultures + cult_groups, religions + rel_groups, other_titles)
    out_path = output / 'localisation/zz~imperial_titles_unmodified.csv'
    write_output(out_path, parser, loc_keys, noble_regex)

@print_time
def main():
    parser = SimpleParser()
    for moddirs, output in zip(MODDIRS, OUTPUT):
        run_with_mod_set(parser,
                         [rootpath / d for d in moddirs], rootpath / output)

if __name__ == '__main__':
    main()
