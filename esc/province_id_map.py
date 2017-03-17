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
            # number_name_map[number] = row[4]
    # number_county_map = {}
    # for path in parser.files('history/provinces/* - *.txt'):
    #     number, name = path.stem.split(' - ')
    #     number = int(number)
    #     if number_name_map.get(number) == name:
    #         try:
    #             number_county_map[number] = parser.parse_file(path)['title'].val
    #         except KeyError:
    #             continue
    image = Image.open(str(provinces_path))
    a = np.array(image)
    b = np.apply_along_axis(
        lambda x: rgb_number_map.get(tuple(x), np.uint16(0)), 2, a)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(rootpath / 'ck2utils/esc/NANOTYPE.ttf'), 16)
    labels = []
    for number in sorted(rgb_number_map.values()):
        size = draw.textsize(str(number), font=font)
        c = np.nonzero(b == number)
        center = np.mean(c[1]), np.mean(c[0])
        pos = [center[0] - size[0] / 2, center[1] - size[1] / 2,
               center[0] + size[0] / 2, center[1] + size[1] / 2]
        rad = 0
        ang = -15
        opos = list(pos)
        while True:
            if (0 <= pos[0] and pos[2] <= image.width and
                0 <= pos[1] and pos[3] <= image.height):
                for pos2 in labels:
                    if (pos[2] > pos2[0] and pos[0] < pos2[2] and
                        pos[1] < pos2[3] and pos[3] > pos2[1]):
                        break
                else:
                    break
            ang = (ang + 15) % 360
            if ang == 0:
                rad += 2
            pos[0] = opos[0] + rad * math.cos(math.radians(ang))
            pos[1] = opos[1] + rad * math.sin(math.radians(ang))
            pos[2:] = pos[0] + size[0], pos[1] + size[1]
        print(number, rad, ang)
        draw.text(tuple(pos[:2]), str(number), font=font, fill=(255, 255, 255))
        labels.append(pos)
        if b[int(pos[1] + size[1] / 2), int(pos[0] + size[0] / 2)] != number:
            d = ((c[1] - (pos[0] + size[0] / 2)) ** 2 +
                 (c[0] - (pos[1] + size[1] / 2)) ** 2)
            dest = tuple(np.transpose(c)[np.argmin(d)][::-1])
            start = (max(pos[0] - 1, min(dest[0], pos[2] + 1)),
                     max(pos[1] - 1, min(dest[1], pos[3] + 1)))
            if start != dest:
                draw.line([start, dest], fill=(255, 255, 255))
    mod = parser.moddirs[0].name.lower() + '_' if parser.moddirs else ''
    out_path = rootpath / (mod + 'province_id_map.png')
    image.save(str(out_path))

if __name__ == '__main__':
    main()
