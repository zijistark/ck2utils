#!/bin/bash
cd /home/Nicholas/mod
date -I > modules/version.txt
/home/Nicholas/CK2/HIP-tools/installer/main.py --in-place "$@"
