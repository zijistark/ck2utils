import pathlib
import re
# import sys
import ck2parser

swmhpath = pathlib.Path('../SWMH-BETA/SWMH')
vanillapath = pathlib.Path(
    'C:/Program Files (x86)/Steam/SteamApps/common/Crusader Kings II')

def valid_codename(string):
    try:
        return re.match(r'[ekdcb]_', string)
    except TypeError:
        return False

cultures = [
    'norse', 'swedish', 'norwegian', 'danish', 'icelandic', 'frisian',
    'gothic', 'german', 'low_german', 'dutch', 'lombard', 'visigothic',
    'old_frankish', 'suebi', 'low_saxon', 'thuringian', 'franconian',
    'swabian', 'bavarian', 'low_frankish', 'english', 'saxon', 'old_saxon',
    'anglonorse', 'frankish', 'arpitan', 'norman', 'crusader_culture',
    'basque', 'andalusian_arabic', 'occitan', 'castillan', 'aragonese',
    'catalan', 'galician', 'leonese', 'portuguese', 'armenian', 'greek',
    'east_gothic', 'romanian', 'alan', 'caucasian_avar', 'sicilian_greek',
    'arberian', 'georgian', 'irish', 'scottish', 'cumbric', 'cornish', 'welsh',
    'breton', 'norsegaelic', 'finnish', 'karelian', 'vepsian', 'mari',
    'lappish', 'ugricbaltic', 'livonian', 'komi', 'khanty', 'samoyed',
    'mordvin', 'lettigallish', 'lithuanian', 'prussian', 'turkish', 'turkmen',
    'oghuz', 'uighur', 'mongol', 'cuman', 'pecheneg', 'khazar', 'bolghar',
    'avar', 'karluk', 'kasogi', 'kirghiz', 'bashkir', 'bedouin_arabic',
    'maghreb_arabic', 'levantine_arabic', 'egyptian_arabic', 'sicilian_arabic',
    'russian', 'pommeranian', 'polish', 'bohemian', 'moravian', 'karantanci',
    'croatian', 'serbian', 'bosnian', 'bulgarian', 'hungarian', 'szekely',
    'pahlavi', 'persian', 'tajik', 'daylamite', 'khalaj', 'soghdian',
    'khwarezmi', 'khorasani', 'kurdish', 'pashtun', 'baloch', 'qufs',
    'ethiopian', 'somali', 'afar', 'daju', 'beja', 'zaghawa', 'nubian',
    'manden', 'soninke', 'wolof', 'songhai', 'kanuri', 'hausa', 'berber',
    'sanhaja', 'tagelmust', 'masmuda', 'zanata', 'tuareg', 'ashkenazi',
    'sephardi', 'falashim', 'sardinian', 'sicilian', 'corsican',
    'central_italian', 'southern_italian', 'neapolitan', 'tuscan', 'ligurian',
    'langobardisch', 'italian', 'venetian', 'dalmatian', 'roman', 'nahuatl',
    'bengali', 'oriya', 'assamese', 'hindustani', 'gujurati', 'panjabi',
    'rajput', 'sindhi', 'marathi', 'sinhala', 'tamil', 'telugu', 'brahui',
    'kannada', 'khitan'
]
cultural_groups = [
    'north_germanic', 'central_germanic', 'west_germanic', 'latin', 'iberian',
    'byzantine', 'celtic', 'finno_ugric', 'baltic', 'altaic', 'arabic',
    'east_slavic', 'west_slavic', 'south_slavic', 'magyar', 'iranian',
    'east_african', 'west_african', 'north_african', 'israelite',
    'italian_group', 'mesoamerican', 'indo_aryan_group', 'dravidian_group',
    'sinic'
]

def recalc_cultures():
    global cultures
    global cultural_groups
    cultures = []
    cultural_groups = []
    for path in sorted(swmhpath.glob('common/cultures/*.txt')):
        with path.open(encoding='cp1252') as f:
            item = ck2parser.parse(f.read())
        cultures.extend(n2 for _, v in item for n2, v2 in v if isinstance(v2,
                        list))
        cultural_groups.extend(n for n, v in item)

