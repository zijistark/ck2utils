import re

try:
    from functools import cached_property
except: # for backwards compatibility with python versions < 3.8
    from functools import lru_cache
    def cached_property(f):
        return property(lru_cache()(f))

class NameableEntity():
    def __init__(self, name, display_name):
        self.name = name
        self.display_name = display_name

    def __str__(self):
        return self.display_name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if other is None:
            return False
        if isinstance(other, str):
            return other == self.display_name
        return self.name == other.name

    def __lt__(self, other):
        return self.display_name < str(other)

class Religion():

    def __init__(self, name, group, color):
        self.name = name
        self.group = group
        self.color = color

class IdeaGroup(NameableEntity):
    def __init__(self, name, display_name, ideas, bonus, traditions = None, category = None):
        super().__init__(name, display_name)
        self.ideas = ideas
        bonus.idea_group = self
        self.bonus = bonus
        self.traditions = traditions
        if traditions:
            traditions.idea_group = self
        self.category = category
        for idea_counter, idea in enumerate(ideas):
            idea.idea_group = self
            idea.idea_counter_in_group = idea_counter + 1

    def is_basic_idea(self):
        return self.category != None

    def get_ideas_including_traditions_and_ambitions(self):
        all_ideas = [self.bonus]
        if self.traditions:
            all_ideas.append(self.traditions)
        all_ideas.extend(self.ideas)
        return all_ideas

    def short_name(self):
        return self.display_name.replace(' Ideas', '')

class Idea(NameableEntity):
    overridden_display_names = {
        'daimyo_ideas_start': 'Daimyo traditions', # the game calls them "Sengoku Jidai"
        'TTL_ideas_start': 'Three Leagues traditions', # the game calls them "League Traditions"
    }
    def __init__(self, name, display_name, modifiers):
        if name in self.overridden_display_names:
            display_name = self.overridden_display_names[name]
        super().__init__(name, display_name)
        self.modifiers = modifiers
        self.idea_group = None
        self.idea_counter_in_group = None

    def formatted_name(self):
        if self.idea_group and self.idea_counter_in_group:
            return '{} {}: {}'.format(re.sub('ideas', 'idea',self.idea_group.display_name, flags=re.IGNORECASE), self.idea_counter_in_group, self.display_name)
        else:
            #capitalize first letter and make Traditions and Ambitions lowercase if they are not at the start of the string
            return self.display_name[0].upper() + self.display_name[1:].replace('Tradition', 'tradition').replace('Ambition', 'ambition')

    def is_bonus(self):
        return self == self.idea_group.bonus

    def is_tradition(self):
        return self == self.idea_group.traditions

class Policy(NameableEntity):
    def __init__(self, name, display_name, modifiers, idea_groups):
        super().__init__(name, display_name)
        self.modifiers = modifiers
        self.idea_groups = idea_groups
    def formatted_name(self):
        return '{}-{}: {}'.format(
            self.idea_groups[0].short_name(),
            self.idea_groups[1].short_name(),
            self.display_name)


