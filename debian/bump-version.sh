#!/bin/sh
# Bumps a single unpacked package's own minor version, in place.
# Usage: debian/bump-version.sh <unpacked-package-dir>
set -eu

dir="$1"
control="$dir/DEBIAN/control"

old="$(grep '^Version:' "$control" | awk '{print $2}')"
major="${old%.*}"
minor="${old#*.}"
new="$major.$((minor + 1))"

sed -i "s/^Version:.*/Version: $new/" "$control"

echo "Bumped $dir from $old to $new"
