#!/usr/bin/env python3

from collections import deque
import math
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
    rgb_number_map = {}
    # number_name_map = {}
    default_tree = parser.parse_file('map/default.map')
    provinces_path = parser.file('map/' + default_tree['provinces'].val)
    max_provinces = default_tree['max_provinces'].val
    for row in csv_rows(parser.file('map/' + default_tree['definitions'].val)):
        try:
            number = int(row[0])
        except ValueError:
            continue
        if number < max_provinces:
            rgb_number_map[tuple(np.uint8(row[1:4]))] = np.uint16(number)
    #       number_name_map[number] = row[4]
    # num_county_map = {}
    # for path in parser.files('history/provinces/* - *.txt'):
    #     number, name = path.stem.split(' - ')
    #     number = int(number)
    #     if number_name_map.get(number) == name:
    #         try:
    #             num_county_map[number] = parser.parse_file(path)['title'].val
    #         except KeyError:
    #             continue
    image = Image.open(str(provinces_path))
    a = np.array(image)
    b = np.apply_along_axis(
        lambda x: rgb_number_map.get(tuple(x), np.uint16(0)), 2, a)
    txt = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw_txt = ImageDraw.Draw(txt)
    font = ImageFont.truetype(str(rootpath / 'ck2utils/esc/NANOTYPE.ttf'), 16)
    e = {(n * 4 - 1, 5): np.ones_like(b, dtype=bool) for n in range(1, 5)}
    for number in sorted(rgb_number_map.values()):
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
                draw.line([start, dest], fill=(192, 192, 192))
    print('', file=sys.stderr)
    image.paste(txt, mask=txt)
    mod = parser.moddirs[0].name.lower() + '_' if parser.moddirs else ''
    out_path = rootpath / (mod + 'province_id_map.png')
    image.save(str(out_path))

if __name__ == '__main__':
    main()
