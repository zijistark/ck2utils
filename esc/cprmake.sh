#!/bin/sh

BUILD=${HOME}/cpr-build
mkdir -p $BUILD
cd /c
rsync -a --del --exclude='*.rar' ${REPO_ROOT:3}/CPRplus2019/CPRplus* ${BUILD:3} && \
cd ${REPO_ROOT}
unrar x -idq -phip -y "CPRplus2019/CPRplus/gfx.rar" "$BUILD/CPRplus" && \
py HIP-tools/installer/shrinkwrap.py --modules-dir $BUILD