religions = [
    'catholic', 'cathar', 'fraticelli', 'waldensian', 'lollard', 'orthodox',
    'miaphysite', 'monophysite', 'bogomilist', 'monothelite', 'iconoclast',
    'paulician', 'nestorian', 'messalian', 'sunni', 'zikri', 'yazidi', 'ibadi',
    'kharijite', 'shiite', 'druze', 'hurufi', 'pagan', 'norse_pagan_reformed',
    'norse_pagan', 'tengri_pagan_reformed', 'tengri_pagan',
    'baltic_pagan_reformed', 'baltic_pagan', 'finnish_pagan_reformed',
    'finnish_pagan', 'aztec_reformed', 'aztec', 'slavic_pagan_reformed',
    'slavic_pagan', 'west_african_pagan_reformed', 'west_african_pagan',
    'zun_pagan_reformed', 'zun_pagan', 'hellenic_pagan', 'zoroastrian',
    'mazdaki', 'manichean', 'jewish', 'samaritan', 'karaite', 'hindu',
    'buddhist', 'jain'
]
religious_groups = [
    'christian', 'muslim', 'pagan_group', 'zoroastrian_group', 'jewish_group',
    'indian_group'
]

def recalc_religions():
    global religions
    global religious_groups
    religions = []
    religious_groups = []
    for path in sorted(vanillapath.glob('common/religions/*.txt')):
        with path.open(encoding='cp1252') as f:
            item = ck2parser.parse(f.read())
        religions.extend(n2 for _, v in item for n2, v2 in v if isinstance(v2,
                        list) and n2 not in ['male_names', 'female_names'])
        religious_groups.extend(n for n, v in item)

interesting = [
    'title', 'title_female', 'foa', 'title_prefix', 'short_name', 'name_tier',
    'location_ruler_title', 'dynasty_title_names', 'male_names'
]

# print(repr('(' + '|'.join(interesting) + ')'))
# sys.exit()

results = set()

def exclude(n, v):
    return (valid_codename(n) or n in ['religion', 'culture', 'color',
        'color2', 'capital', 'coat_of_arms', 'allow', 'controls_religion',
        'dignity', 'creation_requires_capital', 'rebel', 'landless', 'primary',
        'pirate', 'tribe', 'mercenary_type', 'independent',
        'strength_growth_per_century', 'mercenary', 'caliphate', 'assimilate',
        'graphical_culture', 'holy_order', 'monthly_income', 'holy_site',
        'gain_effect', 'pentarchy', 'purple_born_heirs', 'duchy_revokation',
        'has_top_de_jure_capital', 'used_for_dynasty_names'] or
        n in cultures or n in religions or n in religious_groups or
        n in interesting)

count = 0

def recurse(v, n=None):
    global count
    for n1, v1 in v:
        if not valid_codename(n1):
            continue
        for n2, v2 in v1:
            count += 1
            if count % 1000 == 0:
                print(count, n2, n1, n, flush=True)
            #     sys.exit()
            # print(count, n2, n1, n, level)
            if not exclude(n2, v2):
                # try:
                results.add(ck2parser.to_string((n2, v2)))
                # print(ck2parser.to_string((n2, v2)))
                # except TypeError:
                    # print(n2, v2)
        recurse(v1, n1)
        # except ValueError:
        #     print(n1, v1)
        #     sys.exit()

recalc_religions()
# print(repr(religions))
# print(repr(religious_groups))
recalc_cultures()
# print(repr(cultures))
# print(repr(cultural_groups))
# raise SystemExit

for path in sorted(swmhpath.glob('common/landed_titles/*.txt')):
    print(path)
    with path.open(encoding='cp1252') as f:
        recurse(ck2parser.parse(f.read()))

print(len(results))

with open('out.txt', 'w') as f:
    print(sorted(results), sep='\n', file=f)
