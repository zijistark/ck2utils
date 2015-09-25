# Ioannes Barbarus
# nicholas.escalona@gmail.com

# requires:
#     >= Python 3.4
#     >= funcparserlib 0.3.6
#     >= NetworkX 0.32
#     >= NumPy 1.9.0
#     >= Pillow 2.0.0
#     >= tabulate 0.7.3

import collections
import csv
import datetime
import operator
import pathlib
import re
import statistics
import funcparserlib
import funcparserlib.lexer
import funcparserlib.parser
import networkx
import numpy
import PIL
import PIL.Image
import tabulate

CKII_DIR = pathlib.Path(
    'C:/Program Files (x86)/Steam/SteamApps/common/Crusader Kings II')

OUTPUT_FILE = pathlib.Path('C:/Users/Nicholas/Desktop/table.txt')
BORDERS_PATH = pathlib.Path('C:/Users/Nicholas/Pictures/CKII/borderlayer.png')

class Interval:
    def __init__(self, start, stop):
        self.start = start
        self.stop = stop

    def __contains__(self, item):
        try:
            return self.start <= item < self.stop
        except TypeError:
            return False

class Title:
    instances = {}
    id_title_map = {}
    id_name_map = {}
    rgb_id_map = {}
    waters = set()
    rivers = set()
    # seas = set()
    province_graph = networkx.Graph()
    kingdom_graph = networkx.Graph()

    @classmethod
    def valid_codename(cls, string):
        try:
            return re.match(r'[ekdcb]_', string)
        except TypeError:
            return False

    @classmethod
    def all(cls):
        return Title.instances.values()

    @classmethod
    def duchies(cls):
        return (title for title in Title.all()
                if title.codename.startswith('d_'))

    @classmethod
    def counties(cls):
        return (title for title in Title.all()
                if title.codename.startswith('c_'))

    @classmethod
    def get(cls, title, create_if_missing=False):
        if title == 0:
            return None
        if isinstance(title, Title):
            return title
        if not Title.valid_codename(title):
            raise ValueError('Invalid title {}'.format(title))
        if create_if_missing and title not in Title.instances:
            Title.instances[title] = Title(title)
        return Title.instances[title]

    def __init__(self, codename):
        self.codename = codename
        self.lieges = {}
        self.vassal_intvls = collections.defaultdict(list)
        self.builts = {}
        self.cultures = {}
        self.religions = {}
        self.name = localisation.get(codename, codename)
        self.other_names = []
        self.neighbors = []
        Title.instances[codename] = self

    def set_id(self, province_id):
        if not province_id > 0:
            raise ValueError('{} province id {} is nonpositive'.format(
                             self.codename, province_id))
        self.id = province_id
        Title.id_title_map[province_id] = self
        if self.name == self.codename:
            key = 'PROV{}'.format(self.id)
            self.set_name(localisation.get(key, self.codename))

    def set_name(self, name):
        self.other_names = [x for x in self.other_names if x != name]
        self.name = name

    def add_other_name(self, name):
        if name != self.name and name not in self.other_names:
            self.other_names.append(name)

    def build(self, from_when=datetime.date.min):
        self.builts[from_when] = True

    def destroy(self, from_when=datetime.date.min):
        self.builts[from_when] = False

    def built(self, when=datetime.date.min):
        try:
            return self.builts[max(date for date in self.builts if
                                   date <= when)]
        except ValueError:
            return False

    def built_holdings(self, when=datetime.date.min):
        return (t for t in self.vassals(when) if t.built(when))

    def set_liege(self, liege, from_when=datetime.date.min):
        try:
            liege = Title.get(liege)
        except KeyError:
            liege = self.liege()
        prev_liege = self.liege(from_when)
        if prev_liege is not None:
            intvl = next(intvl for intvl in prev_liege.vassal_intvls[self] if
                         from_when in intvl)
            intvl.stop = from_when
        self.lieges[from_when] = liege
        to_when = min((date for date in self.lieges if date > from_when),
                      default=datetime.date.max)
        if liege is not None:
            liege.vassal_intvls[self].append(Interval(from_when, to_when))

    def liege(self, when=datetime.date.min):
        try:
            return self.lieges[max(date for date in self.lieges if
                                   date <= when)]
        except ValueError:
            return None

    def culture(self, when=datetime.date.min):
        try:
            culture = self.cultures[max(date for date in self.cultures if
                                    date <= when)]
        except ValueError:
            return None
        return localisation.get(culture, culture)

    def religion(self, when=datetime.date.min):
        try:
            religion = self.religions[max(date for date in self.religions if
                                      date <= when)]
        except ValueError:
            return None
        return localisation.get(religion, religion)

    def vassals(self, when=datetime.date.min):
        return (title for title, intvls in self.vassal_intvls.items() if
                any(when in intvl for intvl in intvls))

    def coastal(self):
        return any(x in Title.seas for x in Title.province_graph[self.id])

