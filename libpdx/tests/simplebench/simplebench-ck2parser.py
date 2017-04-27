#!/usr/bin/python3

from ck2parser import SimpleParser
from pathlib import Path

p = SimpleParser()
p.ignore_cache = True
p.parse_file(Path("test_input.txt"), errors='ignore')
