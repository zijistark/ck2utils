#!/usr/bin/env python3

from copy import deepcopy
import csv
from itertools import product
from ck2parser import rootpath, SimpleParser, FullParser, Pair, Obj, Number, Op
from print_time import print_time

template = '''
standard_skirmish_generic_neutral_tier.1_tactic = {
    days = 5
    sprite = 3
    group = tier_1_tech
    trigger = {
        phase = skirmish
        flank_has_leader = yes
        days = 11
        location = { terrain = farmlands }
        leader = {
            OR = {
                AND = {
                    is_landed = yes
                    capital_scope = {
                        TECH_RECRUITMENT = 0.5
                        NOT = { TECH_RECRUITMENT = 1.0 }
                    }
                }
                AND = {
                    is_landed = no
                    employer = {
                        capital_scope = {
                            TECH_RECRUITMENT = 0.5
                            NOT = { TECH_RECRUITMENT = 1.0 }
                        }
                    }
                }
            }
        }
    }
    mean_time_to_happen = {
        days = 1
        modifier = { factor = 1.1 }
        modifier = {
            factor = 1.1
            leader = { martial = 1 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 2 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 3 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 4 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 5 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 6 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 7 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 8 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 9 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 10 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 11 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 12 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 13 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 14 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 15 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 16 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 17 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 18 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 19 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 20 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 21 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 22 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 23 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 24 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 25 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 26 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 27 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 28 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 29 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 30 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 31 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 32 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 33 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 34 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 35 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 36 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 37 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 38 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 39 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 40 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 41 }
        }
        modifier = {
            factor = 1.1
            leader = { martial = 42 }
        }
    }
    light_infantry_offensive = 1
    heavy_infantry_offensive = 1
    pikemen_offensive = 1
    light_cavalry_offensive = 1
    camel_cavalry_offensive = 1
    knights_offensive = 1
    archers_offensive = 1
    horse_archers_offensive = 1
    war_elephants_offensive = 1
    light_infantry_defensive = 1
    heavy_infantry_defensive = 1
    pikemen_defensive = 1
    light_cavalry_defensive = 1
    camel_cavalry_defensive = 1
    knights_defensive = 1
    archers_defensive = 1
    horse_archers_defensive = 1
    war_elephants_defensive = 1
}
'''

terrains = [
    [],
    ['arctic'],
    ['forest', 'woods'],
    ['hills'],
    ['mountain'],
    ['steppe'],
    ['plains'],
    ['jungle'],
    ['marsh'],
    ['desert', 'coastal_desert']
]

