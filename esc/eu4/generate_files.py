#!/usr/bin/env python3
import os
import sys

# add the parent folder to the path so that imports work even if the working directory is the eu4 folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from ck2parser import csv_rows
from eu4.parser import Eu4Parser
from eu4.paths import eu4outpath


class FileGenerator:

    def __init__(self):
        self.eu4parser = Eu4Parser()
        self.parser = self.eu4parser.parser

    def format_effect(self, effect, value):
        #         if effect in ['supply_limit', 'maneuver_value']:
        #             value = value * 100
        formattings = {'infantry_fire': '{{{{icon|inf fire}}}} {{{{green|+{:0.2f}}}}} Infantry fire',
                       'infantry_shock': '{{{{icon|inf shock}}}} {{{{green|+{:0.2f}}}}} Infantry shock',
                       'cavalry_shock': '{{{{icon|cav shock}}}} {{{{green|+{:0.2f}}}}} Cavalry shock',
                       'land_morale': '{{{{icon|land morale}}}} {{{{green|+{:0.2f}}}}} Morale of armies',
                       'combat_width': '{{{{icon|width}}}} {{{{green|+{}}}}} Combat width',
                       'military_tactics': '{{{{icon|tactics}}}} {{{{green|+{:0.2f}}}}} Military tactics',
                       'supply_limit': '{{{{icon|supply}}}} {{{{green|+{:.0%}}}}} Supply limit',
                       'artillery_fire': '{{{{icon|art fire}}}} {{{{green|+{:0.2f}}}}} Artillery fire',
                       'artillery_shock': '{{{{icon|art shock}}}} {{{{green|+{:0.2f}}}}} Artillery shock',
                       'maneuver_value': '{{{{icon|flanking range}}}} {{{{green|+{:.0%}}}}} Improved flanking range',
                       'cavalry_fire': '{{{{icon|cav fire}}}} {{{{green|+{:0.2f}}}}} Cavalry fire',
                       }
        return formattings[effect].format(value)

    def add_unit_to_list(self, unitlist, unit):
        tech_group = ''
        for n, v in self.parser.parse_file('common/units/{}.txt'.format(unit)):
            if n.val == 'unit_type':
                if v.val in ['sub_saharan']:
                    tech_group = 'Sub-Saharan'
                elif v.val == 'nomad_group':
                    tech_group = 'Nomad'
                else:
                    tech_group = self.eu4parser.localize(v.val)
            elif n.val == 'type':
                unit_type = v.val
            else:
                continue
        if unit_type not in unitlist:
            unitlist[unit_type] = []
        unitlist[unit_type].append((tech_group, self.eu4parser.localize(unit)))

    def transform_techs_to_dict(self, techtype):
        techs = []
        for n, v in self.parser.parse_file('common/technologies/{}.txt'.format(techtype)):
            tech = {}
            if n.val == 'technology':
                for n2, v2 in v:
                    if n2.val == 'enable':
                        if 'enable' not in tech:
                            tech['enable'] = []
                        tech['enable'].append(v2.val)
                    elif n2.val == 'expects_institution':
                        tech['expects_institution'] = {}
                        for n3, v3 in v2:
                            tech['expects_institution'][n3.val] = v3.val
                    else:
                        tech[n2.val] = v2.val

                techs.append(tech)
        return techs

    def mil_table(self):

        lines = ['{| class="mildtable" style="width:100%"',
                 '! style="text-align:center; width:5%" | Level',
                 '! style="text-align:center; width:15%" | Technology',
                 '! style="text-align:center; width:20%" | Effects',
                 '! style="text-align:center; width:20%" | Unlocked units',
                 '! style="text-align:center; width:5%" | Year',
                 '! style="text-align:center;" | Description']

        current_fort_level = 0
        for techlevel, tech in enumerate(self.transform_techs_to_dict('mil')):
            lines.append('|-')
            lines.append('! style="text-align: center;" | {}'.format(techlevel))
            lines.append("| ''{}'' ".format(self.eu4parser.localize('mil_tech_cs_{}_name'.format(techlevel))))
            lines.append('| ')
            year = 0
            effectlines = []
            for n, v in tech.items():
                line = None
                if n == 'sprite_level':
                    continue
                elif n == 'year':
                    year = v
                elif n.startswith('fort'):
                    current_fort_level += 1
                    # make sure buildings are first
                    lines.append('* {{{{icon|western_fort0{}|28px}}}} Can now build {}'.format(
                        current_fort_level,
                        self.eu4parser.localize('building_' + n).lower()
                    ))
                elif n in ['barracks', 'regimental_camp', 'training_fields', 'conscription_center']:
                    # make sure buildings are first
                    lines.append('* {{{{icon|western_{}|28px}}}} Can now build {}'.format(n, self.eu4parser.localize(
                        'building_' + n).lower()))
                elif n == 'weapons':
                    # make sure buildings are first
                    lines.append('* {{{{icon|weapons_manufactory|28px}}}} Can now build weapons manufactories')
                elif n == 'enable':
                    continue  # handled later
                else:
                    try:
                        line = self.format_effect(n, v)
                    except:
                        print('No format specified for "' + n + '"')
                if line:
                    effectlines.append('* ' + line)
            lines.extend(effectlines)
            lines.append('|')
            if 'enable' in tech:
                unitlist = {}
                for unit_name in tech['enable']:
                    self.add_unit_to_list(unitlist, unit_name)
                for unit_type in ['infantry', 'cavalry',
                                  'artillery']:  # make sure they are always displayed in the right order
                    if unit_type in unitlist:
                        units = unitlist[unit_type]
                        unit_type_short = unit_type[:3]
                        lines.append('{{unit list')
                        lines.append('| type = {}'.format(unit_type.title()))
                        lines.append('| body =')
                        tech_group_order = ['Western', 'Eastern', 'Anatolian', 'Muslim', 'Indian', 'Chinese', 'Nomad',
                                            'Sub-Saharan', 'North American', 'Mesoamerican', 'South American',
                                            'High American', 'Aboriginal', 'Polynesian', '']
                        units.sort(key=lambda x: '{:3}'.format(tech_group_order.index(x[0])) + x[1])
                        for tech_group, name in units:
                            if tech_group:
                                lines.append('* {{{{{}|{}|{}}}}}'.format(unit_type_short, tech_group, name))
                            else:  # artillery
                                lines.append('* {}'.format(name))
                        lines.append('}}')
            lines.append('| style="text-align: center;" | {}'.format(year))
            lines.append('| style="text-align: justify;" | \'\'{}\'\''.format(
                self.eu4parser.localize('mil_tech_cs_{}_desc'.format(techlevel))))
        lines.append('|}')
        self.write_file('mil_tech', '\n'.join(lines))

    def mil_techs_effects_table(self):
        lines = []
        lines.append('{| class="mildtable" style="text-align:center"')
        lines.append('! Level')
        lines.append('! [[File:Infantry_fire.png|link=Fire|28px]]<br>Infantry<br>fire')
        lines.append('! [[File:Cavalry_fire.png|link=Fire|28px]]<br>Cavalry<br>fire')
        lines.append('! [[File:Artillery_fire.png|link=Fire|28px]]<br>Artillery<br>fire')
        lines.append('! [[File:Infantry_shock.png|link=Shock|28px]]<br>Infantry<br>shock')
        lines.append('! [[File:Cavalry_shock.png|link=Shock|28px]]<br>Cavalry<br>shock')
        lines.append('! [[File:Artillery_shock.png|link=Shock|28px]]<br>Artillery<br>shock')
        lines.append('! [[File:Land morale.png|link=Morale of Armies|28px]]<br>Morale<br>of armies')
        lines.append('! [[File:Military tactics.png|link=Military tactics|28px]]<br>Military<br>tactics')
        lines.append('! [[File:Icon maneuver.png|link=Improved flanking range|28px]]<br>Improved<br>flanking range')
        lines.append('! [[File:Combat width.png|link=Combat width|28px]]<br>Combat<br>width')
        lines.append('! [[File:Supply limit.png|link=Supply limit|28px]]<br>Supply<br>limit')
        columns = {'infantry_fire': '+{:0.2f}', 'cavalry_fire': '+{:0.1f}', 'artillery_fire': '+{:0.1f}',
                   'infantry_shock': '+{:0.2f}', 'cavalry_shock': '+{:0.1f}', 'artillery_shock': '+{:0.2f}',
                   'land_morale': '+{:0.1f}', 'military_tactics': '+{:0.2f}', 'maneuver_value': '+{:.0%}',
                   'combat_width': '+{}', 'supply_limit': '+{:.0%}'}
        cumulative_values = {column: 0 for column in columns}
        # this is the base value as displayed in the game. I have no idea where in the files that is defined
        cumulative_values['military_tactics'] = 0.5
        cumulative_values['combat_width'] = 15  # from BASE_COMBAT_WIDTH in defines.lua
        for techlevel, tech in enumerate(self.transform_techs_to_dict('mil')):
            lines.append('|-')
            lines.append('! {}'.format(techlevel))
            for column_name, lineformat in columns.items():
                current_lineformat = lineformat
                if column_name in tech:
                    cumulative_values[column_name] += tech[column_name]
                    if techlevel > 0:
                        current_lineformat = '{{{{green|' + lineformat + '}}}}'
                lines.append('| ' + current_lineformat.format(cumulative_values[column_name]))
        lines.append('|}')
        self.write_file('mil_tech_effects_table', '\n'.join(lines))

    def unit_pip_table(self):
        """unfinished"""
        unitlist = {'infantry': {}, 'cavalry': {}, 'artillery': {}}
        for techlevel, tech in enumerate(self.transform_techs_to_dict('mil')):
            if 'enable' in tech:
                for unit_name in tech['enable']:
                    tech_group = 'all'  # for artillery
                    pips = 0
                    category = None
                    for n, v in self.parser.parse_file('common/units/{}.txt'.format(unit_name)):
                        if n.val == 'unit_type':
                            tech_group = v.val
                        elif n.val == 'type':
                            category = v.val
                        elif n.val in (
                                'maneuver', 'offensive_morale', 'defensive_morale', 'offensive_fire', 'defensive_fire',
                                'offensive_shock', 'defensive_shock'):
                            pips += int(v.val)
                    if category is None:
                        raise Exception('No category for {}'.format(unit_name))

                    if techlevel not in unitlist[category]:
                        unitlist[category][techlevel] = {}
                    if tech_group not in unitlist[category][techlevel]:
                        unitlist[category][techlevel][tech_group] = pips
                    elif unitlist[category][techlevel][tech_group] != pips:
                        raise Exception(
                            'Differing number of pips for {} in category {} on tech {} in group {}'.format(unit_name,
                                                                                                           category,
                                                                                                           techlevel,
                                                                                                           tech_group))
        print(unitlist)

    #         for techlevel in range(1,32):

    def straits(self):
        lines = ['{{MultiColumn|']
        default_tree = self.parser.parse_file('map/default.map')
        for row in csv_rows(self.parser.file('map/' + default_tree['adjacencies'].val)):
            if row[0] not in ['From', '-1'] and row[2] != 'canal':
                # "–" is an en-dash
                lines.append('* {} – {}'.format(self.eu4parser.localize('PROV' + row[0]),
                                                self.eu4parser.localize('PROV' + row[1])))
        lines.append('|4}}')
        self.write_file('straits', '\n'.join(lines))

    def write_file(self, name, content):
        output_file = eu4outpath / 'eu4{}.txt'.format(name)
        with output_file.open('w') as f:
            f.write(content)

    def generate_all(self):
        self.mil_table()
        self.mil_techs_effects_table()
        self.straits()
        # self.unit_pip_table()


if __name__ == '__main__':
    generator = FileGenerator()
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            getattr(generator, arg)()
    #             generator[arg]()
    else:
        generator.generate_all()
