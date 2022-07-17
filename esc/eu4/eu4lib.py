import re
from colormath.color_objects import sRGBColor
from eu4.provincelists import coastal_provinces
from eu4.cache import cached_property


class Province(object):

    def __init__(self, provinceID, parser=None):
        self.id = provinceID
        self.parser = parser
        self.name = parser.localize('PROV{}'.format(provinceID))
        self.center_of_trade = 0
        self.attributes = {}

    def __str__(self, *args, **kwargs):
        return '{} ({})'.format(self.name, self.id)

    def __setitem__(self, key, value):
        if key in ['ID', 'Name', 'Type', 'Continent', 'center_of_trade']:
            setattr(self, key.lower(), value)
        else:
            self.attributes.__setitem__(key, value)

    def __getitem__(self, key):
        if hasattr(self, key.lower().replace(' ', '')):
            return getattr(self, key.lower().replace(' ', ''))
        return self.attributes.__getitem__(key)

    def __contains__(self, key):
        if hasattr(self, key.lower().replace(' ', '')):
            return True
        return key in self.attributes

    def get(self, key, default=None):
        if hasattr(self, key.lower().replace(' ', '')):
            return getattr(self, key.lower().replace(' ', ''))
        return self.attributes.get(key, default)

    @property
    def type(self):
        return self.parser.get_province_type(self.id)

    @cached_property
    def continent(self):
        return self.parser.get_continent(self)

    @cached_property
    def area(self):
        return self.parser.get_area(self)

    @cached_property
    def region(self):
        return self.parser.get_region(self.area.name)

    @cached_property
    def superregion(self):
        return self.parser.get_superregion(self.region.name)

    @cached_property
    def tradenode(self):
        return self.parser.get_trade_node(self)

    @cached_property
    def has_port(self):
        return self.id in coastal_provinces

    def format_center_of_trade_string(self):
        if self.has_port:
            cot_names = {1: 'Natural Harbor', 2: 'Entrepot', 3: 'World Port'}
        else:
            cot_names = {1: 'Emporium', 2: 'Market Town', 3: 'World Trade Center'}
        return cot_names[self.center_of_trade]


class NameableEntity:
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


class NameableEntityWithProvinces(NameableEntity):

    def __init__(self, name, display_name, provinces=None, provinceIDs=None, parser=None):
        super().__init__(name, display_name)
        self._provinces = provinces
        self._provinceIDs = provinceIDs
        self.parser = parser

    @cached_property
    def provinces(self):
        if self._provinces is None:
            self._provinces = [self.parser.all_provinces[provinceID] for provinceID in self._provinceIDs]
        return self._provinces

    @cached_property
    def provinceIDs(self):
        if self._provinceIDs is None:
            self._provinceIDs = [province.id for province in self._provinces]
        return self._provinceIDs


class NameableEntityWithProvincesAndColor(NameableEntityWithProvinces):
    def __init__(self, name, display_name, provinces=None, provinceIDs=None, parser=None, color=None):
        super().__init__(name, display_name, provinces, provinceIDs, parser)
        self.color = color


class Continent(NameableEntityWithProvinces):
    pass


class Area(NameableEntityWithProvinces):

    def __init__(self, name, display_name, provinces=None, provinceIDs=None, parser=None, color=None):
        super().__init__(name, display_name, provinces, provinceIDs, parser)
        self.color = color

    @cached_property
    def region(self):
        return self.parser.get_region(self.name)

    @cached_property
    def contains_land_provinces(self):
        for province in self.provinces:
            if province.type == 'Land':
                return True
        return False

    @cached_property
    def contains_inland_seas(self):
        for province in self.provinces:
            if province.type == 'Inland sea':
                return True
        return False


class Region(NameableEntity):

    def __init__(self, name, display_name, areas=None, area_names=None, parser=None):
        super().__init__(name, display_name)
        self._areas = areas
        self.area_names = area_names
        self.parser = parser
        self._provinceIDs = None

    @property
    def areas(self):
        if not self._areas:
            self._areas = [self.parser.all_areas[area_name] for area_name in self.area_names if
                           area_name in self.parser.all_areas]
        return self._areas

    @cached_property
    def superregion(self):
        return self.parser.get_superregion(self.name)

    @cached_property
    def contains_land_provinces(self):
        for area in self.areas:
            if area.contains_land_provinces:
                return True
        return False

    @cached_property
    def contains_inland_seas(self):
        for area in self.areas:
            if area.contains_inland_seas:
                return True
        return False

    @cached_property
    def provinceIDs(self):
        if self._provinceIDs is None:
            self._provinceIDs = []
            #             [provinceID for area in self.areas for provinceID in area.provinceIDs ]
            for area in self.areas:
                self._provinceIDs.extend(area.provinceIDs)
        return self._provinceIDs

    @cached_property
    def color(self):
        return self.parser.region_colors[self.name]


