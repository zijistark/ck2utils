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
import ck2parser
import localpaths

# if true, instead of removing localisation, write out a file listing broken
# localisations expected to match one of the patterns to be removed
AUDIT = False

vanilladir = localpaths.vanilladir

def make_outpath(outroot, inpath, *roots):
    for i, root in enumerate(roots):
        try:
            return outroot / inpath.relative_to(root)
        except ValueError:
            if i == len(roots) - 1:
                raise

def get_max_provs(where):
    tree = ck2parser.parse_file(where / 'map/default.map')
    return next(int(v.val) for n, v in tree if n.val == 'max_provinces')

def process_cultures(where, build):
    def update_obj(obj):
        for p in reversed(obj.contents):
            if p.key.val == 'dynasty_title_names':
                obj.contents.remove(p)

    cultures = []
    culture_groups = []
    for inpath, tree in ck2parser.parse_files('common/cultures/*', where):
        for n, v in tree:
            culture_groups.append(n.val)
            for n2, v2 in v:
                if n2.val != 'graphical_cultures':
                    cultures.append(n2.val)
                    update_obj(v2)
            update_obj(v)
        if not AUDIT:
            outpath = make_outpath(build, inpath, where, vanilladir)
            with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
                f.write(tree.str())
    return cultures, culture_groups

def process_history(where, build, extra_keys=None):
    for glob in ['history/provinces/*', 'history/titles/*']:
        for inpath, tree in ck2parser.parse_files(glob, where):
            mutated = False
            for n, v in tree:
                if isinstance(n, ck2parser.Date):
                    for p2 in reversed(v.contents):
                        n2, v2 = p2
                        if re.fullmatch(r'(reset_)?(name|adjective)', n2.val):
                            if not AUDIT:
                                mutated = True
                                v.contents.remove(p2)
                            elif n2.val in ['name', 'adjective']:
                                extra_keys.add(v2.val)
            if mutated:
                outpath = make_outpath(build, inpath, where, vanilladir)
                with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
                    f.write(tree.str())

def get_religions(where):
    religions = []
    religion_groups = []
    for _, tree in ck2parser.parse_files('common/religions/*', where):
        for n, v in tree:
            religion_groups.append(n.val)
            religions.extend(n2.val for n2, v2 in v
                             if (isinstance(v2, ck2parser.Obj) and
                                 n2.val not in ['male_names', 'female_names']))
    return religions, religion_groups

def get_governments(where):
    governments = []
    prefixes = []
    for _, tree in ck2parser.parse_files('common/governments/*', where):
        for _, v in tree:
            for n2, v2 in v:
                governments.append(n2.val)
                try:
                    prefix = next(
                        v3.val for n3, v3 in v2 if n3.val == 'title_prefix')
                except StopIteration:
                    continue
                if prefix not in prefixes:
                    prefixes.append(prefix)
    return governments, prefixes

def get_unlanded_titles(where):
    ul_titles = []
    for glob in ['common/job_titles/*', 'common/minor_titles/*']:
        for _, tree in ck2parser.parse_files(glob, where):
            ul_titles.extend(n.val for n, v in tree)
    return ul_titles

