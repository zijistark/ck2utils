#!/usr/bin/env python3

from collections import defaultdict
import itertools
import math
from pathlib import Path
import re
import sys
import urllib.request
import numpy as np
from PIL import Image, ImageFont, ImageDraw
import spectra
from ck2parser import rootpath, csv_rows, SimpleParser, Obj
from localpaths import eu4dir
from print_time import print_time

CULTURE_GROUP_COLOR = {
    'germanic': '#DC8A39',
    'scandinavian': '#3F7DD6',
    'british': '#36A79C',
    'gaelic': '#DB7C8B',
    'latin': '#39A065',
    'iberian': '#C28C56',
    'french': '#C7AF0C',
    'finno_ugric': '#459DD0',
    'south_slavic': '#75A5BC',
    'west_slavic': '#CEB561',
    'carpathian': '#C3959B',
    'east_slavic': '#5E88BF',
    'baltic': '#E7B50C',
    'byzantine': '#926C92',
    'caucasian': '#4582CB',
    'turko_semitic': '#3B9E7D',
    'maghrebi': '#0490B2',
    'iranian': '#BF7185',
    'altaic': '#939D4C',
    'central_american': '#1A35B1',
    'maya': '#7D5C6E',
    'otomanguean': '#79A26D',
    'andean_group': '#B68664',
    'je_tupi': '#C9614A',
    'je': '#745C27',
    'maranon': '#216589',
    'chibchan': '#81B17D',
    'mataco': '#766397',
    'araucanian': '#17728F',
    'carribean': '#6EAD81',
    'eskaleut': '#941E46',
    'central_algonquian': '#645E7D',
    'plains_algonquian': '#287942',
    'eastern_algonquian': '#2959AE',
    'iroquoian': '#F0A782',
    'siouan': '#C14136',
    'caddoan': '#76C199',
    'muskogean': '#5DB44C',
    'sonoran': '#78948C',
    'na_dene': '#A18B28',
    'penutian': '#246DC2',
    'east_asian': '#8CCF74',
    'korean_g': '#82194A',
    'japanese_g': '#B2A38F',
    'mon_khmer': '#9A8123',
    'malay': '#75A143',
    'thai': '#844666',
    'burman': '#724667',
    'pacific': '#5E7537',
    'eastern_aryan': '#3E7ABD',
    'hindusthani': '#C11A0E',
    'western_aryan': '#DC8A39',
    'dravidian': '#889D17',
    'central_indic': '#30A433',
    'mande': '#B68664',
    'sahelian': '#276C8C',
    'west_african': '#709669',
    'southern_african': '#BF7185',
    'kongo_group': '#6B5EA9',
    'great_lakes_group': '#79A26D',
    'african': '#75A5BC',
    'cushitic': '#CA7055',
    'sudanese': '#68898C',
    'evenks': '#DC969E',
    'kamchatkan_g': '#A64839',
    'tartar': '#C7AF0C'
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
    prov_color_lut = np.empty(max_provinces, '3u1')
    for row in csv_rows(parser.file('map/' + default_tree['definitions'].val)):
        try:
            number = int(row[0])
        except ValueError:
            continue
        if number < max_provinces:
            rgb = tuple(np.uint8(row[1:4]))
            rgb_number_map[rgb] = np.uint16(number)

    group_cultures = defaultdict(list)
    for _, tree in parser.parse_files('common/cultures/*'):
        for n, v in tree:
            if n.val in CULTURE_GROUP_COLOR:
                for n2, v2 in v:
                    if (isinstance(v2, Obj) and
                        not re.match(r'((fe)?male|dynasty)_names', n2.val)):
                        group_cultures[n.val].append(n2.val)

    culture_color = {'noculture': colors['land']}
    spherical_code = {
        0: [],
        1: [(0, 0, 1)],
        2: [(0, 0, 1), (0, 0, -1)],
        3: [(1, 0, 0), (-1 / 2, math.sqrt(3) / 2, 0),
            (-1 / 2, -math.sqrt(3) / 2, 0)]
    }
    out_of_gamut = 0
    for group, cultures in group_cultures.items():
        group_color = spectra.html(CULTURE_GROUP_COLOR[group]).to('lab').values
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
    culture_count = sum(len(x) for x in group_cultures.values())
    print('Out of gamut: {:.2%}'.format(out_of_gamut / culture_count),
          file=sys.stderr)

    for path in parser.files('history/provinces/*'):
        match = re.match(r'\d+', path.stem)
        if not match:
            continue
        number = int(match.group())
        if number >= max_provinces:
            continue
        tree = parser.parse_file(path)
        properties = {'culture': 'noculture'}
        history = defaultdict(list)
        for n, v in tree:
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
    font = ImageFont.truetype(str(rootpath / 'ck2utils/esc/NANOTYPE.ttf'), 16)
    mod = parser.moddirs[0].name.lower() + '_' if parser.moddirs else ''
    borders_path = rootpath / (mod + 'eu4borderlayer.png')
    borders = Image.open(str(borders_path))

    out = Image.fromarray(prov_color_lut[b])
    out.paste(borders, mask=borders)
    out_path = rootpath / (mod + 'eu4culture_map.png')
    out.save(str(out_path))

if __name__ == '__main__':
    main()
