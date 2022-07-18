import sys
import os
import re
from collections import OrderedDict
# add the parent folder to the path so that imports work even if the working directory is the eu4 folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from ck2parser import SimpleParser, Obj
from localpaths import eu4dir
from eu4.paths import eu4_version
from eu4.eu4lib import Religion, Idea, IdeaGroup, Policy, Eu4Color, Country
from eu4.cache import disk_cache, cached_property


class Eu4Parser:
    """the methods of this class parse game files and retrieve all kinds of information

    map, event or decision related methods are in the subclasses
    Eu4MapParser. Eu4EventParser and Eu4DecisionParser instead
    """

    # allows the overriding of localisation strings
    localizationOverrides = {}

    def __init__(self):
        self.parser = SimpleParser()
        self.parser.basedir = eu4dir

    @cached_property
    @disk_cache()
    def _localisation_dict(self):
        localisation_dict = {}
        for path in (eu4dir / 'localisation').glob('*_l_english.yml'):
            with path.open(encoding='utf-8-sig') as f:
                for line in f:
                    match = re.fullmatch(r'\s*([^#\s:]+):\d?\s*"(.*)"[^"]*', line)
                    if match:
                        localisation_dict[match.group(1)] = match.group(2)
        localisation_dict.update(self.localizationOverrides)
        return localisation_dict

    def localize(self, key: str, default: str = None) -> str:
        """localize the key from the english eu4 localisation files

        if the key is not found, the default is returned
        unless it is None in which case the key is returned
        """
        if default is None:
            default = key

        return self._localisation_dict.get(key, default)

    @cached_property
    def eu4_version(self):
        return eu4_version()

    @cached_property
    def eu4_major_version(self):
        return '.'.join(self.eu4_version.split('.')[0:2])

    @cached_property
    def all_religions(self):
        all_religions = {}
        for _, tree in self.parser.parse_files('common/religions/*'):
            for group, religions in tree:
                for religion, data in religions:
                    if religion.val in ['defender_of_faith', 'can_form_personal_unions', 'center_of_religion',
                                        'flags_with_emblem_percentage', 'flag_emblem_index_range',
                                        'harmonized_modifier', 'crusade_name', 'ai_will_propagate_through_trade',
                                        'religious_schools']:
                        continue
                    color = Eu4Color.new_from_parser_obj(data['color'])
                    all_religions[religion.val] = Religion(religion.val, group.val, color)
        return all_religions

    def _process_idea_modifiers(self, data):
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
                                     self._process_idea_modifiers(v2))
                    elif idea_name == 'start':
                        traditions = Idea(idea_group_name + '_start',
                                          self.localize(idea_group_name + '_start'),
                                          self._process_idea_modifiers(v2))
                    elif idea_name == 'category':
                        category = v2.val
                    else:
                        if len(v2) == 0:
                            modifiers = all_ideas[idea_name].modifiers
                        else:
                            modifiers = self._process_idea_modifiers(v2)
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
                                raise Exception(
                                    'Unexpected key in allow section of the policy "{}"'.format(policy_name))
                    else:
                        modifiers[n2.val] = v2.val
                all_policies[policy_name] = Policy(policy_name,
                                                   self.localize(policy_name),
                                                   category,
                                                   modifiers,
                                                   idea_groups)
        return all_policies

    @cached_property
    def culture_groups(self):
        """Script names of the culture groups.

        preserves the order of the cultures files
        """
        culture_groups = []
        for _, tree in self.parser.parse_files('common/cultures/*'):
            for n, v in tree:
                culture_groups.append(n.val)
        return culture_groups

    @cached_property
    def culture_to_culture_group_mapping(self):
        cultures = {}
        for _, tree in self.parser.parse_files('common/cultures/*'):
            for n, v in tree:
                for n2, v2 in v:
                    if (isinstance(v2, Obj) and
                            not re.match(r'((fe)?male|dynasty)_names', n2.val)):
                        cultures[n2.val] = n.val
        return cultures

    @cached_property
    def all_countries(self):
        """returns a dictionary. keys are tags and values are Country objects. It is ordered by the tag order"""
        countries = OrderedDict()
        for tag, country_file in self.parser.parse_file('common/country_tags/00_countries.txt'):
            countries[tag.val] = Country(tag.val, self.localize(tag.val), parser=self, country_file=country_file.val)
        return countries

    @cached_property
    @disk_cache()
    def tag_to_color_mapping(self):
        country_colors = {}
        for c in self.all_countries.values():
            country_data = self.parser.parse_file('common/' + c.country_file)
            country_colors[c.tag] = Eu4Color.new_from_parser_obj(country_data['color'])
        return country_colors

    def get_country_color(self, country):
        return self.tag_to_color_mapping[country.tag]


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == '--eu4-version':
        # just print the version number so external scripts can use it
        print(eu4_version())
    else:
        raise Exception("unknown parameters. Only --eu4-version is accepted")
