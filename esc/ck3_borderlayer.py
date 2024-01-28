#!/usr/bin/env python3

from pathlib import Path
import re
import sys
import numpy as np
from PIL import Image
from ck3parser import rootpath, SimpleParser
from print_time import print_time


def parse_default_map(default_map_path):
    needed = {'definitions', 'provinces', 'adjacencies'}
    paths = {}
    with open(str(default_map_path)) as f:
        for line in f:
            if match := re.match(r'(\w+) = "([^"]*)"', line):
                k, v = match.groups()
                if k in needed:
                    paths[k] = 'map_data/' + v
                    needed.remove(k)
                    if not needed:
                        break
    return paths

@print_time
def main():
    parser = SimpleParser()
    if len(sys.argv) > 1:
        parser.moddirs.append(Path(sys.argv[1]))
    map_data_paths = parse_default_map(parser.file('map_data/default.map'))
    provinces_path = parser.file(map_data_paths['provinces'])
    width = parser.parse_file(
        'common/defines/graphic/00_graphics.txt')['NCamera']['PANNING_WIDTH'].val
    image = Image.open(str(provinces_path))  # provinces.png
    cropped = image.crop((0, 0, width, image.height))
    a = np.array(cropped)
    n = np.pad(a, ((1, 0), (0, 0), (0, 0)), 'edge')[:-1] # shifted south 1 pixel
    w = np.pad(a, ((0, 0), (1, 0), (0, 0)), 'edge')[:, :-1]  # shifted east 1 pixel
    nw = np.pad(a, ((1, 0), (1, 0), (0, 0)), 'edge')[:-1, :-1]  # shifted both 1 pixel
    b = np.zeros((a.shape[0], a.shape[1], 4), np.uint8)  # output RGBA
    mask = np.any((a != n) | (a != w) | (a != nw), axis=2) # get boolean mask of border pixels
    mask[np.nonzero(np.all(a == 0, axis=2))] = True
    b[:, :, 3][mask] = 255 # set border pixel transparency to opaque
    out_image = Image.fromarray(b)
    mod = parser.moddirs[0].name.lower() + '_' if parser.moddirs else ''
    out_path = rootpath / (mod + 'ck3_borderlayer.png')
    out_image.save(str(out_path))

if __name__ == '__main__':
    main()
