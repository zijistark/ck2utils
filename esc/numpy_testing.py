#!/usr/bin/env python3

import numpy as np
from PIL import Image
from ck2parser import rootpath, csv_rows, SimpleParser
from localpaths import eu4dir

parser = SimpleParser()
parser.basedir = eu4dir
default_tree = parser.parse_file('map/default.map')
max_provinces = default_tree['max_provinces'].val
provinces_rgb_map = {}
province_rgb_a = np.empty(max_provinces, 'u1,u1,u1')
provinces_path = str(parser.file('map/' + default_tree['provinces'].val))
for row in csv_rows(parser.file('map/' + default_tree['definitions'].val)):
    try:
        number = int(row[0])
    except ValueError:
        continue
    if number < max_provinces:
        rgb = tuple(row[1:4])
        provinces_rgb_map[tuple(np.uint8(rgb))] = np.uint16(number)
        province_rgb_a[number] = rgb

#############

def run(): # 4.62
    im = Image.open(provinces_path)
    a = np.array(im)[:512, :512]
    a = np.apply_along_axis(lambda x: provinces_rgb_map[tuple(x)], 2, a)

def run2(): # 4.19
    im = Image.open(provinces_path)
    a = np.array(im).view('u1,u1,u1')[:512, :512, 0]
    a = np.vectorize(lambda x: provinces_rgb_map[tuple(x)])(a)

def run3(): # 4.15
    im = Image.open(provinces_path)
    a = np.array(im).view('u1,u1,u1')[:512, :512, 0]
    a = np.vectorize(lambda x: provinces_rgb_map[tuple(x)],
                     otypes=[np.uint16])(a)

def run4(): # ~33.5
    im = Image.open(provinces_path)
    a = np.array(im).view('u1,u1,u1')[:512, :512, 0]
    b = np.full_like(a, max_provinces, np.uint16)
    for i, rgb in enumerate(province_rgb_a):
        b[np.nonzero(a == rgb)] = i

#############

def run5(): # ~30.5
    im = Image.open(provinces_path)
    pa = np.array(im).view('u1,u1,u1')[:512, :512, 0]
    for i, rgb in enumerate(province_rgb_a):
        prov_indices = np.nonzero(pa == rgb)

def run6(): # ~15.1
    im = Image.open(provinces_path)
    pa = np.array(im).view('u1,u1,u1')[:512, :512, 0]
    pa = np.vectorize(lambda x: provinces_rgb_map[tuple(x)],
                      otypes=[np.uint16])(pa)
    for number in range(1, max_provinces):
        prov_indices = np.nonzero(pa == number)
