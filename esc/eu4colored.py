#!/usr/bin/env python3

import numpy as np
from PIL import Image
from ck2parser import rootpath, csv_rows, SimpleParser
from localpaths import eu4dir
from print_time import print_time

def map(where, name='', crop=True):
    if isinstance(where, str):
        where = where.split()
    prov_color_lut = np.copy(prov_color_lut_base)
    provs = {y for x in where for y in (contains.get(x, None) or (int(x),))}
    for prov in provs:
        prov_color_lut[prov] = colors['important']
    out_a = prov_color_lut[prov_id]
    out = Image.fromarray(out_a)
    out.paste(borders, mask=borders)
    if crop:
        c = (out_a == colors['important']).nonzero()
        out = out.crop((c[1].min() - margin, c[0].min() - margin,
                        c[1].max() + 1 + margin, c[0].max() + 1 + margin))
    out_path = rootpath / 'eu4{}.png'.format(name)
    out.save(str(out_path))


colors = {
    'land': np.uint8((127, 127, 127)),
    'sea': np.uint8((68, 107, 163)),
    'desert': np.uint8((94, 94, 94)),
    'important': np.uint8((220, 138, 57))
}

margin = 10

parser = SimpleParser()
parser.basedir = eu4dir
default_tree = parser.parse_file('map/default.map')
max_provinces = default_tree['max_provinces'].val
map_path = lambda key: parser.file('map/' + default_tree[key].val)
rgb_number_map = {}
for row in csv_rows(map_path('definitions')):
    try:
        number = int(row[0])
    except ValueError:
        continue
    if number < max_provinces:
        rgb = tuple(np.uint8(row[1:4]))
        rgb_number_map[rgb] = np.uint16(number)
prov_rgb = np.array(Image.open(str(map_path('provinces'))))
prov_rgb = prov_rgb.view('u1,u1,u1')[..., 0]
prov_id = np.vectorize(lambda x: rgb_number_map[tuple(x)],
                       otypes=[np.uint16])(prov_rgb)
borders_path = rootpath / 'eu4borderlayer.png'
borders = Image.open(str(borders_path))
prov_color_lut_base = np.full(max_provinces, colors['land'], '3u1')
for n in parser.parse_file(map_path('climate'))['impassable']:
    prov_color_lut_base[int(n.val)] = colors['desert']
for n in default_tree['sea_starts']:
    prov_color_lut_base[int(n.val)] = colors['sea']
for n in default_tree['lakes']:
    prov_color_lut_base[int(n.val)] = colors['sea']
contains = {}
# for n, v in parser.parse_file(map_path('continent')):
#     contains[n.val] = {n2.val for n2 in v}
for n, v in parser.parse_file(map_path('area')):
    contains[n.val] = {n2.val for n2 in v if hasattr(n2, 'val')}
for n, v in parser.parse_file(map_path('region')):
    contains[n.val] = {n3 for n2 in v.get('areas', [])
                       for n3 in contains[n2.val]}
for n, v in parser.parse_file(map_path('superregion')):
    contains[n.val] = {n3 for n2 in v for n3 in contains[n2.val]}
