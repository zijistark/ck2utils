#!/usr/bin/env python3

import shutil
from ck2parser import rootpath, Pair, Obj, Op, String, FullParser
from print_time import print_time

def mutate_cb(cb_pair):
    name, tree = cb_pair.key.val, cb_pair.value
    third_party = name.startswith('other_')
    check_de_jure_tier = 'check_de_jure_tier' in tree.dictionary
    least_index = float('inf')
    # remove & handle can_use, possibly skipping this CB
    try:
        can_use = next(p for p in tree if p.key.val == 'can_use')
        if can_use.value.has_pair('always', 'no'):
            return
        index = tree.contents.index(can_use)
        least_index = min(index, least_index)
        tree.contents.remove(can_use)
    except StopIteration:
        can_use = Pair('can_use')
    if third_party:
        trigger_name = 'emf_cb_thirdparty_can_use_trigger'
    else:
        trigger_name = 'emf_cb_can_use_trigger'
    trigger = Pair(trigger_name, 'yes')
    if not can_use.value.has_pair(trigger_name, 'yes'):
        can_use.value.contents.insert(0, trigger)
    # remove & handle can_use_gui
    if (tree.has_pair('major_revolt', 'yes') or
        tree.has_pair('is_revolt_cb', 'yes')):
        can_use_gui = None
    else:
        try:
            can_use_gui = next(p for p in tree if p.key.val == 'can_use_gui')
            index = tree.contents.index(can_use_gui)
            least_index = min(index, least_index)
            tree.contents.remove(can_use_gui)
        except StopIteration:
            can_use_gui = Pair('can_use_gui')
        if third_party:
            trigger_name = 'emf_cb_thirdparty_can_use_gui_trigger'
        else:
            trigger_name = 'emf_cb_can_use_gui_trigger'
        trigger = Pair(trigger_name, 'yes')
        if not can_use_gui.value.has_pair(trigger_name, 'yes'):
            can_use_gui.value.contents.insert(0, trigger)
    # remove & handle can_use_title
    try:
        can_use_title = next(p for p in tree if p.key.val == 'can_use_title')
        index = tree.contents.index(can_use_title)
        least_index = min(index, least_index)
        tree.contents.remove(can_use_title)
    except StopIteration:
        can_use_title = None
    if can_use_title:
        if check_de_jure_tier:
            if third_party:
                trigger_name = (
                    'emf_cb_thirdparty_can_use_de_jure_title_trigger')
            else:
                trigger_name = 'emf_cb_can_use_de_jure_title_trigger'
            trigger = Pair(trigger_name, 'yes')
            if not can_use_title.value.has_pair(trigger_name, 'yes'):
                can_use_title.value.contents.insert(0, trigger)
        else:
            if third_party:
                trigger_name = 'emf_cb_thirdparty_can_use_title_trigger'
            else:
                trigger_name = 'emf_cb_can_use_title_trigger'
            trigger = Pair(trigger_name, 'yes')
            if not can_use_title.value.has_pair(trigger_name, 'yes'):
                can_use_title.value.contents.append(trigger)
    # reinsert
    if can_use_title:
        tree.contents.insert(least_index, can_use_title)
    if can_use:
        tree.contents.insert(least_index, can_use)
    if can_use_gui:
        tree.contents.insert(least_index, can_use_gui)
    # handle & insert effects
    try:
        on_success_posttitle = next(p for p in tree
                                    if p.key.val == 'on_success_posttitle')
    except StopIteration:
        on_success_posttitle = make_empty_obj_pair('on_success_posttitle')
        index = next((i for i, p in enumerate(tree)
                      if p.key.val == 'on_success_title'),
                     next(i for (i, p) in enumerate(tree)
                          if p.key.val == 'on_success')) + 1
        tree.contents.insert(index, on_success_posttitle)
    if third_party:
        effect_name = 'emf_cb_thirdparty_on_success_posttitle_effect'
    else:
        effect_name = 'emf_cb_on_success_posttitle_effect'
    effect = Pair(effect_name, 'yes')
    if not on_success_posttitle.value.has_pair(effect_name, 'yes'):
        on_success_posttitle.value.contents.append(effect)

@print_time
def main():
    swmhpath = rootpath / 'SWMH-BETA/SWMH'
    emfpath = rootpath / 'EMF/EMF'
    emfswmhpath = rootpath / 'EMF/EMF+SWMH'
    swmhhistory = swmhpath / 'history'
    emfswmhhistory = emfswmhpath / 'history'
    parser = FullParser()
    parser.fq_keys.append('name')
    parser.no_fold_to_depth = 1
    # parser.no_fold_keys.extend(['factor', 'value'])
    parser.newlines_to_depth = 0

    # shutil.rmtree(str(emfswmhhistory), ignore_errors=True)
    # emfswmhhistory.mkdir(parents=True)
    
    # (emfswmhhistory / 'characters').mkdir()
    path = swmhhistory / 'characters/hungarian.txt'
    tree = parser.parse_file(path)
    effect = tree[159137][867, 1, 1]['effect']
    effect.contents = [p for p in effect.contents
                       if p.key.val == 'create_character']
    effect.contents[:0] = parser.parse('''
# Truce with Bulgaria until 887
random_independent_ruler = {
    limit = { has_landed_title = k_bulgaria }
    opinion = { who = ROOT modifier = in_non_aggression_pact years = 20 }
}
if = {
    limit = { is_nomadic = yes }
    spawn_unit = {
        province = 1147 # Bacau
        owner = ROOT
        troops = {
            light_cavalry = { 465 465 }
            horse_archers = { 235 235 }
        }
        attrition = 0.25
        reinforces = yes
        earmark = start_troops
    }
    spawn_unit = {
        province = 1147 # Bacau
        owner = ROOT
        troops = {
            light_cavalry = { 465 465 }
            horse_archers = { 235 235 }
        }
        attrition = 0.25
        reinforces = yes
        earmark = start_troops
    }
}
        ''').contents
    targetpath = emfswmhhistory / path.relative_to(swmhhistory)
    with targetpath.open('w', encoding='cp1252', newline='\r\n') as f:
        f.write(tree.str(parser))

    # for path, tree in parser.parse_files('common/cb_types/*', basedir=MODPATH):
    #     # for cb_pair in tree:
    #     #     mutate_cb(cb_pair)
    #     with path.open('w', encoding='cp1252', newline='\r\n') as f:
    #         f.write(tree.str(parser))

if __name__ == '__main__':
    main()