cultures = []
localisation = {}

def tokenize(string):
    token_specs = [
        ('comment', (r'#.*',)),
        ('whitespace', (r'\s+',)),
        ('op', (r'[={}]',)),
        ('date', (r'\d*\.\d*\.\d*',)),
        ('number', (r'\d+(\.\d+)?',)),
        ('quoted_string', (r'"[^"#]*"',)),
        ('unquoted_string', (r'[^\s"#={}]+',))
    ]
    useless = ['comment', 'whitespace']
    inner_tokenize = funcparserlib.lexer.make_tokenizer(token_specs)
    return (tok for tok in inner_tokenize(string) if tok.type not in useless)

def parse(tokens):
    def unquote(string):
        return string[1:-1]

    def make_number(string):
        try:
            return int(string)
        except ValueError:
            return float(string)

    def make_date(string):
        # CKII appears to default to 0, not 1, but that's awkward to handle
        # with datetime, and it only comes up for b_embriaco anyway
        year, month, day = ((int(x) if x else 1) for x in string.split('.'))
        return datetime.date(year, month, day)

    def some(tok_type):
        return (funcparserlib.parser.some(lambda tok: tok.type == tok_type) >>
                (lambda tok: tok.value))

    def op(string):
        return funcparserlib.parser.skip(funcparserlib.parser.a(
            funcparserlib.lexer.Token('op', string)))

    many = funcparserlib.parser.many
    fwd = funcparserlib.parser.with_forward_decls
    endmark = funcparserlib.parser.skip(funcparserlib.parser.finished)
    unquoted_string = some('unquoted_string')
    quoted_string = some('quoted_string') >> unquote
    number = some('number') >> make_number
    date = some('date') >> make_date
    key = unquoted_string | quoted_string | number | date
    value = fwd(lambda: obj | key)
    pair = fwd(lambda: key + op('=') + value)
    obj = fwd(lambda: op('{') + many(pair | value) + op('}'))
    toplevel = many(pair | value) + endmark
    return toplevel.parse(list(tokens))

def parse_files(glob):
    return ((path.stem, parse_file(path)) for path in
            pathlib.Path(CKII_DIR).glob(glob))

def parse_file(path):
    with path.open(encoding='latin-1') as f:
        s = f.read()
    return parse(tokenize(s))

def process_cultures(cultures_txts):
    for _, v in cultures_txts:
        cultures.extend(n2 for _, v1 in v for n2, v2 in v1
                        if isinstance(v2, list))

# pre: process_localisation
# pre: process_cultures
def process_landed_titles(landed_titles_txts):
    def recurse(v, n=None):
        for n1, v1 in v:
            try:
                title = Title.get(n1, create_if_missing=True)
            except ValueError:
                continue
            if n is not None:
                title.set_liege(n)
            for n2, v2 in v1:
                if n2 in cultures:
                    title.add_other_name(v2)
            recurse(v1, n1)

    for _, v in landed_titles_txts:
        recurse(v)

# pre: process_landed_titles
def process_provinces(provinces_txts):
    for n, v in provinces_txts:
        v_dict = dict(v)
        title = Title.get(v_dict['title'])
        id_str, name = n.split(' - ')
        title.set_id(int(id_str))
        if title.name == title.codename:
            title.set_name(name)
        title.max_holdings = v_dict['max_settlements']
        title.cultures[datetime.date(1, 1, 1)] = v_dict['culture']
        title.religions[datetime.date(1, 1, 1)] = v_dict['religion']
        for n1, v1 in v:
            if Title.valid_codename(n1):
                try:
                    holding = Title.get(n1)
                except KeyError:
                    print('unknown holding {} in {}.txt'.format(n1, n))
                    continue
                holding.set_liege(title)
                holding.build()
            elif isinstance(n1, datetime.date):
                for n2, v2 in v1:
                    if n2 == 'name':
                        title.add_other_name(v2)
                    elif n2 == 'culture':
                        title.cultures[n1] = v2
                    elif n2 == 'religion':
                        title.religions[n1] = v2
                    elif n2 == 'remove_settlement':
                        Title.get(v2).destroy(n1)
                    elif (Title.valid_codename(n2) and isinstance(v2, str) and
                          re.fullmatch(r'castle|city|temple|tribal', v2)):
                        Title.get(n2).build(n1)

