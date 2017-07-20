#!/bin/bash
cd /home/Nicholas/mod
[ -e modules ] && mv modules{,-backup}
mv modules{-alpha,}
trap "mv modules{,-alpha} ; [ -e modules-backup ] && mv modules{-backup,}" EXIT
date -I > modules/version.txt
/home/Nicholas/CK2/HIP-tools/installer/main.py --in-place "$@"
