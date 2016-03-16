#!/bin/sh

BUILD=/home/Nicholas/cpr-build
cd /home/Nicholas/CK2/CPRplus
mkdir -p $BUILD
rsync -a --del --exclude='*.rar' CPRplus* $BUILD && \
unrar x -idq -phip -y "CPRplus\gfx.rar" "`cygpath -w $BUILD/CPRplus`" && \
../HIP-tools/installer/shrinkwrap.py --modules-dir $BUILD
