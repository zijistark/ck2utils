#!/usr/bin/env python3

from pathlib import Path
import sys
import numpy as np
from PIL import Image
from ck2parser import rootpath, SimpleParser
from print_time import print_time

@print_time
def main():
    parser = SimpleParser()
    if len(sys.argv) > 1:
        parser.moddirs.append(Path(sys.argv[1]))
    default_tree = parser.parse_file('map/default.map')
    provinces_path = parser.file('map/' + default_tree['provinces'].val)
    a = np.array(Image.open(str(provinces_path)))
    b = np.zeros((a.shape[0], a.shape[1], 4), np.uint8)
    for i, j in np.ndindex(a.shape[:2]):
        pixel = tuple(a[i, j])
        if any(pixel):
            for coords in [(i - 1, j - 1), (i - 1, j), (i, j - 1)]:
                try:
                    neighbor = tuple(a[coords])
                except IndexError:
                    continue
                if neighbor != pixel:
                    b[i, j, 3] = 255
                    break
        else:
            b[i, j, 3] = 255
    out_image = Image.fromarray(b)
    mod = parser.moddirs[0].name.lower() + '_' if parser.moddirs else ''
    out_path = rootpath / (mod + 'borderlayer.png')
    out_image.save(str(out_path))

if __name__ == '__main__':
    main()
