#!/bin/sh
# Build audiobible-web_<version>_all.deb
# Usage: packaging/deb/build.sh
set -eu

cd "$(dirname "$0")/../.."
REPO_ROOT="$(pwd)"
VERSION="0.$(git rev-list --count HEAD)"
sed -i "s/^Version: .*/Version: $VERSION/" packaging/deb/control-audiobible-web

WEB_DIR="$REPO_ROOT/debian-pkg-audiobible-web"
rm -rf "$WEB_DIR"
mkdir -p "$WEB_DIR/DEBIAN" "$WEB_DIR/usr/share/audiobible" "$WEB_DIR/usr/bin" \
	"$WEB_DIR/usr/share/doc/audiobible-web"
cp packaging/deb/control-audiobible-web "$WEB_DIR/DEBIAN/control"
cp audiobible-web.py "$WEB_DIR/usr/share/audiobible/audiobible-web.py"
chmod +x "$WEB_DIR/usr/share/audiobible/audiobible-web.py"
ln -s ../share/audiobible/audiobible-web.py "$WEB_DIR/usr/bin/audiobible-web"
cp GPL-3 "$WEB_DIR/usr/share/doc/audiobible-web/copyright"
dpkg-deb --build --root-owner-group "$WEB_DIR" "audiobible-web_${VERSION}_all.deb"
rm -rf "$WEB_DIR"
echo "Built audiobible-web_${VERSION}_all.deb"
