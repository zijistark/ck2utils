#!/bin/bash
cd "${HOME}/Documents/Paradox Interactive/Crusader Kings II/mod"
[ -e modules ] && mv modules{,-backup}
mv modules{-alpha,}
trap "mv modules{,-alpha} ; [ -e modules-backup ] && mv modules{-backup,}" EXIT
date -I > modules/version.txt
py -2 ${REPO_ROOT}/HIP-tools/installer/main.py --in-place "$@"
