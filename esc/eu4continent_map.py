#!/usr/bin/env python3

from pathlib import Path
import sys
import numpy as np
from PIL import Image
import spectra
from ck2parser import rootpath, csv_rows, SimpleParser
from localpaths import eu4dir
from print_time import print_time

CONTINENT_COLOR = {
    'europe': '#7fffff',
    'asia': '#ffff7f',
    'africa': '#7f7fff',
    'north_america': '#ff7f7f',
    'south_america': '#7fff7f',
    'oceania': '#ff7fff',
    'new_world': '#000000'
}

@print_time
def main():
    parser = SimpleParser()
    parser.basedir = eu4dir
    if len(sys.argv) > 1:
        parser.moddirs.append(Path(sys.argv[1]))
    rgb_number_map = {}
    default_tree = parser.parse_file('map/default.map')
    max_provinces = default_tree['max_provinces'].val
    map_path = lambda key: parser.file('map/' + default_tree[key].val)
    colors = {
        'land': np.uint8((127, 127, 127)),
        'sea': np.uint8((68, 107, 163)),
        'desert': np.uint8((94, 94, 94))
    }
    prov_color_lut = np.full(max_provinces, colors['land'], '3u1')
    for row in csv_rows(map_path('definitions')):
        try:
            number = int(row[0])
        except ValueError:
            continue
        if number < max_provinces:
            rgb = tuple(np.uint8(row[1:4]))
            rgb_number_map[rgb] = np.uint16(number)
    for n in parser.parse_file(map_path('climate'))['impassable']:
        prov_color_lut[int(n.val)] = colors['desert']
    for n in default_tree['sea_starts']:
        prov_color_lut[int(n.val)] = colors['sea']
    for n in default_tree['lakes']:
        prov_color_lut[int(n.val)] = colors['sea']
    for n, v in parser.parse_file(map_path('continent')):
        color = spectra.html(CONTINENT_COLOR[n.val])
        upscaled = np.uint8([round(x * 255) for x in color.clamped_rgb])
        for n2 in v:
            prov_color_lut[n2.val] = upscaled
    a = np.array(Image.open(str(map_path('provinces'))))
    a = a.view('u1,u1,u1')[..., 0]
    b = np.vectorize(lambda x: rgb_number_map[tuple(x)], otypes=[np.uint16])(a)
    mod = parser.moddirs[0].name.lower() + '_' if parser.moddirs else ''
    borders_path = rootpath / (mod + 'eu4borderlayer.png')
    borders = Image.open(str(borders_path))

    out = Image.fromarray(prov_color_lut[b])
    out.paste(borders, mask=borders)
    out_path = rootpath / (mod + 'eu4continent_map.png')
    out.save(str(out_path))

if __name__ == '__main__':
    main()
