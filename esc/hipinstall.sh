#!/bin/bash
cd ${HOME}/mod
[ -e modules ] && mv modules{,-backup}
mv modules{-alpha,}
trap "mv modules{,-alpha} ; [ -e modules-backup ] && mv modules{-backup,}" EXIT
date -I > modules/version.txt
${REPO_ROOT}/HIP-tools/installer/main.py --in-place "$@"