def process_titles(titles_txts):
    for n, v in titles_txts:
        title = Title.get(n)
        for n1, v1 in v:
            if isinstance(n1, datetime.date):
                v1_dict = dict(v1)
                liege = v1_dict.get('de_jure_liege')
                if liege:
                    title.set_liege(liege, from_when=n1)
                name_key = v1_dict.get('name')
                if name_key:
                    title.add_other_name(localisation[name_key])

def parse_csvs(paths, row_func):
    for path in paths:
        parse_csv(path, row_func)

def parse_csv(path, row_func):
    with path.open(encoding='latin-1', newline='') as csvfile:
        reader = csv.reader(csvfile, dialect='ckii')
        for row in reader:
            row_func(row)

def process_localisation_row(row):
    key, value, *_ = row
    if key not in localisation:
        localisation[key] = value

# pre: process_provinces
def process_default_map(default_map):
    v_dict = dict(default_map)
    Title.max_provinces = int(v_dict['max_provinces'])
    for n, v in default_map:
        if n == 'sea_zones':
            first_zone, last_zone = map(int, v)
            Title.waters.update(range(first_zone, last_zone + 1))
    for n, v in default_map:
        if n == 'major_rivers':
            Title.rivers.update(map(int, v))
    return tuple(CKII_DIR / 'map' / v_dict[key] for key in
                 ['definitions', 'provinces', 'adjacencies'])

# pre: process default_map, provinces
def process_map_definitions_row(row):
    try:
        province, red, green, blue = map(int, row[:4])
    except ValueError:
        return
    if province < Title.max_provinces:
        try:
            Title.id_title_map[province].rgb = red, green, blue
        except KeyError:
            pass
        key = tuple(numpy.uint8(x) for x in (red, green, blue))
        Title.rgb_id_map[key] = province
        Title.id_name_map[province] = row[4]

# pre: process map definitions
def parse_map_provinces(path):
    def province_id(rgb):
        return Title.rgb_id_map.get(tuple(rgb), 0)

    image = PIL.Image.open(str(path))
    image = numpy.array(image)
    for i, j in numpy.ndindex(image.shape[0] - 1, image.shape[1] - 1):
        province = province_id(image[i, j])
        if province != 0:
            neighbor_x = province_id(image[i, j + 1])
            neighbor_y = province_id(image[i + 1, j])
            for neighbor in [neighbor_x, neighbor_y]:
                if neighbor != province and neighbor != 0:
                    Title.province_graph.add_edge(province, neighbor)
    seas_lakes = Title.province_graph.subgraph(Title.waters - Title.rivers)
    Title.seas = {x for x in seas_lakes if seas_lakes[x]}

def generate_holding_map(in_path, out_path):
    COLORMAP = {1: numpy.uint8((247, 252, 245)),
                2: numpy.uint8((219, 241, 213)),
                3: numpy.uint8((173, 222, 167)),
                4: numpy.uint8((116, 196, 118)),
                5: numpy.uint8((55, 160, 85)),
                6: numpy.uint8((11, 119, 52)),
                7: numpy.uint8((0, 68, 27))}
    NO_HOLDINGS_COLOR = numpy.uint8((36, 36, 36))
    WATER_COLOR = numpy.uint8((51, 67, 85))

    def num_holdings(rgb):
        rgb_t = tuple(rgb)
        try:
            return rgb_map[rgb_t]
        except KeyError:
            province = Title.rgb_id_map.get(rgb_t, 0)
            if province == 0 or province in Title.waters:
                color = WATER_COLOR
            else:
                try:
                    title = Title.id_title_map[province]
                except KeyError:
                    color = NO_HOLDINGS_COLOR
                else:
                    color = COLORMAP[title.max_holdings]
            rgb_map[rgb_t] = color
            return color

    rgb_map = {}
    in_image = PIL.Image.open(str(in_path))
    # width_px, height_px = in_image.size
    # dpi = 96
    # size = (width_px / dpi, height_px / 96)
    # figure = matplotlib.pyplot.figure(figsize=size, dpi=dpi, frameon=False)
    # plot_axes = figure.add_axes([0, 0, 1, 1])
    # plot_axes.axis('off')
    array = numpy.array(in_image)
    array = numpy.apply_along_axis(num_holdings, 2, array)
    out_image = PIL.Image.fromarray(array)
    # colormap = matplotlib.cm.get_cmap('Greens', 7)
    # colormap.set_under('#242424')
    # colormap.set_over('#334355')
    # norm = matplotlib.colors.Normalize(0.5, 7.5)
    # colored_image = plot_axes.matshow(array, cmap=colormap, norm=norm)
    borders = PIL.Image.open(str(BORDERS_PATH))
    out_image.paste(borders, mask=borders)
    # # plot_axes.imshow(borders_image)
    out_image.save(str(out_path))

