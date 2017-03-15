#!/usr/bin/env python3

from pathlib import Path
import sys
from PIL import Image, ImageFont, ImageDraw
from ck2parser import rootpath, SimpleParser
from print_time import print_time



@print_time
def main():
    parser = SimpleParser()
    if len(sys.argv) > 1:
        parser.moddirs.append(Path(sys.argv[1]))
    default_tree = parser.parse_file('map/default.map')
    provinces_path = parser.file('map/' + default_tree['provinces'].val)
    positions_path = parser.file('map/' + default_tree['positions'].val)
    image = Image.open(str(provinces_path))
    draw = ImageDraw.Draw(image)
    font = None and ImageFont.truetype('times.ttf', 10)
    for n, v in parser.parse_file(positions_path):
        number = str(n.val)
        textsize = draw.textsize(number, font=font)
        pos = v['position'].contents[6:8]
        text_x = pos[0].val - textsize[0] / 2
        text_y = image.height - pos[1].val - textsize[1] / 2
        draw.text((text_x, text_y), number, font=font)
    mod = parser.moddirs[0].name.lower() + '_' if parser.moddirs else ''
    out_path = rootpath / (mod + 'province_id_map.png')
    image.save(str(out_path))

if __name__ == '__main__':
    main()