class Superregion(NameableEntity):

    def __init__(self, name, display_name, regions=None, region_names=None, parser=None):
        super().__init__(name, display_name)
        self._regions = regions
        self.region_names = region_names
        self.parser = parser

    @property
    def regions(self):
        if not self._regions:
            self._regions = [self.parser.all_regions[region_name] for region_name in self.region_names]
        return self._regions

    @cached_property
    def contains_land_provinces(self):
        for region in self.regions:
            if region.contains_land_provinces:
                return True
        return False


class ColonialRegion(NameableEntityWithProvincesAndColor):
    pass


class Terrain(NameableEntityWithProvincesAndColor):
    pass


class Country(NameableEntity):
    def __init__(self, tag, display_name, color=None, parser=None, country_file=None):
        super().__init__(tag, display_name)
        self.tag = tag
        self.color = color
        if color:
            print(tag)
        self.parser = parser
        self.country_file = country_file

    def get_color(self):
        if not self.color:
            self.color = self.parser.get_country_color(self)
        return self.color


class Event:

    def __init__(self, parser, attributes):
        self.parser = parser
        self.attributes = attributes
        self.id = attributes['id'].val_str()
        self.title = parser.localize(attributes['title'].val_str())
        self.desc = parser.localize(attributes['desc'].val_str(), 'variable desc')


class Decision:

    def __init__(self, parser, decision_id, attributes):
        self.parser = parser
        self.attributes = attributes
        self.id = decision_id
        self.title = parser.localize('{}_title'.format(decision_id))
        self.desc = parser.localize('{}_desc'.format(decision_id), 'no desc')


class Religion:

    def __init__(self, name, group, color):
        self.name = name
        self.group = group
        self.color = color


class TradeCompany(NameableEntityWithProvincesAndColor):
    pass


class TradeNode(NameableEntityWithProvincesAndColor):

    def __init__(self, name, display_name, location, outgoing_node_names=None, inland=False, endnode=False, provinces=None, provinceIDs=None, parser=None, color=None):
        super().__init__(name, display_name, provinces, provinceIDs, parser, color)
        self.location = location
        if outgoing_node_names is not None:
            self.outgoing_node_names = outgoing_node_names
        else:
            self.outgoing_node_names = []
        self.inland = inland
        self.endnode = endnode

    @cached_property
    def outgoing_nodes(self):
        return [self.parser.all_trade_nodes[name] for name in self.outgoing_node_names]

    @cached_property
    def incoming_nodes(self):
        return [node for node in self.parser.all_trade_nodes.values() if self.name in node.outgoing_node_names]


class IdeaGroup(NameableEntity):
    overridden_display_names = {
        'latin_ideas': 'Italian (minor) ideas',
    }

    def __init__(self, name, display_name, ideas, bonus, traditions=None, category=None):
        if name in self.overridden_display_names:
            display_name = self.overridden_display_names[name]
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
        return self.category is not None

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
        'daimyo_ideas_start': 'Daimyo traditions',  # the game calls them "Sengoku Jidai"
        'TTL_ideas_start': 'Three Leagues traditions',  # the game calls them "League Traditions"
        'latin_ideas_start': 'Italian (minor) traditions',
        'latin_ideas_bonus': 'Italian (minor) ambition',
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
            return '{} {}: {}'.format(re.sub('ideas', 'idea', self.idea_group.display_name, flags=re.IGNORECASE),
                                      self.idea_counter_in_group, self.display_name)
        else:
            # capitalize first letter and make Traditions and Ambitions lowercase if they are not at the start of the string
            return self.display_name[0].upper() + self.display_name[1:].replace('Tradition', 'tradition').replace(
                'Ambition', 'ambition')

    def is_bonus(self):
        return self == self.idea_group.bonus

    def is_tradition(self):
        return self == self.idea_group.traditions


class Policy(NameableEntity):
    def __init__(self, name, display_name, category, modifiers, idea_groups):
        super().__init__(name, display_name)
        self.category = category
        self.modifiers = modifiers
        self.idea_groups = idea_groups

    def formatted_name(self):
        return '{}-{}: {}'.format(
            self.idea_groups[0].short_name(),
            self.idea_groups[1].short_name(),
            self.display_name)


class Eu4Color(sRGBColor):

    def __init__(self, r, g, b, is_upscaled=True):
        super().__init__(r, g, b, is_upscaled=is_upscaled)

    def get_css_color_string(self):
        rgb_r, rgb_g, rgb_b = self.get_upscaled_value_tuple()
        return 'rgb({},{},{})'.format(rgb_r, rgb_g, rgb_b)

    @classmethod
    def new_from_parser_obj(cls, color_obj):
        """create an Eu4Color object from an ck2parser Obj.

        The Obj must contain a list/tuple of rgb values.
        For example if the following pdx script is parsed into the variable data:
            color = { 20 50 210 }
        then this function could be called in the following way:
            Eu4Color.new_from_parser_obj(data['color'])
        """
        return cls(color_obj.contents[0].val, color_obj.contents[1].val, color_obj.contents[2].val, is_upscaled=True)