# pre: parse_map_provinces
def process_map_adjacencies_row(row):
    try:
        from_province, to_province = map(int, row[:2])
    except ValueError:
        return
    Title.province_graph.add_edge(from_province, to_province)

# TODO: write secondary table for british duchies in 769
def format_duchies_table():
    def rows():
        starts = [datetime.date(769, 1, 1), datetime.date(867, 1, 1),
                  datetime.date(1066, 9, 15)]
        start_1066 = starts[2]
        for duchy in Title.duchies():
            if not duchy.vassal_intvls:
                # skip duchy-level titles with no de jure territory ever
                continue
            row = collections.OrderedDict()
            row['Duchy'] = duchy.name
            kingdom = duchy.liege(start_1066)
            row['Kingdom'] = kingdom.name if kingdom else '-'
            try:
                empire = kingdom.liege(start_1066)
                row['Empire'] = empire.name if empire else '-'
            except AttributeError:
                row['Empire'] = '-'
            start_holdings = [sum(1 for c in duchy.vassals(s) for b in
                                  c.built_holdings(s)) for s in starts]
            for datum, start in zip(start_holdings, starts):
                row['{} holdings'.format(start.year)] = datum
            counties = list(duchy.vassals(start_1066))
            max_holdings = sum(c.max_holdings for c in counties)
            row['Max holdings'] = max_holdings
            coastal_holdings = sum(c.max_holdings for c in counties if
                                   c.coastal())
            row['Coastal holdings'] = coastal_holdings
            row['Counties'] = len(counties)
            largest_county = max((c.max_holdings for c in counties), default=0)
            row['Largest county'] = largest_county
            coasts = sum(county.coastal() for county in counties)
            row['Coasts'] = coasts
            row['Other names'] = ', '.join(duchy.other_names)
            row['ID'] = duchy.codename
            yield row

    sorted_rows = sorted(rows(), key=operator.itemgetter('Empire', 'Kingdom', 
                                                         'Duchy'))
    return tabulate.tabulate(sorted_rows, headers='keys', tablefmt='mediawiki')

def format_counties_table():
    def rows():
        starts = [datetime.date(769, 1, 1), datetime.date(867, 1, 1),
                  datetime.date(1066, 9, 15)]
        start_1066 = starts[2]
        for county in Title.counties():
            row = collections.OrderedDict()
            row['ID'] = county.id
            row['County'] = county.name
            row['Duchy'] = '-'
            row['Kingdom'] = '-'
            row['Empire'] = '-'
            duchy = county.liege(start_1066)
            if duchy:
                row['Duchy'] = duchy.name
                kingdom = duchy.liege(start_1066)
                if kingdom:
                    row['Kingdom'] = kingdom.name
                    empire = kingdom.liege(start_1066)
                    if empire:
                        row['Empire'] = empire.name
            cultures = [(when, county.culture(when)) for when in starts]
            for start, datum in cultures:
                row['{} culture'.format(start.year)] = datum
            religions = [(when, county.religion(when)) for when in starts]
            for start, datum in religions:
                row['{} religion'.format(start.year)] = datum
            start_holdings = [
                (s, sum(1 for b in county.built_holdings(s))) for s in starts]
            for start, datum in start_holdings:
                row['{} holdings'.format(start.year)] = datum
            row['Max holdings'] = county.max_holdings
            row['Coastal'] = 'yes' if county.coastal() else 'no'
            row['Other names'] = ', '.join(county.other_names)
            row['Title ID'] = county.codename
            yield row

    sorted_rows = sorted(rows(), key=operator.itemgetter('ID'))
    return tabulate.tabulate(sorted_rows, headers='keys', tablefmt='mediawiki')

def duchy_stats():
    start_1066 = datetime.date(1066, 9, 15)
    counties = [sum(1 for x in d.vassals(start_1066)) for d in Title.duchies()]
    counties = [x for x in counties if x > 0]
    print('count: {}'.format(len(counties)))
    mean = statistics.mean(counties)
    median = statistics.median(counties)
    print('mean: {}'.format(mean))
    print('median: {}'.format(median))

