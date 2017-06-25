#!/usr/bin/env python3

from collections import OrderedDict
import re
import numpy as np
from PIL import Image
from ck2parser import rootpath, csv_rows, SimpleParser, Pair, Obj
from localpaths import eu4dir
from print_time import print_time

def localisation():
    localisation_dict = {}
    for path in (eu4dir / 'localisation').glob('*_l_english.yml'):
        with path.open(encoding='utf-8-sig') as f:
            for line in f:
                match = re.fullmatch(r'\s*([^#\s:]+):\d?\s*"(.*)"[^"]*', line)
                if match:
                    localisation_dict[match.group(1)] = match.group(2)
    return localisation_dict

def analyze_provinces():
    parser = SimpleParser()
    parser.basedir = eu4dir

    localisation_dict = localisation()
    localize = lambda key: localisation_dict.get(key, key)

    default_tree = parser.parse_file('map/default.map')

    max_provinces = default_tree['max_provinces'].val
    random_only = {n.val for n in default_tree['only_used_for_random']}
    map_path = lambda key: parser.file('map/' + default_tree[key].val)

    provinces = OrderedDict()
    for i in range(1, max_provinces):
        if i in random_only:
            continue
        prov = {}
        prov['ID'] = str(i)
        prov['Name'] = localize('PROV{}'.format(i))
        prov['Type'] = 'bgcolor=#AAFFAA|Land'
        provinces[i] = prov

    provinces_rgb_map = {}
    for row in csv_rows(map_path('definitions')):
        try:
            number = int(row[0])
        except ValueError:
            continue
        if number < max_provinces:
            rgb = tuple(np.uint8(row[1:4]))
            provinces_rgb_map[rgb] = np.uint16(number)

    inland_sea_names = set()
    is_inland_sea = {}
    terrain_tree = parser.parse_file(map_path('terrain_definition'))
    for n, v in terrain_tree['categories']:
        inland_sea = v.has_pair('inland_sea', 'yes')
        if inland_sea:
            inland_sea_names.add(n.val)
        if 'terrain_override' in v.dictionary:
            is_inland_sea.update((n2.val, inland_sea)
                                 for n2 in v['terrain_override'])
    inland_sea_nums = set()
    for n, v in terrain_tree['terrain']:
        if v['type'].val in inland_sea_names:
            inland_sea_nums.update(n2.val for n2 in v['color'])

    pa = np.array(Image.open(str(map_path('provinces'))))
    pa = pa.view('u1,u1,u1')[..., 0]
    pa = np.vectorize(lambda x: provinces_rgb_map[tuple(x)],
                      otypes=[np.uint16])(pa)
    ta = np.array(Image.open(str(map_path('terrain'))))
    provs_not_found = []
    for number in provinces:
        if number in is_inland_sea:
            continue
        prov_indices = np.nonzero(pa == number)
        if len(prov_indices[0]):
            terrain_num = np.argmax(np.bincount(ta[prov_indices]))
            is_inland_sea[number] = terrain_num in inland_sea_nums
        else:
            provs_not_found.append(number)
    for number in provs_not_found:
        del provinces[number]

    for n in parser.parse_file(map_path('climate'))['impassable']:
        if n.val in provinces:
            provinces[n.val]['Type'] = 'bgcolor=#E5E5E5|Wasteland'
    for n in default_tree['sea_starts']:
        if n.val in provinces:
            if is_inland_sea.get(n.val):
                provinces[n.val]['Type'] = 'bgcolor=#CCDDFF|Inland sea'
            else:
                provinces[n.val]['Type'] = 'bgcolor=#CCDDFF|Sea'
    for n in default_tree['lakes']:
        if n.val in provinces:
            provinces[n.val]['Type'] = 'bgcolor=#CCDDFF|Lake'

    for n, v in parser.parse_file(map_path('continent')):
        name = localize(n.val)
        for n2 in v:
            if n2.val in provinces:
                provinces[n2.val]['Continent'] = name

    superregion = {}
    for n, v in parser.parse_file(map_path('superregion')):
        superregion.update((n2.val, n.val) for n2 in v)
    region = {}
    for n, v in parser.parse_file(map_path('region')):
        if 'areas' in v.dictionary:
            region.update((n2.val, n.val) for n2 in v['areas'])
    for n, v in parser.parse_file(map_path('area')):
        for n2 in v:
            if not isinstance(n2, Pair) and n2.val in provinces:
                provinces[n2.val]['Area'] = localize(n.val)
                if n.val in region:
                    this_region = region[n.val]
                    provinces[n2.val]['Region'] = localize(this_region)
                    if this_region in superregion:
                        this_super = superregion[this_region]
                        provinces[n2.val]['Superregion'] = localize(this_super)

    culture_group = {}
    for _, tree in parser.parse_files('common/cultures/*'):
        for n, v in tree:
            for n2, v2 in v:
                if (isinstance(v2, Obj) and
                    not re.match(r'((fe)?male|dynasty)_names', n2.val)):
                    culture_group[n2.val] = n.val

    for path in parser.files('history/provinces/*'):
        match = re.match(r'\d+', path.stem)
        if not match:
            continue
        number = int(match.group())
        if number >= max_provinces:
            continue
        tree = parser.parse_file(path)
        history = {}
        values = {}
        modifiers = []
        for n, v in tree:
            if isinstance(n.val, tuple):
                if n.val <= (1444, 11, 11):
                    history[n.val] = {}, []
                    for n2, v2 in v:
                        if n2.val == 'add_permanent_province_modifier':
                            history[n.val][1].append(v2['name'].val)
                        else:
                            history[n.val][0][n2.val] = v2
            elif n.val == 'add_permanent_province_modifier':
                modifiers.append(v['name'].val)
            else:
                values[n.val] = v
        for _, (history_values, history_modifiers) in sorted(history.items()):
            values.update(history_values)
            modifiers.extend(history_modifiers)
        dev = [values[x].val if x in values else 0
               for x in ['base_tax', 'base_production', 'base_manpower']]
        province = provinces[number]
        province['Development'] = str(sum(dev)) if sum(dev) else ''
        province['BT'] = str(dev[0]) if dev[0] else ''
        province['BP'] = str(dev[1]) if dev[1] else ''
        province['BM'] = str(dev[2]) if dev[2] else ''
        if 'trade_goods' in values:
            good = localize(values['trade_goods'].val)
            if good == 'Naval Supplies':
                good = 'Naval supplies'
            good_str = '[[File:{0}.png|24px|alt={0}|link={0}]]'.format(good)
            province['Trade good'] = good_str
        mods_str = ' / '.join(localize(x) for x in modifiers)
        province['Permanent modifiers'] = mods_str
        if 'owner' in values:
            owner = localize(values['owner'].val)
            owner_fmt = '[[File:{0}.png|24px|border|alt={0}|link={0}]] [[{0}]]'
            province['Owner (1444)'] = owner_fmt.format(owner)
        if 'religion' in values:
            religion = localize(values['religion'].val)
            religion_fmt = '[[File:{0}.png|24px|alt={0}|link={0}]]'
            province['Religion'] = religion_fmt.format(religion)
        if 'culture' in values:
            culture = values['culture'].val
            province['Culture'] = localize(culture)
            group = culture_group[culture]
            province['Culture Group'] = localize(group)

    for _, tree in parser.parse_files('common/tradenodes/*'):
        for n, v in tree:
            name = localize(n.val)
            if 'members' in v.dictionary:
                for n2 in v['members']:
                    provinces[n2.val]['Trade node'] = name

    return provinces

def format_output(provinces, headings):
    lines = ['{| class="wikitable sortable" '
              'style="font-size:95%; text-align:left"']
    lines.extend('! {}'.format(head) for head in headings)
    for prov in provinces.values():
        lines.append('|-')
        for head in headings:
            value = prov.get(head, '')
            lines.append(('|{}' if head == 'Type' else '| {}').format(value))
    lines.append('|}')
    lines.append('')
    return '\n'.join(lines)

@print_time
def main():
    provinces = analyze_provinces()

    tables = [
        (('ID,Name,Development,BT,BP,BM,'
          'Trade good,Trade node,Permanent modifiers').split(','),
         'eu4economic.txt'),
        ('ID,Name,Type,Continent,Superregion,Region,Area'.split(','),
         'eu4geographical.txt'),
        ('ID,Name,Owner (1444),Religion,Culture,Culture Group'.split(','),
         'eu4political.txt'),
    ]

    for headings, filename in tables:
        output = format_output(provinces, headings)
        output_file = rootpath / filename
        with output_file.open('w') as f:
            f.write(output)

if __name__ == '__main__':
    main()
