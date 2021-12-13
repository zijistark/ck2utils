import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from localpaths import eu4dir
from eu4.paths import eu4_version
from ck2parser import SimpleParser

import re

from eu4.eu4lib import Religion, Idea, IdeaGroup, Policy
from colormath import color_objects


try:
    from functools import cached_property
except: # for backwards compatibility with python versions < 3.8
    from functools import lru_cache
    def cached_property(f):
        return property(lru_cache()(f))


class Eu4Parser(object):
    '''
    classdocs
    '''
    localizationOverrides = {}

    def __init__(self):
        '''
        Constructor
        '''
        self.parser = SimpleParser()
        self.parser.basedir = eu4dir
        self.localisation_dict = None

    def localize (self, key, default=None):
        if default is None:
            default = key
        if not self.localisation_dict:
            self.localisation_dict = {}
            for path in (eu4dir / 'localisation').glob('*_l_english.yml'):
                with path.open(encoding='utf-8-sig') as f:
                    for line in f:
                        match = re.fullmatch(r'\s*([^#\s:]+):\d?\s*"(.*)"[^"]*', line)
                        if match:
                            self.localisation_dict[match.group(1)] = match.group(2)
            self.localisation_dict.update(self.localizationOverrides)
        return self.localisation_dict.get(key, default)

    @cached_property
    def eu4_version(self):
        return eu4_version()

    @cached_property
    def all_religions(self):
        all_religions = {}
        for _, tree in self.parser.parse_files('common/religions/*'):
            for group, religions in tree:
                for religion, data in religions:
                    if religion.val in ['defender_of_faith', 'can_form_personal_unions', 'center_of_religion', 'flags_with_emblem_percentage', 'flag_emblem_index_range', 'harmonized_modifier', 'crusade_name','ai_will_propagate_through_trade', 'religious_schools']:
                        continue
                    color = color_objects.sRGBColor(data['color'].contents[0].val, data['color'].contents[1].val, data['color'].contents[2].val, is_upscaled=True)
                    all_religions[religion.val] = Religion(religion.val, group.val, color)
        return all_religions

    def process_idea_modifirs(self, data):
        modifiers = {}
        for modifier, value in data:
            modifiers[modifier.val] = value.val
        return modifiers

    @cached_property
    def all_idea_groups(self, filter_groups=['SYN_ideas', 'JMN_ideas']):
        # collect all ideas to handle duplicate ideas which are not always specified again
        all_ideas = {}
        all_idea_groups = {}
        for _, tree in self.parser.parse_files('common/ideas/*'):
            for n, v in tree:
                idea_group_name = n.val
                if idea_group_name in filter_groups:
                    continue
                category = None
                bonus = None
                traditions = None
                ideas = []
                if idea_group_name == 'compatibility_127':
                    continue
                for n2, v2 in v:
                    idea_name = n2.val
                    if idea_name in ['trigger', 'free', 'ai_will_do', 'important']:
                        continue
                    if idea_name == 'bonus':
                        bonus = Idea(idea_group_name + '_bonus',
                                     self.localize(idea_group_name + '_bonus'),
                                     self.process_idea_modifirs(v2))
                    elif idea_name == 'start':
                        traditions = Idea(idea_group_name + '_start',
                                         self.localize(idea_group_name + '_start'),
                                         self.process_idea_modifirs(v2))
                    elif idea_name == 'category':
                        category = v2.val
                    else:
                        if len(v2) ==  0:
                            modifiers = all_ideas[idea_name].modifiers
                        else:
                            modifiers = self.process_idea_modifirs(v2)
                        idea = Idea(idea_name,
                                      self.localize(idea_name),
                                      modifiers)
                        ideas.append(idea)
                        all_ideas[idea_name] = idea

                idea_group = IdeaGroup(idea_group_name,
                                       self.localize(idea_group_name),
                                       ideas,
                                       bonus,
                                       traditions,
                                       category)
                all_idea_groups[idea_group_name] = idea_group
        return all_idea_groups


    @cached_property
    def ideas_and_policies_by_modifier(self):
        ideas_and_policies_by_modifier = {}
        for idea_group in self.all_idea_groups.values():
            for idea in idea_group.get_ideas_including_traditions_and_ambitions():
                for modifier, value in idea.modifiers.items():
                    if modifier not in ideas_and_policies_by_modifier:
                        ideas_and_policies_by_modifier[modifier] = {}
                    if value not in ideas_and_policies_by_modifier[modifier]:
                        ideas_and_policies_by_modifier[modifier][value] = []
                    ideas_and_policies_by_modifier[modifier][value].append(idea)
        for policy in self.all_policies.values():
            for modifier, value in policy.modifiers.items():
                if modifier not in ideas_and_policies_by_modifier:
                    ideas_and_policies_by_modifier[modifier] = {}
                if value not in ideas_and_policies_by_modifier[modifier]:
                    ideas_and_policies_by_modifier[modifier][value] = []
                ideas_and_policies_by_modifier[modifier][value].append(policy)
        return ideas_and_policies_by_modifier

    @cached_property
    def all_policies(self):
        all_policies = {}
        for _, tree in self.parser.parse_files('common/policies/*'):
            for n, v in tree:
                policy_name = n.val
                category = None
                idea_groups = []
                modifiers = {}
                for n2, v2 in v:
                    if n2.val in ['potential', 'ai_will_do']:
                        pass
                    elif n2.val == 'monarch_power':
                        category = v2.val
                    elif n2.val == 'allow':
                        for n3, v3 in v2:
                            if n3.val == 'full_idea_group':
                                idea_groups.append(self.all_idea_groups[v3.val])
                            else:
                                raise Exception('Unexpected key in allow section of the policy "{}"'.format(policy_name))
                    else:
                        modifiers[n2.val] = v2.val
                all_policies[policy_name] = Policy(policy_name,
                                                   self.localize(policy_name),
                                                   modifiers,
                                                   idea_groups)
        return all_policies

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == '--eu4-version':
        # just print the version number so external scripts can use it
        print(eu4_version())
    else:
        raise Exception("unknown paramters. Only --eu4-version is accepted")