def format_other_provs_table():
    def rows():    
        # dunno why broken , temp fix
        category = dict.fromkeys(range(1, Title.max_provinces), 'terra incognita')
        # category = dict.fromkeys(range(1, Title.max_provinces), 'unused')
        for province in Title.id_title_map:
            del category[province]
        for province in Title.waters:
            category[province] = 'terminal lake'
        for province in Title.rivers:
            category[province] = 'river'
        for province in Title.seas:
            category[province] = 'ocean'
        for prov, categ in list(category.items()):
            # dunno why this is broken
            if categ == 'unused' and prov in Title.province_graph:
                if Title.province_graph[prov]:
                    category[prov] == 'terra incognita'
                else:
                    category[prov] == 'disconnected terra incognita'
        for prov, categ in sorted(category.items()):
            row = collections.OrderedDict()
            row['ID'] = prov
            name = localisation.get('PROV{}'.format(prov),
                                    Title.id_name_map[prov])
            row['Name'] = name
            row['Type'] = categ
            yield row

    sorted_rows = sorted(rows(), key=operator.itemgetter('ID'))
    return tabulate.tabulate(sorted_rows, headers='keys', tablefmt='mediawiki')

# def color_kingdoms():
#     when = datetime.date(1066, 9, 15)
#     for u in Title.province_graph:
#         try:
#             k_u = Title.id_title_map[u].liege(when).liege(when)
#         except KeyError:
#             continue
#         e_u = k_u.liege(when)
#         if e_u.codename not in ['e_scandinavia', 'e_persia', 'e_arabia',
#                                 'e_abyssinia', 'e_britannia', 'e_mali',
#                                 'e_rajastan', 'e_bengal', 'e_deccan']:
#             Title.kingdom_graph.add_node(k_u.codename, color=0,
#                                          weight=len(list(k_u.vassals(when))))
#     for u, v in Title.province_graph.edges_iter():
#         try:
#             k_u = Title.id_title_map[u].liege(when).liege(when)
#             k_v = Title.id_title_map[v].liege(when).liege(when)
#         except KeyError:
#             continue
#         if (k_u is not k_v and k_u.codename in Title.kingdom_graph and
#             k_v.codename in Title.kingdom_graph):
#             Title.kingdom_graph.add_edge(k_u.codename, k_v.codename)
#     for u in Title.kingdom_graph:
#         adjacent_colors = set()
#         for v in Title.kingdom_graph[u]:
#             adjacent_colors.add(Title.kingdom_graph.node[v]['color'])
#         color = 1
#         while color in adjacent_colors:
#             color += 1
#         Title.kingdom_graph.node[u]['color'] = color
#         print(color, u)


# TODO: refactor stuff
def main():
    csv.register_dialect('ckii', delimiter=';', quoting=csv.QUOTE_NONE)
    titles_txts = parse_files('history/titles/*.txt')
    provinces_txts = parse_files('history/provinces/*.txt')
    landed_titles_txts = parse_files('common/landed_titles/*.txt')
    cultures_txts = parse_files('common/cultures/*.txt')
    parse_csvs(sorted(CKII_DIR.glob('localisation/*.csv')),
               process_localisation_row)
    process_cultures(cultures_txts)
    process_landed_titles(landed_titles_txts)
    process_provinces(provinces_txts)
    process_titles(titles_txts)
    default_map = parse_file(CKII_DIR / 'map/default.map')
    map_definitions, map_provinces, map_adjacencies = (
        process_default_map(default_map))
    parse_csv(map_definitions, process_map_definitions_row)
    parse_map_provinces(map_provinces)
    parse_csv(map_adjacencies, process_map_adjacencies_row)

    # duchy_stats()
    # output = format_duchies_table()

    # output = format_counties_table()

    output = format_other_provs_table()

    output = re.sub(r' {2,}', ' ', output)
    with OUTPUT_FILE.open('w') as f:
        f.write(output)

    # color_kingdoms()

    # generate_holding_map(map_provinces, pathlib.Path(
    #     'C:/Users/Nicholas/Pictures/CKII/max_holdings.png'))

# def parse_map_test():
#     Title.province_graph = networkx.Graph()
#     parse_map_provinces(CKII_DIR / 'map/provinces_test.bmp')

if __name__ == '__main__':
    main()
