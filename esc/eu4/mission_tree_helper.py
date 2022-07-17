import pathlib
from PIL import Image, ImageChops
from argparse import ArgumentParser
import os
import sys
# add the parent folder to the path so that imports work even if the working directory is the eu4 folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import ck2parser
from localpaths import eu4dir

class MissionTreeHelper():

    box_left = 10
    box_upper = 262
    box_width = 519
    box_height = 730

    comparison_height = 150
    y_skip_on_other_images = 40

    # background image
    box_left_bg = 17
    box_upper_bg = 132


    def main(self):
        parser = ArgumentParser(description='helpers to generate mission images for the wiki')
        parser.add_argument('screenshots', help='screenshots to crop', type=pathlib.Path, nargs='*')
        parser.add_argument('--out', help='output image', type=pathlib.Path)
        parser.add_argument('--generate-mission-tree-completion-decisions', help='generate decisions which can be used to complete missions to make nice screenshots for the wiki', action='store_true')
        args = parser.parse_args()
        if args.screenshots:
            self.process_screenshots(args.screenshots, args.out)
        elif args.generate_mission_tree_completion_decisions:
            self.generate_mission_tree_completion_decisions()

    def count_nonblack_pil(self, img):
        """Return the number of pixels in img that are not black.
        img must be a PIL.Image object in mode RGB.

        """
        bbox = img.getbbox()
        if not bbox: return 0
        return sum(img.crop(bbox)
                   .point(lambda x: 255 if x else 0)
                   .convert("L")
                   .point(bool)
                   .getdata())

    def images_are_the_same(self, image1, image2):
        diff = ImageChops.difference(image1, image2)
        if diff.getbbox() is None: # exactly the same
            return True
        else:
            # consider similar images to be the same, because there are usually
            # some differing pixel around the mission icons
            # and they can't easily be filtered out
            # the images have about 77k pixel, if they are really different,
            # they differ by more than 20k
            different_pixel = self.count_nonblack_pil(diff)
            return different_pixel < 2000

    def load(self, screenshot_file):
        return Image.open(screenshot_file)

    def crop(self, screenshot, y_skip):
        box_upper = self.box_upper + y_skip
        return screenshot.crop((self.box_left, box_upper, self.box_left + self.box_width, self.box_upper + self.box_height))

    def append_image(self, image, image_to_append, y):
        new_image = Image.new('RGB', (
                    image.size[0],
                    y + image_to_append.size[1]
                    )
                )
        new_image.paste(image)
        new_image.paste(image_to_append, (0, y))
        return new_image

    def remove_bg(self, cropped_screenshot, y_skip):
        """ make the background black by removing certain colors from the image"""
        image_without_bg = Image.new('RGB', cropped_screenshot.size, (0,0,0))
        for x in range(0,cropped_screenshot.size[0]):# process all pixels
            for y in range(0,cropped_screenshot.size[1]):
                color = cropped_screenshot.getpixel((x,y))
                # this skips all the colors which are in the mission background image
                # of course it also removes some pixel from the mission images and banner,
                # but this doesn't really matter, because the image without background is only used
                # for comparisons
                if color[0] < 10 or color[0] > 55 or (color[2] - color[0]) > 30 or color[0] > color[1] or color[1] > color[2]:
                    image_without_bg.putpixel((x,y), color)
        return image_without_bg

    def process_screenshots(self, screenshot_files, outfile):
        # if there is only one image, we can skip the rest of the processing,
        if len(screenshot_files) == 1:
            self.crop(self.load(screenshot_files[0]), 0).save(outfile)
            return

        composite_image = None
        composite_image_without_bg = None
        for screenshot_file in screenshot_files:
            if not composite_image:
                composite_image = self.crop(self.load(screenshot_file), 0)
                composite_image_without_bg = self.remove_bg(composite_image, 0)
            else:
                cropped_screenshot = self.crop(self.load(screenshot_file), self.y_skip_on_other_images)
                cropped_screenshot_without_bg = self.remove_bg(cropped_screenshot, self.y_skip_on_other_images)
                upper_part_of_new_image = cropped_screenshot_without_bg.crop((0,0,self.box_width,self.comparison_height))

                match_found = False
                y_position_to_test = composite_image.size[1] - self.comparison_height
                while not match_found:
                    comparison_image = composite_image_without_bg.crop((0,y_position_to_test, self.box_width, y_position_to_test+self.comparison_height))
                    if self.images_are_the_same(comparison_image,  upper_part_of_new_image):
                        print('match found {}'.format(y_position_to_test) )
                        match_found = True
                    else:
                        y_position_to_test -= 1
                    if y_position_to_test == 0:
                        print('No match found for image')
                        upper_part_of_new_image.show()
                        composite_image_without_bg.show()
                        exit()
                composite_image = self.append_image(composite_image, cropped_screenshot, y_position_to_test)
                composite_image_without_bg = self.append_image(composite_image_without_bg, cropped_screenshot_without_bg, y_position_to_test)
        composite_image.save(outfile)

    def generate_mission_tree_completion_decisions(self):
        """ To create the images for mission trees on the wiki"""

        parser =  ck2parser.SimpleParser()
        parser.basedir = eu4dir

        allmissions = []
        mission_flags = []
        for file, tree in parser.parse_files('missions/*'):
            for k, v in tree:
                for k2, v2 in v:
                    mission = k2.val_str()
                    if mission not in ['has_country_shield', 'ai', 'generic', 'potential', 'slot', 'potential_on_load']:
                        allmissions.append(mission)
                    elif mission == 'potential':
                        for condition, condition_value in v2:
                            if condition.val_str() == 'has_country_flag':
                                mission_flags.append(condition_value.val)
        decision_template = """    {}_decision = {{
         potential = {{
            ai = no
        }}
        allow = {{
            always = yes
        }}
        effect = {{
            {}
        }}
    }}"""
        print("country_decisions = {")
        print(decision_template.format('complete_all_missions', "\n".join(["\t\tcomplete_mission = {}".format(mission) for mission in allmissions])))
        clear_effect = "\n".join(["clr_country_flag = {}".format(flag_to_clear) for flag_to_clear in mission_flags])
        for flag in mission_flags:
            name = "activate_{}_missions".format(flag)
            effect = "{}\nset_country_flag = {}\nswap_non_generic_missions = yes".format(clear_effect, flag)
            print(decision_template.format(name,effect))
        print("}")
if __name__ == '__main__':
    MissionTreeHelper().main()