terrain_mods = {
    'arctic': [
        (+0.5, ['light_infantry_offensive', 'light_infantry_defensive']),
        (+0.5, ['archers_offensive', 'archers_defensive']),
        (-0.25, ['pikemen_offensive']),
        (-0.25, ['camel_cavalry_offensive']),
        (-0.25, ['knights_offensive']),
        (-0.25, ['war_elephants_offensive']),
    ],
    'forest': [
        (+0.5, ['heavy_infantry_defensive']),
        (+0.5, ['pikemen_defensive']),
        (-0.25, ['light_cavalry_defensive']),
        (-0.25, ['camel_cavalry_defensive']),
        (-0.25, ['knights_defensive']),
        (-0.25, ['archers_offensive', 'archers_defensive']),
        (-0.25, ['horse_archers_offensive', 'horse_archers_defensive']),
        (-0.25, ['war_elephants_defensive']),
    ],
    'hills': [
        (+0.5, ['light_infantry_offensive', 'light_infantry_defensive']),
        (+0.5, ['pikemen_offensive', 'pikemen_defensive']),
        (-0.25, ['light_cavalry_defensive']),
        (-0.25, ['camel_cavalry_defensive']),
        (-0.25, ['knights_defensive']),
        (+0.5, ['archers_offensive', 'archers_defensive']),
        (-0.25, ['horse_archers_defensive']),
        (-0.25, ['war_elephants_defensive']),
    ],
    'mountain': [
        (+0.75, ['light_infantry_offensive', 'light_infantry_defensive']),
        (+0.75, ['pikemen_offensive', 'pikemen_defensive']),
        (-0.25, ['light_cavalry_offensive', 'light_cavalry_defensive']),
        (-0.25, ['camel_cavalry_offensive', 'camel_cavalry_defensive']),
        (-0.25, ['knights_offensive', 'knights_defensive']),
        (+0.75, ['archers_offensive', 'archers_defensive']),
        (-0.25, ['horse_archers_offensive', 'horse_archers_defensive']),
        (-0.25, ['war_elephants_offensive', 'war_elephants_defensive']),
    ],
    'steppe': [
        (+0.5, ['light_cavalry_offensive', 'light_cavalry_defensive']),
        (+0.5, ['camel_cavalry_offensive', 'camel_cavalry_defensive']),
        (+0.5, ['knights_offensive', 'knights_defensive']),
        (+1.0, ['horse_archers_offensive', 'horse_archers_defensive']),
        (+0.5, ['war_elephants_offensive', 'war_elephants_defensive']),
    ],
    'plains': [
        (+0.5, ['light_cavalry_offensive', 'light_cavalry_defensive']),
        (+0.5, ['camel_cavalry_offensive', 'camel_cavalry_defensive']),
        (+0.5, ['knights_offensive', 'knights_defensive']),
        (+0.5, ['horse_archers_offensive', 'horse_archers_defensive']),
        (+0.5, ['war_elephants_offensive', 'war_elephants_defensive']),
    ],
    'jungle': [
        (+0.50, ['light_infantry_offensive', 'light_infantry_defensive']),
        (-0.25, ['light_cavalry_defensive']),
        (-0.25, ['camel_cavalry_defensive']),
        (-0.25, ['knights_defensive']),
        (+0.50, ['archers_offensive', 'archers_defensive']),
        (-0.25, ['horse_archers_defensive']),
        (+0.5, ['war_elephants_offensive', 'war_elephants_defensive']),
    ],
    'marsh': [
        (+0.5, ['light_infantry_offensive', 'light_infantry_defensive']),
        (-0.25, ['heavy_infantry_offensive', 'heavy_infantry_defensive']),
        (-0.25, ['pikemen_offensive', 'pikemen_defensive']),
        (-0.25, ['light_cavalry_offensive', 'light_cavalry_defensive']),
        (-0.25, ['camel_cavalry_offensive', 'camel_cavalry_defensive']),
        (-0.25, ['knights_offensive', 'knights_defensive']),
        (+0.5, ['archers_offensive', 'archers_defensive']),
        (-0.25, ['horse_archers_offensive', 'horse_archers_defensive']),
        (-0.25, ['war_elephants_offensive', 'war_elephants_defensive']),
    ],
    'desert': [
        (+0.5, ['light_cavalry_offensive', 'light_cavalry_defensive']),
        (+1.0, ['camel_cavalry_offensive', 'camel_cavalry_defensive']),
        (+0.5, ['knights_offensive', 'knights_defensive']),
        (+0.5, ['horse_archers_offensive', 'horse_archers_defensive']),
        (+0.5, ['war_elephants_offensive', 'war_elephants_defensive']),
    ]
}

def localize(outcome, skirmish):
    names = ['Disastrous', 'Confused', 'Coordinated', 'Concerted', 'Decisive',
        'Inspired', 'Legendary', 'Disorganized']
    phase = 'Maneuver' if skirmish else 'Advance'
    return f'{names[outcome + 2]} {phase}'

def terrain_mod(terrain, troop):
    if len(terrain) == 0:
        return 0
    return sum(k for k, v in terrain_mods[terrain[0]] if troop in v)

def terrain_tree(terrain):
    if len(terrain) == 0:
        return Pair('NOR', [terrain_tree([x]) for y in terrains[1:]
                                              for x in y])
    if len(terrain) == 1:
        return Pair('terrain', terrain[0])
    return Pair('OR', [terrain_tree([x]) for x in terrain])

def enemy_tree(n, k):
    return Pair('enemy', [Pair('group', f'tier_{k}_tech'),
                          Pair('factor', Number(str(0.0625 * (n - k))))])

N = 6
Q = (1 / 2) ** (1 / 7)

def factor(m, o):
    return N * Q ** abs(m - 7 * o) / sum(Q ** abs(m - 7 * x) for x in range(7))

