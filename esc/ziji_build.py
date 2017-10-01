#!/usr/bin/env python3

'''
Removes all localisations thoroughly*:
  - provinces, landed titles
  - noble titles, minor titles, job titles
  - cultures, religions, governments

*including history, not including events/decisions

Positional argument 1: path to mod
    defaults to localpaths.rootpath / 'SWMH-BETA/SWMH'.
Positional argument 2: path to output directory
    defaults to path to mod: i.e., work in-place, i.e., clobber the mod.
    or, pick a different directory, write a .mod file that points to it, with
    a dependency on the first mod, and you're set.
'''

import csv
import pathlib
import re
import sys
from ck2parser import (rootpath, vanilladir, csv_rows, files, get_religions,
                       get_province_id_name_map, is_codename, Date, String,
                       SimpleParser)
from print_time import print_time

# if true, instead of removing localisation, write out a file listing broken
# localisations expected to match one of the patterns to be removed
#
# This option assumes SWMH localisation filenames. If necessary it can be made
# more general
AUDIT = False

# if true, blank ALL localisations
NUKE_IT_FROM_ORBIT = False

COUNTY_TITLE_NAMES = True
PROVINCE_HISTORY_NAMES = False

def make_outpath(outroot, inpath, *roots):
    for i, root in enumerate(roots):
        try:
            return outroot / inpath.relative_to(root)
        except ValueError:
            if i == len(roots) - 1:
                raise

def process_cultures(parser, build):
    def update_obj(obj):
        for p in reversed(obj.contents):
            if p.key.val == 'dynasty_title_names':
                obj.contents.remove(p)
                return True
        return False

    cultures = []
    culture_groups = []
    for inpath, tree in parser.parse_files('common/cultures/*'):
        mutated = False
        for n, v in tree:
            culture_groups.append(n.val)
            for n2, v2 in v:
                if n2.val != 'graphical_cultures':
                    cultures.append(n2.val)
                    mutated |= update_obj(v2)
            mutated |= update_obj(v)
        if not AUDIT and mutated:
            outpath = make_outpath(build, inpath, vanilladir, *parser.moddirs)
            with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
                f.write(tree.str(parser))
    return cultures, culture_groups

def process_history(parser, build, extra_keys):
    prov_title = {}
    id_name = get_province_id_name_map(parser)
    # critical_error = False
    for glob in ['history/provinces/*', 'history/titles/*']:
        # replace errors: vanilla history has some UTF-8 bytes
        for inpath, tree in parser.parse_files(glob, errors='replace'):
            # if isinstance(tree, Exception):
            #     critical_error = True
            #     continue
            mutated = False
            for n, v in tree:
                if isinstance(n, Date):
                    for p2 in reversed(v.contents):
                        n2, v2 = p2
                        if re.fullmatch(r'(reset_)?(name|adjective)', n2.val):
                            if not AUDIT:
                                mutated = True
                                v.contents.remove(p2)
                            elif n2.val in ['name', 'adjective']:
                                extra_keys.add(v2.val)
                if glob == 'history/provinces/*' and n.val == 'title':
                    number, name = inpath.stem.split(' - ')
                    number = int(number)
                    if id_name.get(number) == name:
                        prov_title['PROV{}'.format(number)] = v.val
            if mutated:
                outpath = make_outpath(build, inpath, vanilladir,
                                       *parser.moddirs)
                with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
                    f.write(tree.str(parser))
    # if critical_error:
    #     raise SystemExit()
    return id_name, prov_title

def get_governments(parser):
    governments = []
    prefixes = []
    for _, tree in parser.parse_files('common/governments/*'):
        for _, v in tree:
            for n2, v2 in v:
                governments.append(n2.val)
                try:
                    prefix = v2['title_prefix'].val
                except KeyError:
                    continue
                if prefix not in prefixes:
                    prefixes.append(prefix)
    return governments, prefixes

def get_unlanded_titles(parser):
    ul_titles = []
    for glob in ['common/job_titles/*', 'common/minor_titles/*']:
        for _, tree in parser.parse_files(glob):
            ul_titles.extend(n.val for n, v in tree)
    return ul_titles

def get_max_provinces(parser):
    return next(parser.parse_files('map/default.map'))[1]['max_provinces'].val

