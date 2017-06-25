#!/usr/bin/env python3

from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageFont, ImageDraw
from ck2parser import rootpath, csv_rows, SimpleParser
from print_time import print_time

@print_time
def main():
    parser = SimpleParser()
    if len(sys.argv) > 1:
        parser.moddirs.append(Path(sys.argv[1]))
    default_tree = parser.parse_file('map/default.map')
    provinces_path = parser.file('map/' + default_tree['provinces'].val)
    max_provinces = default_tree['max_provinces'].val
    county_provs = set()
    colors = {
        'land': np.uint8((127, 127, 127)),
        'sea': np.uint8((51, 67, 85)),
        'desert': np.uint8((36, 36, 36)),
        'mountains': np.uint8((0, 0, 0))
    }
    rgb_number_map = {
        tuple(np.uint8((0, 0, 0))): np.uint16(0),
        tuple(np.uint8((255, 255, 255))): np.uint16(max_provinces)
    }
    prov_color_lut = np.full(max_provinces + 1, colors['desert'], '3u1')
    prov_color_lut[0] = colors['mountains']
    prov_color_lut[max_provinces] = colors['sea']
    for row in csv_rows(parser.file('map/' + default_tree['definitions'].val)):
        try:
            number = int(row[0])
        except ValueError:
            continue
        if number < max_provinces:
            rgb = tuple(np.uint8(row[1:4]))
            rgb_number_map[rgb] = np.uint16(number)
            path = 'history/provinces/{} - {}.txt'.format(number, row[4])
            try:
                if 'title' in parser.parse_file(path).dictionary:
                    county_provs.add(number)
                    prov_color_lut[number] = colors['land']
            except StopIteration:
                pass
    for n, v in default_tree:
        if n.val == 'sea_zones':
            i, j = (int(n2.val) for n2 in v)
            prov_color_lut[i:j + 1] = colors['sea']
    noncounty_provs = set(range(1, max_provinces)) - county_provs

    image = Image.open(str(provinces_path))
    a = np.array(image).view(dtype='u1,u1,u1')[..., 0]
    b = np.vectorize(lambda x: rgb_number_map[tuple(x)], otypes=[np.uint16])(a)
    font = ImageFont.truetype(str(rootpath / 'ck2utils/esc/NANOTYPE.ttf'), 16)
    mod = parser.moddirs[0].name.lower() + '_' if parser.moddirs else ''
    borders_path = rootpath / (mod + 'borderlayer.png')
    borders = Image.open(str(borders_path))

    for provs, water in [(county_provs, False), (noncounty_provs, True)]:
        txt = Image.new('RGBA', image.size, (0, 0, 0, 0))
        lines = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw_txt = ImageDraw.Draw(txt)
        draw_lines = ImageDraw.Draw(lines)
        maxlen = len(str(max(provs)))
        e = {(n * 4 - 1, 5): np.ones_like(b, bool)
             for n in range(1, maxlen + 1)}
        for number in sorted(provs):
            print('\r' + str(number), end='', file=sys.stderr)
            size = len(str(number)) * 4 - 1, 5
            c = np.nonzero(b == number)
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
            draw_txt.text((pos[0], pos[1] - 6), str(number),
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
                    draw_lines.line([start, dest], fill=(192, 192, 192))
        print('', file=sys.stderr)
        out = Image.fromarray(prov_color_lut[b])
        out.paste(borders, mask=borders)
        out.paste(lines, mask=lines)
        out.paste(txt, mask=txt)
        mode = '_water' if water else ''
        out_path = rootpath / (mod + 'province_id_map' + mode + '.png')
        out.save(str(out_path))

if __name__ == '__main__':
    main()
