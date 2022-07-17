#!/usr/bin/env python3
import os
import sys
import math
from locale import strxfrm, setlocale, LC_COLLATE
# add the parent folder to the path so that imports work even if the working directory is the eu4 folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from eu4.wiki import WikiTextConverter
from eu4.paths import eu4outpath
from eu4.mapparser import Eu4MapParser

# the MonumentList needs pyradox which needs to be imported in some way
# sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../../../pyradox')
# from pyradox.filetype.table import make_table, WikiDialect


class MonumentList:
    """unfinished; needs pyradox and pdxparse"""

    def __init__(self):
        self.parser = Eu4MapParser()
        self.monument_icons = None

    def get_monument_icon(self, monumentid):
        if self.monument_icons is None:
            self.monument_icons = {}
            for n, v in self.parser.parser.parse_file('interface/great_project.gfx'):
                for n2, v2 in v:
                    name = v2['name'].val.replace('GFX_great_project_', '')
                    image = v2['texturefile'].val.replace('gfx//interface//great_projects//', '').replace('.dds', '')
                    self.monument_icons[name] = image
        return self.monument_icons[monumentid]

    def parse_monuments(self):
        monuments = {}
        for monumentid, v in self.parser.parser.merge_parse('common/great_projects/*'):
            name = self.parser.localize(monumentid)
            monument_type = v['type']
            if monument_type == 'canal':
                build_cost = v['build_cost']
                prestige_gain = v['on_built']['owner']['add_prestige']
            else:
                build_cost = None
                prestige_gain = None
            provinceID = v['start']
            prov = self.parser.all_provinces[provinceID]
            can_be_moved = v['can_be_moved'].val == 'yes'
            level = v['starting_tier'].val
            if len(v['can_use_modifiers_trigger']) > 0:
                trigger = v['can_use_modifiers_trigger'].str(self.parser.parser)
            else:
                trigger = None
            if len(v['can_upgrade_trigger']) > 0:
                can_upgrade_trigger = v['can_upgrade_trigger'].str(self.parser.parser)
            else:
                can_upgrade_trigger = None
            if len(v['build_trigger']) > 0:
                build_trigger = v['build_trigger'].str(self.parser.parser)
            else:
                build_trigger = None
            if trigger != can_upgrade_trigger:
                print('Warning: can_use_modifiers_trigger is {} but can_upgrade_trigger is {}'.format(trigger, can_upgrade_trigger))
            if trigger != build_trigger:
                print('Warning: can_use_modifiers_trigger is {} but build_trigger is {}'.format(trigger, build_trigger))
            if len(v['keep_trigger']) > 0:
                print('Warning: keep_trigger is not empty')
            tier_data = []
            for tier in range(4):
                values = v['tier_{}'.format(tier)]
                upgrade_time = values['upgrade_time'].inline_str(self.parser.parser)[0]
                if tier == 0:
                    expected_upgrade_time = 0
                    expected_upgrade_cost = 0
                if tier == 1:
                    expected_upgrade_time = 120
                    expected_upgrade_cost = 1000
                if tier == 2:
                    expected_upgrade_time = 240
                    expected_upgrade_cost = 2500
                if tier == 3:
                    expected_upgrade_time = 480
                    expected_upgrade_cost = 5000
                if upgrade_time != '{{ months = {} }}'.format(expected_upgrade_time):
                    print('Warning: unexpected upgrade_time "{}" on tier {}'.format(upgrade_time, tier))
                cost_to_upgrade = values['cost_to_upgrade'].inline_str(self.parser.parser)[0]
                if cost_to_upgrade != '{{ factor = {} }}'.format(expected_upgrade_cost):
                    print('Warning: unexpected cost_to_upgrade "{}" on tier {}'.format(cost_to_upgrade, tier))

                if len(values['province_modifiers']) > 0:
                    province_modifiers = values['province_modifiers'].inline_str(self.parser.parser)[0]
                else:
                    province_modifiers = None
                if len(values['area_modifier']) > 0:
                    area_modifier = values['area_modifier'].inline_str(self.parser.parser)[0]
                else:
                    area_modifier = None
                if len(values['country_modifiers']) > 0:
                    country_modifiers = values['country_modifiers'].inline_str(self.parser.parser)[0]
                else:
                    country_modifiers = None
                if len(values['on_upgraded']) > 0:
                    on_upgraded = values['on_upgraded'].inline_str(self.parser.parser)[0]
                else:
                    on_upgraded = None
                tier_data.append({'province_modifiers': province_modifiers, 'area_modifier': area_modifier, 'country_modifiers': country_modifiers, 'on_upgraded': on_upgraded})
            monuments[monumentid] = {'name': name, 'provinceID': provinceID, 'province': prov, 'can_be_moved': can_be_moved, 'level': level, 'trigger': trigger, 'tiers': tier_data, 'build_cost': build_cost, 'type': monument_type, 'build_trigger': build_trigger, 'prestige_gain': prestige_gain, 'icon': self.get_monument_icon(monumentid)}
        return monuments

    def _get_unique_key(self, monument, what, tier=None):
        if tier:
            return '{}_{}_{}'.format(monument, tier, what)
        else:
            return '{}_{}'.format(monument, what)

    def generate(self):

        wiki_converter = WikiTextConverter()

        trigger_and_effects = {}
        modifiers = {}
        monuments = self.parse_monuments()

        for monument, data in monuments.items():
            if data['trigger']:
                trigger_and_effects[self._get_unique_key(monument, 'trigger')] = data['trigger']
            for tier in range(4):
                tier_data = data['tiers'][tier]
                for mod_type in ['province_modifiers', 'area_modifier', 'country_modifiers']:
                    if tier_data[mod_type]:
                        modifiers[self._get_unique_key(monument, mod_type, tier)] = wiki_converter.remove_surrounding_brackets(tier_data[mod_type])
                if tier_data['on_upgraded']:
                    trigger_and_effects[self._get_unique_key(monument, 'on_upgraded', tier)] = tier_data['on_upgraded']


        wiki_converter.to_wikitext(province_scope=trigger_and_effects, modifiers=modifiers)

        trigger_effects_modifiers = {**trigger_and_effects, **modifiers}

        for monument, data in monuments.items():
            if data['trigger']:
                # add linebreak because the conditions are lists
                data['Requirements'] = '\n' + wiki_converter.remove_indent(trigger_and_effects[self._get_unique_key(monument, 'trigger')])
            else:
                data['Requirements'] = ''
            for tier in range(1,4):
                effects = ''
                tier_data = data['tiers'][tier]
                for effect_type, description in {'province_modifiers': 'Province modifiers', 'area_modifier': 'Area modifiers', 'country_modifiers': 'Global modifiers', 'on_upgraded': 'When upgraded'}.items():
                    if self._get_unique_key(monument, effect_type, tier) in trigger_effects_modifiers:
                        effects += description + ':\n{{plainlist|\n' + wiki_converter.add_indent(trigger_effects_modifiers[self._get_unique_key(monument, effect_type, tier)]) + '\n}}\n'
                data['tier_' + str(tier)] = effects

        monuments = {k: v for (k,v) in monuments.items() if v['type'] == 'monument'}

        monuments = dict(sorted(monuments.items(), key=lambda x: x[1]['name']))
        for i, monument in enumerate(monuments.items(), start =1 ):
            monument[1]['number'] = i

        column_specs = [
            ('', 'id="%(name)s" | %(number)d'),
            ('Name', 'style="text-align:center; font-weight: bold; font-size:larger" | %(name)s \n\n[[File:%(icon)s.png|%(name)s]]'),
            ('Location', lambda k, v: '<small>{{plainlist|\n*%s\n*%s}}</small>\n%s' % (
                v['province'].superregion,
                v['province'].region,
                v['province'])),
            ('Level', '%(level)d'),
#            ('[[File:Great project level icon move.png|24px|Can be relocated]]', lambda k,v: 'yes' if v['can_be_moved'] else 'no')
            ('[[File:Great project level icon move.png|24px|Can be relocated]]', lambda k,v: '{{icon|%s}}' % ('yes' if v['can_be_moved'] else 'no')),
            ('Requirements', '%(Requirements)s'),
            ('[[File:Great project level icon tier 1.png|24px]] Noteworthy level', '%(tier_1)s'),
            ('[[File:Great project level icon tier 2.png|24px]] Significant level', '%(tier_2)s'),
            ('[[File:Great project level icon tier 3.png|24px]] Magnificent level', '%(tier_3)s'),
            ]

        dialect = WikiDialect
        dialect.row_cell_begin = lambda s: ''
        dialect.row_cell_delimiter = '\n| '

        table = make_table(monuments, 'wiki', column_specs,
                           table_style = '')
        #print(table)
        self._writeFile('monuments', table)

    def _writeFile(self, name, content):
        output_file = eu4outpath / 'eu4{}.txt'.format(name)
        with output_file.open('w') as f:
            f.write(content)