def main():
    if len(sys.argv) <= 1:
        modpath = localpaths.rootpath / 'SWMH-BETA/SWMH'
    else:
        modpath = pathlib.Path(sys.argv[1])
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

    max_provs = get_max_provs(modpath)
    cultures, culture_groups = process_cultures(modpath, build)
    religions, religion_groups = get_religions(modpath)
    governments, gov_prefixes = get_governments(modpath)
    ul_titles = get_unlanded_titles(modpath)
    ck2parser.fq_keys = cultures
    lt_keys_to_remove = [
        'title', 'title_female', 'foa', 'title_prefix', 'short_name',
        'name_tier', 'location_ruler_title', 'dynasty_title_names'] + cultures
    titles = set()
    extra_keys = set()

    def update_tree(tree):
        for n, v in tree:
            if ck2parser.is_codename(n.val):
                titles.add(n.val)
                for p2 in reversed(v.contents):
                    n2, v2 = p2
                    if n2.val in lt_keys_to_remove:
                        if AUDIT:
                            if isinstance(v2, ck2parser.String):
                                extra_keys.add(v2.val)
                            continue
                        v.contents.remove(p2)
                update_tree(v)

    # process landed_titles
    for inpath, tree in ck2parser.parse_files('common/landed_titles/*',
                                              modpath):
        outpath = make_outpath(build, inpath, modpath, vanilladir)
        update_tree(tree)
        if not AUDIT:
            with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
                f.write(tree.str())

    type_re = '|'.join(['family_palace_', 'vice_royalty_'] + gov_prefixes)
    title_re = '|'.join(ul_titles)
    culture_re = '|'.join(cultures + culture_groups)
    religion_re = '|'.join(religions + religion_groups)
    govs_re = '|'.join(governments)
    misc_regex = culture_re + '|' + religion_re + '|' + govs_re
    noble_regex = ('(({})?((baron|count|duke|king|emperor)|'
                   '((barony|county|duchy|kingdom|empire)(_of)?))_?)?({})?'
                   '(_female)?(_({}|{}))?').format(type_re, title_re, culture_re,
                                                religion_re)

    # process history
    process_history(modpath, build, extra_keys)

    def check_key(key):
        lt_match = re.match(r'[ekdcb]_((?!_adj($|_)).)*', key)
        prov_match = re.fullmatch(r'PROV(\d+)', key)
        if lt_match:
            title = lt_match.group()
            if title not in titles:
                return None
            if re.fullmatch(r'c_((?!_adj($|_)).)*', key):
                return None
        elif prov_match:
            prov_id = prov_match.group(1)
            if not (0 < prov_id < max_provs):
                return None
        elif re.fullmatch(misc_regex, key):
            pass
        elif re.fullmatch(noble_regex, key):
            pass
        elif key in extra_keys:
            pass
        else:
            return None
        outrow = [''] * 15
        outrow[0] = key
        outrow[-1] = 'x'
        return outrow

    if AUDIT:
        # import pprint
        # pprint.pprint(noble_regex)
        inpaths = [modpath / 'localisation' / name for name in [
            'A Cultures.csv', 'A DuchiesKingdomsandEmpires de jure.csv',
            'A DuchiesKingdomsandEmpires titular.csv',
            'A Jobs and minor titles.csv', 'A Mercs.csv', 'A Nobletitles.csv',
            'A Religions.csv', 'A SWMHbaronies.csv', 'A SWMHcounties.csv',
            'A SWMHnewprovinces.csv', 'A SWMHprovinces.csv']]
        outpath = modpath / 'out.txt'
        with outpath.open('w', encoding='cp1252', newline='') as f:
            for inpath in inpaths:
                for row in ck2parser.csv_rows(inpath):
                    if len(row) >= 2 and '#' not in row[0]:
                        if not check_key(row[0]):
                            print(row[0], file=f)
        raise SystemExit()

    # process localisation
    outrows = [[''] * 15]
    outrows[0][:6] = ['#CODE', 'ENGLISH', 'FRENCH', 'GERMAN', '', 'SPANISH']
    outrows[0][-1] = 'x'

    keys_seen = set()
    for path in ck2parser.files('localisation/*', modpath):
        for row in ck2parser.csv_rows(path):
            if len(row) >= 2 and row[0] not in keys_seen:
                keys_seen.add(row[0])
                outrow = check_key(row[0])
                if outrow:
                    outrows.append(outrow)

    outpath = build / 'localisation' / 'A AAA testing override.csv'
    with outpath.open('w', encoding='cp1252', newline='') as csvfile:
        csv.writer(csvfile, dialect='ckii').writerows(outrows)

if __name__ == '__main__':
    main()
