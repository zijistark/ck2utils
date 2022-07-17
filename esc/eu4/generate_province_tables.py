#!/usr/bin/env python3
import os
import sys
# add the parent folder to the path so that imports work even if the working directory is the eu4 folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from collections import defaultdict
from locale import strxfrm, setlocale, LC_COLLATE
from eu4.mapparser import Eu4MapParser
from eu4.paths import eu4outpath


class ProvinceTables(object):

    def __init__(self):
        self.parser = Eu4MapParser()

    def main(self):
        # for correct sorting. en_US seems to work even for non english characters, but the default None sorts all non-ascii characters to the end
        setlocale(LC_COLLATE, 'en_US.utf8')
        provinces = self.parser.all_provinces
        continents = self.analyze_continents(provinces)
        notes, provinces_to_include_in_continent = self.find_oddities(provinces)

        tables = [
            (('ID,Name,Development,BT,BP,BM,'
              'Trade good,Trade node,Modifiers').split(','),
             'eu4economic.txt'),
            ('ID,Name,Type,Continent,Superregion,Region,Area'.split(','),
             'eu4geographical.txt'),
            ('ID,Name,Owner (1444),Religion,Culture,Culture Group'.split(','),
             'eu4political.txt'),
        ]

        for headings, filename in tables:
            output = self.format_output(provinces, headings)
            output_file = eu4outpath / filename
            with output_file.open('w') as f:
                f.write(output)

        output = self.format_continent_output(continents,
            ('Provinces,Base Tax,Base Production,Base Manpower,'
             'Development').split(','))
        output_file = eu4outpath / 'eu4continenttable.txt'
        with output_file.open('w') as f:
            f.write(output)
        map_filenames = {'Africa': 'superregion_africa.png', 'Asia': 'Asian regions.png', 'East Indies': 'Superregion east indies.png',  'Europe': 'European regions.png', 'India': 'Superregion india.png', 'Oceania': 'Oceanian regions.png', 'North America': 'North American regions.png', 'South America': 'Superregion_south_america.png'}
        for continent in continents:
            if continent == 'Total':
                continue
            provinces_to_include = [p for p, c in provinces_to_include_in_continent.items() if c == continent]
            provinces_to_exclude = [p for p, c in provinces_to_include_in_continent.items() if c != continent]
            if continent == 'Asia':
                provincesOnContinent = [x for x in provinces.values() if x.get('Superregion') == 'India' and x.get('Continent') == continent and x.get('Type').endswith('Land') and (x.get('ID') not in provinces_to_exclude)]
                self.write_region_list(provincesOnContinent, continent, notes, map_filenames['India'], 'India')
                provincesOnContinent = [x for x in provinces.values() if x.get('Superregion') == 'East Indies' and x.get('Continent') == continent and x.get('Type').endswith('Land') and (x.get('ID') not in provinces_to_exclude)]
                self.write_region_list(provincesOnContinent, continent, notes, map_filenames['East Indies'], 'East Indies')
                excluded_superregions = ['India', 'East Indies']
            else:
                excluded_superregions = []
            provincesOnContinent = [x for x in provinces.values() if x.get('ID') in provinces_to_include or (x.get('Continent') == continent and x.get('Type').endswith('Land') and (x.get('Superregion') not in excluded_superregions) and (x.get('ID') not in provinces_to_exclude))]
            self.write_region_list(provincesOnContinent, continent, notes, map_filenames[continent])

    def find_oddities(self, provinces):
        '''look for areas and provinces that are on different continents than the rest of their region/area'''
        print('Some areas and regions spawn multiple continents. Notes for this have been added to the regions tables, but they need manual review')
        areas_to_continents = {}
        regions_to_continents = {}
        provinces_to_include_in_continent = {}
        areas_on_multiple_continents = {}
        for prov in provinces.values():
            if not prov.get('Type').endswith('Land'):
                continue
            if not prov.area.name in areas_to_continents:
                areas_to_continents[prov.area.name] = {}
            if not prov['Continent'] in areas_to_continents[prov.area.name]:
                areas_to_continents[prov.area.name][prov['Continent']] = []
            areas_to_continents[prov.area.name][prov['Continent']].append(prov)

        notes = {}
        for area, continents in areas_to_continents.items():
            if len(continents) > 1:
                if len(continents) > 2:
                    print('Areas in more than 2 continents are not handled. You may be missing some notes. The affected area is ' + area)

                sorted_continents = sorted([{'continent': k, 'provinces': v} for k, v in continents.items()], key=lambda c: len(c['provinces']), reverse=True)

                areas_on_multiple_continents[area] = sorted_continents[0]['continent']
                for p in sorted_continents[1]['provinces']:
                    provinces_to_include_in_continent[p['ID']] = sorted_continents[0]['continent']

                # this code also handles the case that there is more than one province in the continent with the fewer provinces
                # as this doesn't exist yet, I didn't add correct grammar for that case
                notes[area] = "'''Note:''' The province of {} belongs to [[{}]].".format(', '.join( '{} ({})'.format(p['Name'], p['ID']) for p in sorted_continents[1]['provinces']), sorted_continents[1]['continent'])

                print('Area {} is in continents {}. But mostly in {}'.format(area, ', '.join(map(str, continents.keys())), sorted_continents[0]['continent']))
        for prov in provinces.values():
            if not prov.get('Type').endswith('Land'):
                continue
            if prov.area.name in areas_on_multiple_continents and areas_on_multiple_continents[prov.area.name] != prov['Continent']:
                continue
            if not prov['Region'] in regions_to_continents:
                regions_to_continents[prov['Region']] = {}
            if not prov['Continent'] in regions_to_continents[prov['Region']]:
                regions_to_continents[prov['Region']][prov['Continent']] = set()

            regions_to_continents[prov['Region']][prov['Continent']].add(prov.area.name)

        for region, continents in regions_to_continents.items():
            if len(continents) > 1:
                if len(continents) > 2:
                    print('Regions in more than 2 continents are not handled. You may be missing some notes. The affected region is ' + region)
                sorted_continents = sorted([{'continent': k, 'areas': v} for k, v in continents.items()], key=lambda c: len(c['areas']), reverse=True)
                print('Region {} is in continents {}. But mostly in {}'.format(region, ', '.join(map(str, continents.keys())), sorted_continents[0]['continent']))
                notes[region] = {}
                notes[region][sorted_continents[0]['continent'].display_name] = "'''Note:''' The area of {} belongs to {}.".format(', '.join(sorted('[[{}]]'.format(self.parser.localize(a)) for a in sorted_continents[1]['areas'])), sorted_continents[1]['continent'])
                notes[region][sorted_continents[1]['continent'].display_name] = "'''Note:''' The region [[{}]] belongs mainly to {}.".format(region, sorted_continents[0]['continent'])
        return notes, provinces_to_include_in_continent

    def analyze_continents(self, provinces):
        continents = {}
        for prov in provinces.values():
    #         if prov.get('Type').endswith('Land'):
            if prov.type == 'Land':
                continent_name = prov['Continent'].display_name
                if continent_name not in continents:
                    continents[continent_name] = defaultdict(int)
                cont = continents[continent_name]
                cont['Provinces'] += 1
                cont['Base Tax'] += int(prov['BT']) if prov['BT'] else 0
                cont['Base Production'] += int(prov['BP']) if prov['BP'] else 0
                cont['Base Manpower'] += int(prov['BM']) if prov['BM'] else 0
                cont['Development'] += (int(prov['Development'])
                    if prov['Development'] else 0)
        total = defaultdict(int)
        for cont in continents.values():
            for key, val in cont.items():
                total[key] += val
        continents['Total'] = total
        return continents

    def add_estuary_icon(self, localized_modifier_name):
        if 'Estuary' in localized_modifier_name:
            return '[[File:Estuary.png|32px|link=Estuary]]' + localized_modifier_name
        else:
            return localized_modifier_name

    def formatModifiers(self, province):
        modifiers = list(province.get('Modifiers', []))  # use a new list so that we can add CoT locally
        if province.center_of_trade > 0:
            modifiers.append('[[File:Cot level {}.png|32px|link=Center of Trade]]{}'.format(province.center_of_trade, province.format_center_of_trade_string()))
        return '<br/>'.join(sorted(self.add_estuary_icon(self.parser.localize(x)) for x in modifiers))

    def formatForProvinceTable(self, attribute, province):
        if attribute == 'Type':
            return self.formatType(province.type)
        if attribute == 'Modifiers':
            return self.formatModifiers(province)
        formatstrings = {
            'Trade good': '[[File:{0}.png|24px|alt={0}|link={0}]]',
            'Religion': '[[File:{0}.png|24px|alt={0}|link={0}]]',
            'Owner': '[[File:{0}.png|24px|border|alt={0}|link={0}]] [[{0}]]'}
        if attribute == 'Owner' and 'tribal_owner' in province.attributes:
            if 'Owner' in province.attributes:
                raise Exception('province {} has an owner and a tribal_owner'.format(province.id))
            return "''Tribal land of'' " + formatstrings[attribute].format(self.parser.localize(province.get('tribal_owner', '')))
        value = self.parser.localize(province.get(attribute, ''))
        if value == '':
            return value

        # special case, because HAW and UHW are both called "Hawai'i"
        if attribute == 'Owner' and province.get('Owner') == 'HAW':
            return "[[File:HAW.png|24px|border|alt=Hawai'i|link=Oceanian_super-region#Hawai.27i]] [[Oceanian_super-region#Hawai.27i|Hawai'i]]"
        if attribute in formatstrings:
            return formatstrings[attribute].format(value)
        else:
            return value

    def formatType(self, province_type):
        colors = {'Land': '#AAFFAA', 'Wasteland': '#E5E5E5', 'Inland sea': '#CCDDFF', 'Sea': '#CCDDFF', 'Open sea': '#CCDDFF', 'Lake': '#CCDDFF'}
        return 'bgcolor=' + colors[province_type] + '|' + province_type

    def format_output(self, provinces, headings):
        lines = ['{| class="wikitable sortable" '
                  'style="font-size:95%; text-align:left"']
        lines.extend('! {}'.format(head) for head in headings)
        for prov in provinces.values():
            lines.append('|-')
            for head in headings:
    #             value = prov.get(head, '')
    #             if head == 'Type':
                if head == 'Owner (1444)':
                    head = 'Owner'
                value = self.formatForProvinceTable(head, prov)
                lines.append(('|{}' if head == 'Type' else '| {}').format(value))
        lines.append('|}')
        lines.append('')
        return '\n'.join(lines)

    def format_continent_output(self, continents, headings):
        icon_names = {
            'Provinces': 'Province',
            'Base Production': 'Production',
            'Base Manpower': 'Manpower'
        }
        lines = ['{| class = "mildtable sortable" style ="text-align:right"']
        header = '! Continent !! ' + ' !! '.join('{{{{icon|{}}}}} {}'.format(
            icon_names.get(head, head), head)
            for head in headings)
        lines.append(header)
        for cont_name, cont in sorted(continents.items()):
            lines.append('|-')
            line = '|' if cont_name != 'Total' else '!'
            line += ' style="text-align:left" | {}'.format(cont_name)
            if cont_name != 'Total':
                line += ''.join(' || {}'
                                .format(cont.get(head, '')) for head in headings)
            else:
                line += ''.join(' || style="text-align:right" | {}'
                                .format(cont.get(head, '')) for head in headings)
            lines.append(line)
        lines.append('|}')
        lines.append('')
        return '\n'.join(lines)
    def format_regions_output(self, provinces, continent, notes, map_filename):
        sortedProvinces = sorted(sorted(provinces, key=lambda p: strxfrm(p.area.display_name)), key=lambda p: strxfrm(p.region.display_name))
        region_list = {p.get('Region').display_name for p in sortedProvinces}
        toc_lines = ['{| class="toccolours"',
    '! colspan="4" | Contents',
    '|-',
    '| style="text-align: center;" | \'\'\'Map\'\'\'',
    '| colspan="2" style="text-align: right;" | \'\'\'Regions\'\'\'',
    '| style="padding-left:0.5em" | \'\'\'Areas\'\'\'',
    '|-',
    '| rowspan="{}" | [[File:{}|360px]]'.format(len(region_list), map_filename)]

        lines = []
        currentArea = ''
        currentRegion = ''
        areas_in_current_region = []
        for province in sortedProvinces:
    #     for province in provinces.values():
    #         print(province.get('Area', 'none'))
    #         print(province.get('Region', 'rnone'))
    #         print(province.get('Continent', 'cnone'))
            if province.area.name != currentArea:
                if currentArea != '':
                    lines.append('}}')
                if province.region != currentRegion:
                    currentRegion = province.region
                    if areas_in_current_region:
                        toc_lines.append(self.create_toc_area_line(region_list, areas_in_current_region))
                        toc_lines.append('|-')
                        areas_in_current_region = []

                    toc_lines.append('| style="width:2.2em; background-color:{};" |'.format(currentRegion.color.get_css_color_string()))
                    toc_lines.append('| style="text-align: right;" | [[#{}|{}]]'.format(currentRegion.display_name, currentRegion.display_name.replace(' ', '&nbsp;')))

                    lines.append('== {} =='.format(currentRegion))

                    if currentRegion in notes and continent in notes[currentRegion]:
                        lines.append(notes[currentRegion][continent])
                currentArea = province.area.name
                areas_in_current_region.append(province.get('Area', ''))
                lines.append('=== {} <!-- {} -->==='.format(province.get('Area', ''), currentArea))
                if currentArea in notes:
                    lines.append(notes[currentArea])
                lines.append('{{Regions table')
                lines.append('|rows=')
            lines.append('{{{{RTR|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}}}}}'.format(province['ID'], province.get('Name'), self.parser.localize(province.get('Owner', 'Natives')), province.get('BT'), province.get('BP'), province.get('BM'), self.parser.localize(province.get('Religion')), self.parser.localize(province.get('Culture', '')), self.parser.localize(province.get('Trade good')), province.tradenode.display_name, self.formatModifiers(province)))
        lines.append('}}')
        #toc_lines.append('| style="padding-left:0.5em" | {{{{TOCcell|{}|end}}}}'.format('}} {{TOCcell|'.join(areas_in_current_region)))
        toc_lines.append(self.create_toc_area_line(region_list, areas_in_current_region))
        toc_lines.append('|}')
        return '\n'.join(toc_lines + lines)

    def write_region_list(self, provinces, continent, notes, map_filename, continent_for_filename=None):
        if not continent_for_filename:
            continent_for_filename = continent
        output = self.format_regions_output(provinces, continent, notes, map_filename)
        output_file = eu4outpath / 'eu4regiontable_{}.txt'.format(continent_for_filename)
        with output_file.open('w') as f:
            f.write(output)

    def create_toc_area_line(self, region_list, areas_in_current_region):
        toc_line_area = '| style="padding-left:0.5em" | {{{{TOCcell|{}|end}}}}'.format('}} {{TOCcell|'.join([area.display_name for area in areas_in_current_region]))
        for area in areas_in_current_region:
            areaname = area.display_name
            if areaname in region_list: # have to link to areaname_2 if there is a region with the same name as an area
                print('Area {} is also a region'.format(areaname))
                toc_line_area = toc_line_area.replace('{{{{TOCcell|{}}}}}'.format(areaname), '<span style="white-space:nowrap;">[[#{0}_2|{0}]] •</span>'.format(areaname))

        return toc_line_area


if __name__ == '__main__':
    ProvinceTables().main()
