#!/usr/bin/python3

import ck2parser
from print_time import print_time

@print_time
def main():
	parser = ck2parser.SimpleParser(ck2parser.rootpath / 'SWMH-BETA/SWMH')
	max_provinces = parser.parse_file('map/default.map')['max_provinces'].val

	outpath = parser.moddirs[0] / 'province_setup.txt'
	with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
		print('''\
# -*- ck2 -*-

log = "Dumping province data:"
''', file=f)

		for i in range(1, max_provinces):
			print('''\
if = {{ limit = {{ NOT = {{ {0} = {{ always = yes }} }} }} log = "<NULL> id={0}" }}
if = {{
	limit = {{ {0} = {{ always = yes }} }}
	{0} = {{
		if = {{ limit = {{ is_land = no }} log = "<NOT_LAND> id=[This.GetID], name='[This.GetName]', terrain=[This.EMFDebug_GetTerrain]" }}
		if = {{
			limit = {{ is_land = yes }}
			county = {{ save_event_target_as = c }}
			set_variable = {{ which = ms value = 0 }}
			if = {{ limit = {{ num_of_max_settlements = 1 }} set_variable = {{ which = ms value = 1 }} }}
			if = {{ limit = {{ num_of_max_settlements = 2 }} set_variable = {{ which = ms value = 2 }} }}
			if = {{ limit = {{ num_of_max_settlements = 3 }} set_variable = {{ which = ms value = 3 }} }}
			if = {{ limit = {{ num_of_max_settlements = 4 }} set_variable = {{ which = ms value = 4 }} }}
			if = {{ limit = {{ num_of_max_settlements = 5 }} set_variable = {{ which = ms value = 5 }} }}
			if = {{ limit = {{ num_of_max_settlements = 6 }} set_variable = {{ which = ms value = 6 }} }}
			if = {{ limit = {{ num_of_max_settlements = 7 }} set_variable = {{ which = ms value = 7 }} }}
			log = "<LAND> id=[This.GetID], name='[This.GetName]', title=[c.GetID], terrain=[This.EMFDebug_GetTerrain], max_settlements=[This.ms.GetValue]"
			clear_event_target = c
		}}
	}}
}}
'''.format(i), file=f)


if __name__ == '__main__':
    main()