@print_time
def main():
    parser = SimpleParser()
    if len(sys.argv) <= 1:
        modpath = rootpath / 'SWMH-BETA/SWMH'
    else:
        modpath = pathlib.Path(sys.argv[1])
    parser.moddirs = [modpath]
    if len(sys.argv) <= 2:
        build = modpath
    else:
        build = pathlib.Path(sys.argv[2])
    for d in ['common/cultures', 'common/landed_titles', 'history/provinces',
              'history/titles', 'localisation']:
        # pls cygwin gib 3.5
        # (build / d).mkdir(parents=True, exist_ok=True)
        try:
            (build / d).mkdir(parents=True)
        except FileExistsError: # pls cygwin gib 3.5
            pass

    max_provs = get_max_provinces(parser)
    cultures, culture_groups = process_cultures(parser, build)
    if not NUKE_IT_FROM_ORBIT:
        religions, religion_groups = get_religions(parser)
        governments, gov_prefixes = get_governments(parser)
        ul_titles = get_unlanded_titles(parser)
    parser.fq_keys = cultures
    lt_keys_to_remove = [
        'title', 'title_female', 'foa', 'title_prefix', 'short_name',
        'name_tier', 'location_ruler_title', 'dynasty_title_names'] + cultures
    titles = set()
    extra_keys = set()

    def update_tree(tree):
        for n, v in tree:
            if is_codename(n.val):
                titles.add(n.val)
                for p2 in reversed(v.contents):
                    n2, v2 = p2
                    if n2.val in lt_keys_to_remove:
                        if AUDIT:
                            if isinstance(v2, String):
                                extra_keys.add(v2.val)
                            continue
                        v.contents.remove(p2)
                update_tree(v)

    # process landed_titles
    for inpath, tree in parser.parse_files('common/landed_titles/*'):
        outpath = make_outpath(build, inpath, vanilladir, *parser.moddirs)
        update_tree(tree)
        if not AUDIT:
            with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
                f.write(tree.str(parser))

    # process history
    id_name, prov_title = process_history(parser, build, extra_keys)

    if NUKE_IT_FROM_ORBIT:
        outrows = [[''] * 15]
        outrows[0][:6] = ['#CODE', 'ENGLISH', 'FRENCH', 'GERMAN', '', 'SPANISH']
        outrows[0][-1] = 'x'
        inpaths = list(files('localisation/*.csv', parser.moddirs))
        for inpath in inpaths:
            outpath = build / 'localisation' / inpath.name
            with outpath.open('w', encoding='cp1252', newline='') as csvfile:
                csv.writer(csvfile, dialect='ckii').writerows(outrows)
        raise SystemExit()

    type_re = '|'.join(['family_palace_', 'vice_royalty_'] + gov_prefixes)
    title_re = '|'.join(ul_titles)
    culture_re = '|'.join(cultures + culture_groups)
    religion_re = '|'.join(religions + religion_groups)
    govs_re = '|'.join(governments)
    misc_regex = culture_re + '|' + religion_re + '|' + govs_re
    noble_regex = ('(({})?((baron|count|duke|king|emperor)|'
                   '((barony|county|duchy|kingdom|empire)(_of)?))_?)?({})?'
                   '(_female)?(_({}|{}))?').format(type_re, title_re,
                                                   culture_re, religion_re)

    def check_key(key):
        outrow = [''] * 15
        outrow[0] = key
        outrow[-1] = 'x'
        lt_match = re.match(r'[ekdcb]_((?!_adj($|_)).)*', key)
        prov_match = re.fullmatch(r'PROV(\d+)', key)
        if lt_match:
            title = lt_match.group()
            if title not in titles:
                return None
            if re.fullmatch(r'c_((?!_adj($|_)).)*', key):
                return None
        elif prov_match:
            prov_id = int(prov_match.group(1))
            if not (0 < prov_id < max_provs):
                return None
            if COUNTY_TITLE_NAMES:
                outrow[1] = prov_title.get(key, '')
            elif PROVINCE_HISTORY_NAMES:
                outrow[1] = '{} ({})'.format(id_name[int(key[4:])], key[4:])
            else:
                outrow[1] = ''
        elif re.fullmatch(misc_regex, key):
            pass
        elif re.fullmatch(noble_regex, key):
            pass
        elif key in extra_keys:
            pass
        else:
            return None
        return outrow

    if AUDIT:
        # import pprint
        # pprint.pprint(noble_regex)
        inpaths = [modpath / 'localisation' / name for name in [
            'A_Cultures.csv', 'A_DuchiesKingdomsandEmpires_de_jure.csv',
            'A_DuchiesKingdomsandEmpires_titular.csv',
            'A_Jobs_and_minor_titles.csv', 'A_Mercs.csv',
            'A_Nobletitles.csv', 'A_Religions.csv', 'A_SWMHbaronies.csv',
            'A_SWMHcounties.csv', 'A_SWMHnewprovinces.csv',
            'A_SWMHprovinces.csv'] for modpath in parser.moddirs]
        outpath = rootpath / 'ziji_build.txt'
        with outpath.open('w', encoding='cp1252', newline='') as f:
            for inpath in inpaths:
                for row in csv_rows(inpath):
                    if not check_key(row[0]):
                        print(row[0], file=f)
        raise SystemExit()

    # process localisation
    outrows = [[''] * 15]
    outrows[0][:6] = ['#CODE', 'ENGLISH', 'FRENCH', 'GERMAN', '', 'SPANISH']
    outrows[0][-1] = 'x'

    keys_seen = set()
    for path in files('localisation/*.csv', parser.moddirs):
        for row in csv_rows(path):
            if len(row) >= 2 and row[0] not in keys_seen:
                keys_seen.add(row[0])
                outrow = check_key(row[0])
                if outrow:
                    outrows.append(outrow)

    outpath = build / 'localisation' / '0 testing override.csv'
    with outpath.open('w', encoding='cp1252', newline='') as csvfile:
        csv.writer(csvfile, dialect='ckii').writerows(outrows)

if __name__ == '__main__':
    main()
