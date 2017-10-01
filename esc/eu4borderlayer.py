#!/usr/bin/env python3

from pathlib import Path
import sys
import numpy as np
from PIL import Image
from ck2parser import rootpath, SimpleParser
from localpaths import eu4dir
from print_time import print_time

@print_time
def main():
    parser = SimpleParser()
    parser.basedir = eu4dir
    if len(sys.argv) > 1:
        parser.moddirs.append(Path(sys.argv[1]))
    default_tree = parser.parse_file('map/default.map')
    provinces_path = parser.file('map/' + default_tree['provinces'].val)
    a = np.array(Image.open(str(provinces_path))) # provinces.bmp
    n = np.pad(a, ((1, 0), (0, 0), (0, 0)), 'edge')[:-1] # shifted south 1 pixel
    w = np.pad(a, ((0, 0), (1, 0), (0, 0)), 'edge')[:, :-1]  # shifted east 1 pixel
    nw = np.pad(a, ((1, 0), (1, 0), (0, 0)), 'edge')[:-1, :-1]  # shifted both 1 pixel
    b = np.zeros((a.shape[0], a.shape[1], 4), np.uint8)  # output RGBA
    mask = np.any((a != n) | (a != w) | (a != nw), axis=2) # get boolean mask of border pixels
    mask[np.nonzero(np.all(a == 0, axis=2))] = True
    b[:, :, 3][mask] = 255 # set border pixel transparency to opaque
    out_image = Image.fromarray(b)
    mod = parser.moddirs[0].name.lower() + '_' if parser.moddirs else ''
    out_path = rootpath / (mod + 'eu4borderlayer.png')
    out_image.save(str(out_path))

if __name__ == '__main__':
    main()
