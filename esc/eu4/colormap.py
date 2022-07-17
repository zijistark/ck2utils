#!/usr/bin/env python3

import numpy as np
from PIL import Image
from localpaths import rootpath
from colormath import color_objects
from _collections import OrderedDict
from eu4.cache import cached_property
from eu4.paths import eu4outpath
from eu4.mapparser import Eu4MapParser


class ColorMapGenerator:

    colors = {
        'land': np.uint8((127, 127, 127)),
        'sea': np.uint8((68, 107, 163)),
        'desert': np.uint8((94, 94, 94)),
        'important': np.uint8((220, 138, 57)),
        'castile': np.uint8((193,  171,  8)),
        'turquoise': np.uint8((57,  160,  101)),
        'Darkturquoise': np.uint8((0, 206, 209)),
        'orange': np.uint8((255, 127, 0)),
        'red': np.uint8((110, 0, 41)),
        'blue': np.uint8((4, 35, 125)),
        'yellow': np.uint8((255, 255, 126)),
        'green': np.uint8((0, 127, 0)),
        'lightgreen': np.uint8((0, 255, 0)),
        'purple': np.uint8((128, 0, 128)),
        'brown': np.uint8((165, 42, 42)),
        'brightred': np.uint8((255, 0, 0)),
        'cyan': np.uint8((0, 255, 255)),
        'gold': np.uint8((255, 214, 48)),
        'dc': np.uint8((255, 0, 0)),
        'do': np.uint8((127, 0, 0)),
        'ic': np.uint8((0, 255, 0)),
        'io': np.uint8((0, 127, 0)),
        'pink': np.uint8((255, 0, 230)),
        'white': np.uint8((255, 255, 255)),
    }

    def __init__(self):
        self.mapparser = Eu4MapParser()
        self.outpath = eu4outpath
        self.contains = {}

        # caching the border image
        self._borderlayer = None

        # to check that one name isn't used for multiple things. e.g. an area and region with the same internal name
        self.name_to_type = {}

        if not self.outpath.exists():
            self.outpath.mkdir(parents=True)

    def convert_color_to_np_type(self, color):
        if color in self.colors:
            return self.colors[color]
        if isinstance(color, color_objects.BaseRGBColor):
            return color.get_upscaled_value_tuple()
        if isinstance(color, int):
            if color < len(self.mapparser.color_list):
                return self.mapparser.color_list[color].get_upscaled_value_tuple()
            else:
                print('Color id {} is too big'.format(color))
                return self.colors['white']

        return color

    @cached_property
    def prov_color_lut_base(self):
        prov_color_lut_base = np.full(self.mapparser.max_provinces, self.colors['land'], '3u1')

        prov_type_to_colors = {'Wasteland': self.colors['desert'],
                               'Land': self.colors['land'],
                               'Inland sea': self.colors['sea'],
                               'Sea': self.colors['sea'],
                               'Open sea': self.colors['sea'],
                               'Lake': self.colors['sea']}

        for province in self.mapparser.all_provinces.values():
            prov_color_lut_base[province.id] = prov_type_to_colors[province.type]

        return prov_color_lut_base

    def _add_to_contains_dict(self, provinceID, grouping, grouping_type):
        if not grouping:  # ignore empty groupings, e.g. empty areas for impassable provinces
            return
        if grouping in self.name_to_type:
            if self.name_to_type[grouping] != grouping_type:
                raise Exception('{} already exists as {}, but is added as {} now'.format(
                    grouping, self.name_to_type[grouping], grouping_type))
        else:
            self.name_to_type[grouping] = grouping_type

        if grouping not in self.contains:
            self.contains[grouping] = []

        self.contains[grouping].append(provinceID)

    def get_contains_dict(self):
        if not self.contains:
            for province in self.mapparser.all_provinces.values():
                self._add_to_contains_dict(province.id, province.id, 'provinceID-int')
                self._add_to_contains_dict(province.id, str(province.id), 'provinceID-str')
                self._add_to_contains_dict(province.id, province.area.name, 'area')
                self._add_to_contains_dict(province.id, province.region.name, 'region')
                self._add_to_contains_dict(province.id, province.superregion.name, 'superregion')
                self._add_to_contains_dict(province.id, province.continent.name, 'continent')
                if province.get('Culture'):
                    self._add_to_contains_dict(province.id, province['Culture'], 'culture')

            # @TODO: move somewhere else
            for n, v in self.mapparser.parser.parse_file('common/colonial_regions/00_colonial_regions.txt'):
                if 'provinces' in v.dictionary:
                    self.contains[n.val] = {n2.val for n2 in v['provinces'] if hasattr(n2, 'val')}
        return self.contains

    def generate_mapimage_with_important_provinces(self, where, name='', crop=True, margin=10):
        if crop is True:
            crop_to_color = 'important'
        else:
            crop_to_color = None
        self.generate_mapimage_with_several_colors({'important': where}, name, crop_to_color, margin)

    def calculate_boundaries(self, province_list, margin=10):
        """ calculate the min_x, max_x, min_y, max_y of the given provinces on the map and add a margin"""
        c = np.isin(self.mapparser.positions_to_provinceID_array, province_list).nonzero()

        min_y = c[0].min() - margin
        min_x = c[1].min() - margin
        max_y = c[0].max() + margin
        max_x = c[1].max() + margin

        # make sure the max and min values are not outside the image
        min_y = max(0, min_y)
        min_x = max(0, min_x)
        max_y = min(self.mapparser.positions_to_provinceID_array.shape[0] - 1, max_y)
        max_x = min(self.mapparser.positions_to_provinceID_array.shape[1] - 1, max_x)

        return min_x, max_x, min_y, max_y

    def generate_mapimage_with_several_colors(self, color_to_provinces, name='', crop_to_color=None, margin=10):
        out_path = self.outpath / '{}.png'.format(name)
        self.generate_mapimage_object_with_several_colors(color_to_provinces, crop_to_color, margin).save(str(out_path))

    def add_province_borders(self, out):
        if not self._borderlayer:
            borders_path = rootpath / 'eu4borderlayer.png'
            self._borderlayer = Image.open(str(borders_path))
        out.paste(self._borderlayer, mask=self._borderlayer)

    def generate_mapimage_object_with_several_colors(self, color_to_provinces, crop_to_color=None, margin=10):
        prov_color_lut = np.copy(self.prov_color_lut_base)

        provinces_used_for_cropping = []
        for category in color_to_provinces:
            provinceIdList = color_to_provinces[category]
            if isinstance(provinceIdList, str):
                provinceIdList = provinceIdList.split()
            provs = {y for x in provinceIdList for y in (self.get_contains_dict().get(x, None) or (int(x),))}
            if crop_to_color == category or crop_to_color == True:  # true means to include all colored provinces
                provinces_used_for_cropping.extend(provs)
            for prov in provs:
                prov_color_lut[prov] = self.convert_color_to_np_type(category)

        out_a = prov_color_lut[self.mapparser.positions_to_provinceID_array]
        out = Image.fromarray(out_a)
        self.add_province_borders(out)

        if crop_to_color:
            min_x, max_x, min_y, max_y = self.calculate_boundaries(provinces_used_for_cropping, margin)
            # for some reason, pillow excludes the bottom row and rightmost
            # column of pixels when cropping, so we have to add 1 to include them
            out = out.crop((min_x, min_y, max_x + 1, max_y + 1))

        return out

    def create_shaded_image(self, color_to_provinces, color_to_provinces_without_shading=None, name='',
                            crop_to_color=None, margin=10):
        color_first_image = color_to_provinces.copy()
        color_second_image = OrderedDict(reversed(list(color_to_provinces.items())))
        if color_to_provinces_without_shading:
            for k, v in color_to_provinces_without_shading.items():
                color_first_image[k] = v
                color_second_image[k] = v
        first_image = self.generate_mapimage_object_with_several_colors(color_first_image, crop_to_color, margin)
        second_image = self.generate_mapimage_object_with_several_colors(color_second_image, crop_to_color, margin)
        shaded_image = Image.new(first_image.mode, first_image.size)
        for x in range(first_image.width):
            for y in range(first_image.height):
                if (x+y) % 6 < 3:
                    source_image_for_current_pixel = first_image
                else:
                    source_image_for_current_pixel = second_image

                shaded_image.putpixel((x, y), source_image_for_current_pixel.getpixel((x, y)))

        out_path = self.outpath / '{}.png'.format(name)
        shaded_image.save(str(out_path))
