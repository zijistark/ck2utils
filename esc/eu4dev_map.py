#!/usr/bin/env python3

from collections import defaultdict
from pathlib import Path
import re
import sys
import matplotlib.cm
import matplotlib.colors
import numpy as np
from PIL import Image, ImageFont, ImageDraw
from ck2parser import rootpath, csv_rows, SimpleParser
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
    provs_to_label = set()
    colors = {
        'sea': np.uint8((51, 67, 85)),
        'desert': np.uint8((36, 36, 36))
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
            provs_to_label.add(number)

    province_values = {}
    for path in parser.files('history/provinces/*'):
        match = re.match(r'\d+', path.stem)
        if not match:
            continue
        number = int(match.group())
        if number >= max_provinces:
            continue
        if number in province_values:
            print('extra province history {}'.format(path), file=sys.stderr)
            continue
        properties = {
            'base_tax': 0,
            'base_production': 0,
            'base_manpower': 0,
        }
        history = defaultdict(list)
        for n, v in parser.parse_file(path):
            if n.val in properties:
                properties[n.val] = v.val
            elif isinstance(n.val, tuple) and n.val <= (1444, 11, 11):
                history[n.val].extend((n2.val, v2.val) for n2, v2 in v
                                      if n2.val in properties)
        properties.update(p2 for _, v in sorted(history.items()) for p2 in v)
        province_values[number] = properties

    for n in parser.parse_file(climate_path)['impassable']:
        prov_color_lut[int(n.val)] = colors['desert']
        provs_to_label.discard(int(n.val))
    for n in default_tree['sea_starts']:
        prov_color_lut[int(n.val)] = colors['sea']
        provs_to_label.discard(int(n.val))
    for n in default_tree['lakes']:
        prov_color_lut[int(n.val)] = colors['sea']
        provs_to_label.discard(int(n.val))
    for n in default_tree['only_used_for_random']:
        provs_to_label.discard(int(n.val))

    image = Image.open(str(provinces_path))
    a = np.array(image).view('u1,u1,u1')[..., 0]
    b = np.vectorize(lambda x: rgb_number_map[tuple(x)], otypes=[np.uint16])(a)
    font = ImageFont.truetype(str(rootpath / 'ck2utils/esc/NANOTYPE.ttf'), 16)
    mod = parser.moddirs[0].name.lower() + '_' if parser.moddirs else ''
    borders_path = rootpath / (mod + 'eu4borderlayer.png')
    borders = Image.open(str(borders_path))

    for value_func, name in [(lambda x: sum(x.values()), ''),
                             (lambda x: x['base_tax'], 'tax'),
                             (lambda x: x['base_production'], 'prod'),
                             (lambda x: x['base_manpower'], 'man')]:
        province_value = {n: value_func(province_values[n])
                          for n in provs_to_label}
        vmin, vmax = 0, max(province_value.values())
        cmap = matplotlib.cm.get_cmap('plasma')
        norm = matplotlib.colors.Normalize(vmin, vmax * 4 / 3)
        colormap = matplotlib.cm.ScalarMappable(cmap=cmap, norm=norm)
        for number, value in province_value.items():
            prov_color_lut[number] = colormap.to_rgba(value, bytes=True)[:3]

        txt = Image.new('RGBA', image.size, (0, 0, 0, 0))
        lines = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw_txt = ImageDraw.Draw(txt)
        draw_lines = ImageDraw.Draw(lines)
        maxlen = len(str(vmax))
        e = {(n * 4 - 1, 5): np.ones_like(b, bool)
             for n in range(1, maxlen + 1)}
        for number in sorted(provs_to_label):
            print('\r' + str(number), end='', file=sys.stderr)
            value = province_value[number]
            size = len(str(value)) * 4 - 1, 5
            c = np.nonzero(b == number)
            if len(c[0]) == 0:
                continue
            center = np.mean(c[1]), np.mean(c[0])
            pos = [int(round(max(0, min(center[0] - size[0] / 2,
                                        image.width - size[0])))),
                   int(round(max(0, min(center[1] - size[1] / 2,
                                        image.height - size[1]))))]
            pos[2:] = pos[0] + size[0], pos[1] + size[1]
            if not e[size][pos[1], pos[0]]:
                x1, x2 = max(0, pos[0] - 1), min(pos[0] + 2, image.width)
                y1, y2 = max(0, pos[1] - 1), min(pos[1] + 2, image.height)
                if not np.any(e[size][y1:y2, x1:x2]):
                    x1, y1, (x2, y2) = 0, 0, image.size
                f = np.nonzero(e[size][y1:y2, x1:x2])
                g = (f[0] - pos[1]) ** 2 + (f[1] - pos[0]) ** 2
                pos[:2] = np.transpose(f)[np.argmin(g)][::-1] + [x1, y1]
                pos[2:] = pos[0] + size[0], pos[1] + size[1]
            draw_txt.text((pos[0], pos[1] - 6), str(value),
                          fill=(255, 255, 255, 255), font=font)
            for size2 in e:
                rows = slice(max(pos[1] - size2[1] - 1, 0), pos[3] + 2)
                cols = slice(max(pos[0] - size2[0] - 1, 0), pos[2] + 2)
                e[size2][rows, cols] = False
            x = int(round(pos[0] + size[0] / 2))
            y = int(round(pos[1] + size[1] / 2))
            if b[y, x] != number:
                d = (c[0] - y) ** 2 + (c[1] - x) ** 2
                dest = tuple(np.transpose(c)[np.argmin(d)][::-1])
                start = (max(pos[0] - 1, min(dest[0], pos[2])),
                         max(pos[1] - 1, min(dest[1], pos[3])))
                if start != dest:
                    print('\rline drawn for {}'.format(number),
                          file=sys.stderr)
                    draw_lines.line([start, dest], fill=(176, 176, 176))
        print('', file=sys.stderr)
        out = Image.fromarray(prov_color_lut[b])
        out.paste(borders, mask=borders)
        out.paste(lines, mask=lines)
        out.paste(txt, mask=txt)
        out_path = rootpath / (mod + 'eu4dev{}_map.png'.format(name))
        out.save(str(out_path))

if __name__ == '__main__':
    main()