class AreaAndRegionsList:

    def __init__(self):
        self.parser = Eu4MapParser()

    def formatSuperRegions(self):
        lines = ['{{MultiColumn|']
        for superregion in self.parser.all_superregions.values():
            if not superregion.contains_land_provinces:
                continue
            lines.append('; {} subcontinent'.format(superregion.display_name))
            for region in superregion.regions:
                lines.append('* {}'.format(region.display_name))
            lines.append('') # blank lines to separate the superregions
        lines.pop() # remove last blank line
        lines.append('|4}}')
        return '\n'.join(lines)

    def formatSeaRegions(self):
        regionsWithInlandSeas = [region for region in self.parser.all_regions.values() if region.contains_inland_seas]
        regionsWithOnlyHighSeas = [region for region in self.parser.all_regions.values() if not region.contains_inland_seas and not region.contains_land_provinces]

        lines = ['{{MultiColumn|']
        lines.append('; With some inland sea zones {{icon|galley}}')
        for region in regionsWithInlandSeas:
            lines.append('* {}'.format(region.display_name))
        lines.append('') # blank lines to separate the superregions

        lines.append('; Without any inland sea zones')
        for region in regionsWithOnlyHighSeas:
            lines.append('* {}'.format(region.display_name))
        lines.append('|4}}')
        return '\n'.join(lines)

    def formatLandAreas(self):
        lines = ['{{MultiColumn|']
        regionsWithRegionInLink = [country.display_name for country in self.parser.all_countries.values()]
        regionsWithRegionInLink.append('Britain')

        for region in sorted(self.parser.all_regions.values(), key=lambda r: strxfrm(r.display_name)):
            if not region.contains_land_provinces:
                continue
            if region.display_name in regionsWithRegionInLink:
                link = '{0} (region)|{0}'.format(region.display_name)
            else:
                link = region.display_name
            lines.append('; [[{}]]'.format(link))
            for area in region.areas:
                lines.append('* {}'.format(area.display_name))
            lines.append('') # blank lines to separate the regions
        lines.pop() # remove last blank line
        lines.append('|5}}')
        return '\n'.join(lines)

    def formatSeaAreas(self):
        lines = ['{{MultiColumn|']

        for region in sorted(self.parser.all_regions.values(), key=lambda r: strxfrm(r.display_name)):
            if region.contains_land_provinces:
                continue
            lines.append('; {}'.format(region.display_name))
            for area in region.areas:
                lines.append('* {}'.format(area.display_name))
            lines.append('') # blank lines to separate the regions
        lines.pop() # remove last blank line
        lines.append('|5}}')
        return '\n'.join(lines)

    def formatSuperregionsColorTable(self):
        lines = ['{| class="wikitable" style="float:right; clear:right; width:300px; text-align:center; "',
                 '|+ Subcontinents',
                 '|']
        sregions_per_column = math.ceil(len([s for s in self.parser.all_superregions.values() if s.contains_land_provinces]) / 3)
        columns = []
        currentColumn = []
        for i, sregion in enumerate(self.parser.all_superregions.values()):
            if not sregion.contains_land_provinces:
                continue
            color = self.parser.color_list[i]
            currentColumn.append('| style="background-color:{}"|{}'.format(color.get_css_color_string(), sregion.display_name))
            if len(currentColumn) == sregions_per_column:
                columns.append('{| style="width:100px;"\n' + '\n|-\n'.join(currentColumn) + '\n|}')
                currentColumn = []
        columns.append('{| style="width:100px;"\n' + '\n|-\n'.join(currentColumn) + '\n|}')
        lines.append('\n|\n'.join(  columns  ) )
        lines.append('|}')
        return '\n'.join(lines)


    def formatEstuaryList(self):
        lines = ['{{SVersion|' + self.parser.eu4_major_version + '}}',
                 '{{desc|Estuary|' + self.parser.localize('desc_river_estuary_modifier') + '}}',
                 'River estuaries give {{icon|local trade power}} {{green|+10}} local trade power.<ref name="emod">See in {{path|common/event_modifiers/00_event_modifiers.txt}}</ref> ',
                 '{{MultiColumn|'
                 ]
        estuary_lines = []
        for estuary, provinces in self.parser.estuary_map.items():
            if len(provinces) > 1:
                ref = '<ref name=split>The estuary is shared between two provinces in which case both receive {{icon|local trade power|24px}} {{green|+5}} local trade power.</ref> '
            else:
                ref = ''
            estuary_lines.append('* {} ({}){}'.format(
                    ' and '.join([p.name for p in provinces]),
                    self.parser.localize(estuary)
                    ,ref

                ))
        lines.extend(sorted(estuary_lines))
        lines.append('|4}}')

        return '\n'.join(lines)

    def writeSuperRegionsList(self):
        self.writeFile('superregions', self.formatSuperregionsColorTable() + '\n\nAll of the land regions are grouped together to form the following in-game subcontinents:\n' + self.formatSuperRegions())

    def writeSeaRegionsList(self):
        self.writeFile('searegions', self.formatSeaRegions())

    def writeLandAreaList(self):
        self.writeFile('landareas', self.formatLandAreas())

    def writeSeaAreaList(self):
        self.writeFile('seaareas', self.formatSeaAreas())

    def writeEstuaryList(self):
        self.writeFile('estuaries', self.formatEstuaryList())

    def writeFile(self, name, content):
        output_file = eu4outpath / 'eu4{}.txt'.format(name)
        with output_file.open('w') as f:
            f.write(content)

if __name__ == '__main__':
    # for correct sorting. en_US seems to work even for non english characters, but the default None sorts all non-ascii characters to the end
    setlocale(LC_COLLATE, 'en_US.utf8')

    # MonumentList().generate()
    # exit()

    list_generator = AreaAndRegionsList()
    list_generator.writeSuperRegionsList()
    list_generator.writeSeaRegionsList()
    list_generator.writeLandAreaList()
    list_generator.writeSeaAreaList()
    list_generator.writeEstuaryList()

