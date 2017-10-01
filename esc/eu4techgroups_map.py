#!/usr/bin/env python3

from collections import defaultdict
from pathlib import Path
import re
import sys
import numpy as np
from PIL import Image
import spectra
from ck2parser import rootpath, csv_rows, SimpleParser, Obj
from localpaths import eu4dir
from print_time import print_time

TECH_GROUP_COLOR = {
    'western': '#ccc000',           'eastern': '#b38000',
    'ottoman': '#7ecb78',           'muslim': '#00cc00',
    'indian': '#0099cc',            'east_african': '#f98c0f',
    'central_african': '#633c27',   'chinese': '#cc4c00',
    'nomad_group': '#662600',       'sub_saharan': '#804c4c',
    'north_american': '#d98c8c',    'mesoamerican': '#800000',
    'south_american': '#006600',    'andean': '#8c4c8c'
}

@print_time
def main():
    parser = SimpleParser()
    parser.basedir = eu4dir
    if len(sys.argv) > 1:
        parser.moddirs.append(Path(sys.argv[1]))
    rgb_number_map = {}
    default_tree = parser.parse_file('map/default.map')
    provinces_path = parser.file('map/' + default_tree['provinces'].val)
    climate_path = parser.file('map/' + default_tree['climate'].val)
    max_provinces = default_tree['max_provinces'].val
    colors = {
        'land': np.uint8((127, 127, 127)),
        'sea': np.uint8((68, 107, 163)),
        'desert': np.uint8((94, 94, 94))
    }
    prov_color_lut = np.full(max_provinces, colors['land'], '3u1')
    for row in csv_rows(parser.file('map/' + default_tree['definitions'].val)):
        try:
            number = int(row[0])
        except ValueError:
            continue
        if number < max_provinces:
            rgb = tuple(np.uint8(row[1:4]))
            rgb_number_map[rgb] = np.uint16(number)

    tag_tech_group = {}
    for path, tree in parser.parse_files('history/countries/*'):
        tag = path.stem[:3]
        properties = {'technology_group': None}
        history = defaultdict(list)
        for n, v in tree:
            if n.val in properties:
                properties[n.val] = v.val
            elif isinstance(n.val, tuple) and n.val <= (1444, 11, 11):
                history[n.val].extend((n2.val, v2.val) for n2, v2 in v
                                      if n2.val in properties)
        properties.update(p2 for _, v in sorted(history.items()) for p2 in v)
        tag_tech_group[tag] = properties['technology_group']

    for path in parser.files('history/provinces/*'):
        match = re.match(r'\d+', path.stem)
        if not match:
            continue
        number = int(match.group())
        if number >= max_provinces:
            continue
        properties = {'owner': 'XXX'}
        history = defaultdict(list)
        for n, v in parser.parse_file(path):
            if n.val in properties:
                properties[n.val] = v.val
            elif isinstance(n.val, tuple) and n.val <= (1444, 11, 11):
                history[n.val].extend((n2.val, v2.val) for n2, v2 in v
                                      if n2.val in properties)
        properties.update(p2 for _, v in sorted(history.items()) for p2 in v)
        owner = properties['owner']
        if owner in tag_tech_group:
            tech_group = tag_tech_group[owner]
            color = spectra.html(TECH_GROUP_COLOR[tech_group])
            upscaled = [round(x * 255) for x in color.clamped_rgb]
            prov_color_lut[number] = np.uint8(upscaled)

    for n in parser.parse_file(climate_path)['impassable']:
        prov_color_lut[int(n.val)] = colors['desert']
    for n in default_tree['sea_starts']:
        prov_color_lut[int(n.val)] = colors['sea']
    for n in default_tree['lakes']:
        prov_color_lut[int(n.val)] = colors['sea']

    image = Image.open(str(provinces_path))
    a = np.array(image).view('u1,u1,u1')[..., 0]
    b = np.vectorize(lambda x: rgb_number_map[tuple(x)], otypes=[np.uint16])(a)
    mod = parser.moddirs[0].name.lower() + '_' if parser.moddirs else ''
    borders_path = rootpath / (mod + 'eu4borderlayer.png')
    borders = Image.open(str(borders_path))

    out = Image.fromarray(prov_color_lut[b])
    out.paste(borders, mask=borders)
    out_path = rootpath / (mod + 'eu4techgroups_map.png')
    out.save(str(out_path))

if __name__ == '__main__':
    main()
