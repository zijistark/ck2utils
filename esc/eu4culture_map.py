#!/usr/bin/env python3

from collections import defaultdict
import math
from pathlib import Path
import re
import sys
import urllib.request
import numpy as np
from PIL import Image
import spectra
from ck2parser import rootpath, csv_rows, SimpleParser, Obj
from localpaths import eu4dir
from print_time import print_time

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
    prov_color_lut = np.empty(max_provinces, '3u1')
    for row in csv_rows(parser.file('map/' + default_tree['definitions'].val)):
        try:
            number = int(row[0])
        except ValueError:
            continue
        if number < max_provinces:
            rgb = tuple(np.uint8(row[1:4]))
            rgb_number_map[rgb] = np.uint16(number)

    grouped_cultures = []
    for _, tree in parser.parse_files('common/cultures/*'):
        for n, v in tree:
            cultures = []
            for n2, v2 in v:
                if (isinstance(v2, Obj) and
                    not re.match(r'((fe)?male|dynasty)_names', n2.val)):
                    cultures.append(n2.val)
            grouped_cultures.append(cultures)

    region_colors = []
    for _, tree in parser.parse_files('common/region_colors/*'):
        for n, v in tree:
            region_colors.append(spectra.rgb(*(n2.val / 255 for n2 in v)))

    culture_color = {'noculture': colors['land']}
    spherical_code = {
        1: [(0, 0, 1)],
        2: [(0, 0, 1), (0, 0, -1)],
        3: [(1, 0, 0), (-1 / 2, math.sqrt(3) / 2, 0),
            (-1 / 2, -math.sqrt(3) / 2, 0)]
    }
    out_of_gamut = 0
    for i, cultures in enumerate(grouped_cultures):
        group_color = region_colors[i + 1].to('lab').values
        num_cultures = len(cultures)
        try:
            code = spherical_code[num_cultures]
        except KeyError:
            url_fmt = 'http://neilsloane.com/packings/dim3/pack.3.{}.txt'
            url = url_fmt.format(num_cultures)
            with urllib.request.urlopen(url) as response:
                txt = response.read()
            floats = [float(x) for x in txt.split()]
            code = list(zip(*[iter(floats)]*3))
            spherical_code[num_cultures] = code
        for culture, coords in zip(cultures, code):
            offset_lab = [a + b * 14 for a, b in zip(group_color, coords)]
            color = spectra.lab(*offset_lab)
            if color.rgb != color.clamped_rgb:
                out_of_gamut += 1
            upscaled = [round(x * 255) for x in color.clamped_rgb]
            culture_color[culture] = np.uint8(upscaled)
    culture_count = sum(len(x) for x in grouped_cultures)
    print('Out of gamut: {:.2%}'.format(out_of_gamut / culture_count),
          file=sys.stderr)

    for path in parser.files('history/provinces/*'):
        match = re.match(r'\d+', path.stem)
        if not match:
            continue
        number = int(match.group())
        if number >= max_provinces:
            continue
        properties = {'culture': 'noculture'}
        history = defaultdict(list)
        for n, v in parser.parse_file(path):
            if n.val in properties:
                properties[n.val] = v.val
            elif isinstance(n.val, tuple) and n.val <= (1444, 11, 11):
                history[n.val].extend((n2.val, v2.val) for n2, v2 in v
                                      if n2.val in properties)
        properties.update(p2 for _, v in sorted(history.items()) for p2 in v)
        prov_color_lut[number] = culture_color[properties['culture']]

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
    out_path = rootpath / (mod + 'eu4culture_map.png')
    out.save(str(out_path))

if __name__ == '__main__':
    main()
