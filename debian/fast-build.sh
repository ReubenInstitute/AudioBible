#!/bin/sh
# Rebuilds a single unpacked package directory straight into a .deb,
# bypassing debhelper/dh_* entirely (no Perl, no dpkg-buildpackage).
# Usage: debian/fast-build.sh <unpacked-package-dir> <output.deb>
set -eu

dir="$1"
out="$2"

dpkg-deb -b -Zgzip -z1 "$dir" "$out"
