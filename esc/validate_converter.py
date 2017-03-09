#!/usr/bin/env python3

import re
from ck2parser import vanilladir, rootpath, SimpleParser, is_codename
from print_time import print_time


@print_time
def main():
    ck2root = vanilladir
    eu4root = ck2root / '../Europa Universalis IV'
    parser = SimpleParser()
    # parser.moddirs.append(rootpath / 'SWMH-BETA/SWMH')
    ck2titles = set()
    for _, tree in parser.parse_files('common/landed_titles/*'):
        dfs = list(tree)
        while dfs:
            n, v = dfs.pop()
            if is_codename(n.val):
                ck2titles.add(n.val)
                dfs.extend(v)
    eu4provhistories = {}
    for path in (eu4root / 'history/provinces').iterdir():
        num = re.match(r'\d+', path.stem).group()
        eu4provhistories[num] = path.stem
    eu4taghistories = {}
    for path in (eu4root / 'history/countries').iterdir():
        eu4taghistories[path.stem[:3]] = path.stem
    bad_ck2_id_prov = set()
    bad_eu4_id_prov = set()
    bad_filename_prov = set()
    with open('province_table.csv', encoding='cp1252') as f:
        for line in f:
            try:
                ck2title, eu4id, filename, *_ = line.split(';')
            except ValueError:
                continue
            if any('#' in x for x in [ck2title, eu4id, filename]):
                continue
            if ck2title not in ck2titles:
                bad_ck2_id_prov.add(ck2title)
            if eu4id not in eu4provhistories:
                bad_eu4_id_prov.add(eu4id)
            elif filename != eu4provhistories[eu4id]:
                bad_filename_prov.add(filename)
    bad_ck2_id_tag = set()
    bad_eu4_tag_tag = set()
    bad_eu4_file_tag = set()
    with open('nation_table.csv', encoding='cp1252') as f:
        for line in f:
            try:
                ck2title, eu4tag, eu4file, *_ = line.split(';')
            except ValueError:
                continue
            if any('#' in x for x in [ck2title, eu4tag, eu4file]):
                continue
            if ck2title not in ck2titles:
                bad_ck2_id_tag.add(ck2title)
            if eu4tag not in eu4taghistories:
                bad_eu4_tag_tag.add(eu4tag)
            elif eu4tag + ' - ' + eu4file != eu4taghistories[eu4tag]:
                bad_eu4_file_tag.add(eu4file)
    ### ERRORS WITH VCF AND SWMH:
    # bad_ck2_id_prov -= {
    #     'b_kathmandu', 'c_acalapura', 'c_aj_bogd', 'c_aksu', 'c_al_aqabah', 'c_al_habbariyah', 'c_al_mafraq',
    #     'c_alampur', 'c_alodia', 'c_altay', 'c_amaravati', 'c_anxi', 'c_aral', 'c_armail', 'c_asayita', 'c_avhaz',
    #     'c_balkonda', 'c_bam', 'c_bamiyan', 'c_banavasi', 'c_bandhugadha', 'c_barasuru', 'c_baygal', 'c_bidar',
    #     'c_bikrampur', 'c_birjand', 'c_bost', 'c_cakrakuta', 'c_canda', 'c_candradvipa', 'c_chach', 'c_chagai',
    #     'c_charkliq', 'c_chauragarh', 'c_cherchen', 'c_cholamandalam', 'c_chunar', 'c_chuy', 'c_cyrenaica', 'c_dailam',
    #     'c_dakhina_desa', 'c_damin_i_koh', 'c_damot', 'c_dashhowuz', 'c_devagiri', 'c_dimapur', 'c_dotawo',
    #     'c_dunhuang', 'c_dunkheger', 'c_dwarasamudra', 'c_farama', 'c_farrah', 'c_fars', 'c_fergana', 'c_gauda',
    #     'c_gaya', 'c_goa', 'c_goalpara', 'c_haruppeswara', 'c_hendjan', 'c_herat', 'c_honnore', 'c_idatarainadu',
    #     'c_ikh_bogd', 'c_ilam', 'c_ili', 'c_inder', 'c_irbid', 'c_ishim', 'c_jask', 'c_jaunpur', 'c_jharkand',
    #     'c_kahketi', 'c_kalat', 'c_kalinganagar', 'c_kalyani', 'c_kamarupanagara', 'c_kamatapur', 'c_kambampet',
    #     'c_kanara', 'c_kanchipuram', 'c_kangly', 'c_kara-kum', 'c_kara_khoja', 'c_kara_khorum', 'c_karashar',
    #     'c_karluk', 'c_karmanta', 'c_kataka', 'c_kazakh', 'c_ket', 'c_khangai', 'c_kherla', 'c_khijjingakota',
    #     'c_khinjali_mandala', 'c_khiva', 'c_khozistan', 'c_kimak', 'c_kipchak', 'c_kiranapura', 'c_kirghiz',
    #     'c_kodalaka_mandala', 'c_kolhapur', 'c_kollipake', 'c_kondana', 'c_kongu', 'c_konjikala', 'c_kosti',
    #     'c_kotivarsa', 'c_kotthasara', 'c_kudalasangama', 'c_kumara_mandala', 'c_kundina', 'c_kunduz', 'c_kurdistan',
    #     'c_kusinagara', 'c_kuwait', 'c_kyzyl', 'c_kyzylkum', 'c_ladistan', 'c_lakomelza', 'c_laksmanavati',
    #     'c_lappland', 'c_lattalura', 'c_loulan', 'c_luntai', 'c_lut', 'c_madhupur', 'c_madurai', 'c_magadha',
    #     'c_mahdia', 'c_mahoyadapuram', 'c_maldives', 'c_mallabhum', 'c_mandesh', 'c_manyakheta', 'c_manyapura',
    #     'c_massawa', 'c_maymana', 'c_medak', 'c_mesopotamia', 'c_midnapore', 'c_mithila', 'c_mudgagiri', 'c_munda',
    #     'c_muztau', 'c_nabadwipa', 'c_nagadipa', 'c_naldurg', 'c_nandagiri', 'c_nandapur', 'c_nanded', 'c_nandurbar',
    #     'c_napata', 'c_narim', 'c_nasikya', 'c_negev', 'c_nellore', 'c_nilagiri', 'c_nisibin', 'c_nobatia',
    #     'c_orangallu', 'c_oshrusana', 'c_otuken', 'c_pannagallu', 'c_parnakheta', 'c_penugonda', 'c_phiti',
    #     'c_pithapuram', 'c_potapi', 'c_pratishthana', 'c_pundravardhana', 'c_puri', 'c_qalqut', 'c_quzdar', 'c_qwivir',
    #     'c_racakonda', 'c_radha', 'c_rajamahendravaram', 'c_rajrappa', 'c_ramagiri', 'c_ratanpur', 'c_rayapura',
    #     'c_rohana', 'c_rothas', 'c_sagar', 'c_samarkand', 'c_samatata', 'c_sambalpur', 'c_saptagrama', 'c_saravan',
    #     'c_sasaram', 'c_simaramapura', 'c_srihatta', 'c_sripuri', 'c_srirangapatna', 'c_suvarnagram', 'c_suvarnapura',
    #     'c_swetaka_mandala', 'c_syr_darya', 'c_tabaristan', 'c_tagadur', 'c_talakad', 'c_tamralipti', 'c_taradavadi',
    #     'c_thana', 'c_tigrinya', 'c_tirunelveli', 'c_tis', 'c_tobol', 'c_trinkitat', 'c_tripuri', 'c_troyes',
    #     'c_tsagaannuur', 'c_tummana', 'c_tura', 'c_turkestan', 'c_uchangidurga', 'c_udayagiri', 'c_urgench',
    #     'c_urzhar', 'c_usturt', 'c_vairagara', 'c_varanasi', 'c_vatapi', 'c_vatsagulma', 'c_vemulavada', 'c_venadu',
    #     'c_vengipura', 'c_vijayapura', 'c_vijayawada', 'c_vilinus', 'c_viraja', 'c_vizagipatam', 'c_wag', 'c_yamalia',
    #     'c_yarkand', 'c_zahedan', 'c_zaranj', 'c_zeila', 'c_zhetysu', 'd_avanti', 'd_baluchistan', 'd_basra',
    #     'd_chera_nadu', 'd_chola_nadu', 'd_dahala', 'd_daksina_kosala', 'd_dandakaranya', 'd_devagiri', 'd_gangavadi',
    #     'd_gauda', 'd_gojjam', 'd_harer', 'd_hayya', 'd_jharkand', 'd_kalinga', 'd_kalyani', 'd_kamarupanagara',
    #     'd_kasi', 'd_konkana', 'd_lanka', 'd_lithuania', 'd_magadha', 'd_mazandaran', 'd_mosul', 'd_nadia',
    #     'd_nasikya', 'd_nulambavadi', 'd_pandya_nadu', 'd_para_lauhitya', 'd_racakonda', 'd_raichur_doab',
    #     'd_ratanpur', 'd_rattapadi', 'd_semien', 'd_shewa', 'd_sinhala', 'd_suhma', 'd_syria', 'd_tirabhukti',
    #     'd_tondai_nadu', 'd_tosali', 'd_udayagiri', 'd_vanga', 'd_varendra', 'd_vengi', 'd_vidharba', 'd_wag',
    #     'd_warangal'
    # }
    # bad_filename_prov -= {
    #     '101 - Liguria', '104 - Lombardia', '1066 - Altai Uriankhai', '1071 - Irtesh', '1110 - Agadir',
    #     '1137 - Wagadugu', '1208 - Haud', '1214 - Wollo', '1233 - Kargah', '1234 - Nubia', '131 - Zagorje15',
    #     '1318 - Szepes', '140 - Usora', '148 - Macedonia', '150 - Bulgaria', '151 - Thrace', '154 - Szepes',
    #     '161 - Wallachia', '1748 - Jaen', '1761 - Alzey', '181 - Valenciennes', '1849 - Hamah', '1853- Kozani',
    #     '1854 - Negev', '1882 - Annaba', '194 - Perigord', '1947 - Carnatic', '2031 - Morasandu', '2032 - Melenadu',
    #     '2033 - Savanur', '2049 - Khudra', '2051 - Bhavanagar', '2056 - Rewakantha', '2056 - Rewakanthra',
    #     '2057 - Bhilsa', '2085 - Tiruchirappalli', '2086 - Multan', '2089 - Chud', '2097 - Baghelkhand',
    #     '2214 - Gurgan', '2233 - Chabahar', '234 - Wessex', '2343 - Hadramawt', '2347 - Hufuf', '2407 - Pereyaslavl',
    #     '2408 - Lipesk', '2454 - Kef', '2458 - Hodna', '2463 - Kasadir', '2464 - Quarzazate', '2465 - Oujda',
    #     '2469 - Toubkhal', '2473 - Sousse', '252 - Highlands', '261 - Ruthenia', '266 - Bohemia', '268 - Bessarabia',
    #     '273 - Wenden', '2761 - Ankober', '2764 - Ausa', '2786 - Busaso', '2960 - Nowy Sacz', '2966 - Glogow',
    #     '2970 - Hradeco', '2975 - Cleves', '2989 - La Rioja', '2996 - Mecklenburg', '2997 - Tuchel', '30 - Viborg',
    #     '3002 - Visoki', '3003 - Euboia', '31 - Savolaks', '313 - Archangelsk', '314 - Ustyug', '316 - Bithynia',
    #     '317 - Bursa', '319 - Antalya', '32 - Keksholm', '322 - Anatolia', '325 - Kastamon', '328 - Sinope',
    #     '330 - Trebizon', '331', '331 - Erserum', '332 - Mus', '345 - Abda', '349 - Figuig', '350 - Laghouat',
    #     '351 - Aures', '356 - Cyrenaica', '357 - Dahrna', '360 - Nile', '362 - Delta', '363 - Diamientia',
    #     '372 - Ulster', '378 - Beirut', '379 - Judea', '381 - Hawran', '383 - Tabouk', '387 - Mocha', '392 - Nejd',
    #     '394 - Al-Qatif', '397 - Beni Yas', '406 - Karbala', '407 - Dayr Az Zor', '409 - Karbala', '41 - Ostpreussen',
    #     '4111 - Santoigne', '4113-Rovaniemi', '4114-Jokkmokk', '4116 - Odayev', '4118 - Deasmhumhain',
    #     '4119 - Sligeach', '4120 - Cilldara', '4121 - Ulaidh', '4123-Birkaland', '4124 - Karelia', '4127 - Torda',
    #     '4129 - Ust-Vym', '413 - Luristan', '415 - Sharizhor', '416 - Tabriz', '418 - Van', '419 - Armenia',
    #     '421 - Murgan', '428 - Hamadan', '429 - Fars', '430 - Laristan', '431 - Hormuz', '433 - Yadz',
    #     '434 - Kohistan', '435 - Zaranj', '436 - Khurasan', '445 - Marv', '46 - Mecklenburg', '462 - Georgia',
    #     '47 - Vorpommern', '472 - Zhetyru', '480 - Pegaya Orda', '50 - Brandenburg', '504 - Lower Sind',
    #     '505 - Upper Sind', '507', '507 - Punjab', '515 - Kathiawar', '516 - Gujarat', '518 - Mewar', '521 - Patan',
    #     '521 - Rajkot', '530 - Malvana', '531 - Kanara', '54 - Bremen', '542 - Telingana', '543 - Kosta',
    #     '544 - Ahmadnagara', '552 - Rajabara', '553 - Garjat', '558 - Bihar', '562 - Koch', '564 - Dacca',
    #     '57 - Hannover', '575 - Gwadar', '577 - Kalat', '59 - Meissen', '64 - Niederbayern', '67 - Franken',
    #     '69 - Konstanz', '740 - Malwa', '767 - Wystuc', '77 - Pfalz'
    # }
    with open('validation.txt', 'w') as f:
        print('### province_table.csv ###', file=f)
        if bad_ck2_id_prov:
            print('Invalid CK2 titles:\n\t', end='', file=f)
            print(*sorted(bad_ck2_id_prov), sep=' ', file=f)
        if bad_eu4_id_prov:
            print('Invalid EU4 IDs:\n\t', end='', file=f)
            print(*sorted(bad_eu4_id_prov), sep=' ', file=f)
        if bad_filename_prov:
            print('Invalid filenames:\n\t', end='', file=f)
            print(*sorted(bad_filename_prov), sep='\n\t', file=f)
        print('### nation_table.csv ###', file=f)
        if bad_ck2_id_tag:
            print('Invalid CK2 titles:\n\t', end='', file=f)
            print(*sorted(bad_ck2_id_tag), sep=' ', file=f)
        if bad_eu4_tag_tag:
            print('Invalid EU4 tags:\n\t', end='', file=f)
            print(*sorted(bad_eu4_tag_tag), sep=' ', file=f)
        if bad_eu4_file_tag:
            print('Invalid filenames:\n\t', end='', file=f)
            print(*sorted(bad_eu4_file_tag), sep='\n\t', file=f)



if __name__ == '__main__':
    main()