@print_time
def main():
    parser = SimpleParser()
    parser.tab_indents = True
    parser.indent_width = 8
    parser.newlines_to_depth = 0
    toplevel = parser.parse(template)
    template_pair = toplevel.contents[0]
    skirmish = []
    melee = []
    loc_rows = ['#CODE;ENGLISH;FRENCH;GERMAN;;SPANISH;;;;;;;;;x'.split(';')]
    melee_loc_rows = []
    for tech, outcome, terrain in product(range(17), range(-2, 6), terrains):
        pair = deepcopy(template_pair)
        loc_name = localize(outcome, skirmish=True)
        melee_loc_name = localize(outcome, skirmish=False)
        leaderless = outcome == 5
        if leaderless:
            outcome = -1
        name_terrain = terrain[0] if terrain else 'generic'
        name_outcome = (f'bonus.{outcome}' if outcome > 0 else
                        'no.leader' if leaderless else
                        f'malus.{-outcome}' if outcome < 0 else 'neutral')
        pair.key.val = (f'standard_skirmish_{name_terrain}_{name_outcome}_'
                        f'tier.{tech}_tactic')
        pair.value.contents[1].value.val = outcome + 3
        pair.value.contents[2].value.val = f'tier_{tech}_tech'
        if leaderless:
            pair.value.contents[3].value.contents[1].value.val = 'no'
        pair.value.contents[3].value.contents[3].value = Obj(
            [terrain_tree(terrain)])
        tech_level = (pair.value.contents[3].value.contents[-1].value
                          .contents[0].value.contents)
        tech_level[0].value.contents[1].value.contents[0].value.val = (
            0.5 * tech)
        (tech_level[0].value.contents[1].value.contents[1].value.contents[0]
            .value.val) = 0.5 * tech + 0.5
        (tech_level[1].value.contents[1].value.contents[0].value.contents[0]
            .value.val) = 0.5 * tech
        (tech_level[1].value.contents[1].value.contents[0].value.contents[1]
            .value.contents[0].value.val) = 0.5 * tech + 0.5
        if tech == 0:
            del tech_level[0].value.contents[1].value.contents[0]
            del (tech_level[1].value.contents[1].value.contents[0].value
                 .contents[0])
        elif tech == 16:
            del tech_level[0].value.contents[1].value.contents[1]
            del (tech_level[1].value.contents[1].value.contents[0].value
                 .contents[1].value.contents[0])
        mtths = pair.value.contents[4].value.contents
        if leaderless:
            mtths[0].value.val = N
            del mtths[1:]
        else:
            mtths[1].value.contents[0].value.val = round(
                factor(0, outcome + 2), 2)
            for m in range(1, 43):
                mtths[m + 1].value.contents[0].value.val = round(
                    factor(m, outcome + 2) / factor(m - 1, outcome + 2), 2)
        for troop in pair.value.contents[5:]:
            troop.value.val = (0.25 * outcome
                + terrain_mod(terrain, troop.key.val))
        pair.value.contents.extend([enemy_tree(tech, x)
                                    for x in range(tech - 1, -1, -1)])
        melee_pair = deepcopy(pair)
        del pair.value.contents[3].value.contents[2]
        skirmish.append(pair)
        loc_rows.append([pair.key.val, loc_name] + [''] * 12 + ['x'])
        melee_pair.key.val = (f'standard_melee_{name_terrain}_{name_outcome}_'
                              f'tier.{tech}_tactic')
        melee_pair.value.contents[3].value.contents[0].value.val = 'melee'
        del melee_pair.value.contents[3].value.contents[2]
        melee.append(melee_pair)
        melee_loc_rows.append([melee_pair.key.val, melee_loc_name] + [''] * 12
                              + ['x'])
    toplevel.contents = skirmish + melee
    parser.write(toplevel, rootpath / 'dang_tactics.txt')
    loc_path = rootpath / 'dang_tactics_loc.csv'
    loc_rows += melee_loc_rows
    with loc_path.open('w', encoding='cp1252', newline='') as csvfile:
        csv.writer(csvfile, dialect='ckii').writerows(loc_rows)

if __name__ == '__main__':
    main()
