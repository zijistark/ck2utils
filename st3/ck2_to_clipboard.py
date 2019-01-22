#!/usr/bin/python3

import sys
import os
import subprocess
import localpaths

###

g_base_dir = localpaths.rootpath / 'ck2utils/st3'

###


def main():
	os.chdir(str(g_base_dir))
	subprocess.run(['./ck2/codenames.py', '--all'], check=True)
	subprocess.run('./print_syntax_vars.pl ck2/var/*.txt ck2/static/*.txt | clip', shell=True, check=True)
	return 0


###


if __name__ == '__main__':
	sys.exit(main())
