#!/usr/bin/env python3
"""
Build the book and corpus meta packages -- separate from bootstrap.py,
which only builds chapter packages.

Which chapter packages exist is discovered from sdist/*.deb filenames
(the same source of truth bootstrap.py uses). Each meta package just
Depends on its chapter packages, pinned to VERSION; it carries no payload
of its own.

Usage: debian/build-meta-packages.py [book]
  With no arguments, builds every book meta package plus the corpus meta
  package.
  With a book (e.g. 27), builds only that book's meta package.
"""
import argparse
import glob
import hashlib
import os
import shutil
import subprocess
import sys

import jinja2

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
DEBIAN = os.path.join(REPO, "debian")
TEMPLATES = os.path.join(DEBIAN, "templates")
BUILD_ROOT = os.path.join(REPO, "build")
SDIST = os.path.join(BUILD_ROOT, "sdist")
OUTDIR = os.path.join(BUILD_ROOT, "dist")
STAGING = os.path.join(BUILD_ROOT, "staging")
VERSION = "1.0"
MAINTAINER = "Reuben Institute <reubeninstitute@gmail.com>"

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATES),
    keep_trailing_newline=True,
)


def discover_books():
    """book -> sorted list of its chapter package names, from sdist/*.deb
    filenames."""
    books = {}
    for deb in glob.glob(os.path.join(SDIST, "audiobible-*-*_*.deb")):
        name = os.path.basename(deb)
        pkg = name.split("_", 1)[0]  # audiobible-<book>-<chapter>
        parts = pkg.split("-")
        if len(parts) != 3:
            continue  # skip meta packages like audiobible-01_...
        _, book, chapter = parts
        books.setdefault(book, []).append(pkg)
    for book in books:
        books[book].sort()
    return books


def write_depends_control(pkg_root, pkg, depends, description):
    debian_dir = os.path.join(pkg_root, "DEBIAN")
    os.makedirs(debian_dir, exist_ok=True)
    os.chmod(debian_dir, 0o755)

    depends_list = [f"{d} (= {VERSION})" for d in depends]
    rendered = JINJA_ENV.get_template("control-meta.j2").render(
        pkg=pkg,
        version=VERSION,
        maintainer=MAINTAINER,
        depends=depends_list,
        description=description,
    )
    control = os.path.join(debian_dir, "control")
    with open(control, "w") as fh:
        fh.write(rendered)
    os.chmod(control, 0o644)
    return debian_dir


def embed_scripts(debian_dir):
    for name in ("bump-version.sh", "fast-build.sh"):
        src = os.path.join(DEBIAN, name)
        dst = os.path.join(debian_dir, name)
        shutil.copy(src, dst)
        os.chmod(dst, 0o755)


def write_md5sums(pkg_root):
    debian_dir = os.path.join(pkg_root, "DEBIAN")
    lines = []
    for dirpath, _, files in os.walk(pkg_root):
        if "DEBIAN" in dirpath.split(os.sep):
            continue
        for f in sorted(files):
            path = os.path.join(dirpath, f)
            rel = os.path.relpath(path, pkg_root)
            with open(path, "rb") as fh:
                digest = hashlib.md5(fh.read()).hexdigest()
            lines.append(f"{digest}  {rel}\n")
    md5sums = os.path.join(debian_dir, "md5sums")
    with open(md5sums, "w") as fh:
        fh.writelines(sorted(lines))
    os.chmod(md5sums, 0o644)


def build_deb(pkg_root, pkg):
    """Pack pkg_root into dist/, then remove the staging dir -- it's
    scratch space, not needed once the .deb exists."""
    os.makedirs(OUTDIR, exist_ok=True)
    out = os.path.join(OUTDIR, f"{pkg}_{VERSION}_all.deb")
    env = dict(os.environ, TMPDIR=OUTDIR)
    subprocess.run(
        ["dpkg-deb", "-b", "-Zgzip", "-z1", pkg_root, out], check=True, env=env
    )
    shutil.rmtree(pkg_root)
    return out


def build_meta_package(pkg, depends, description):
    pkg_root = os.path.join(STAGING, pkg)
    if os.path.exists(pkg_root):
        shutil.rmtree(pkg_root)
    os.makedirs(pkg_root, exist_ok=True)
    os.chmod(pkg_root, 0o755)

    debian_dir = write_depends_control(pkg_root, pkg, depends, description)
    embed_scripts(debian_dir)
    write_md5sums(pkg_root)
    return build_deb(pkg_root, pkg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("book", nargs="?", help="e.g. 27 -- build only this book's meta package")
    args = parser.parse_args()

    if not os.path.isdir(SDIST):
        sys.exit(f"{SDIST} not found -- nothing to discover chapter packages from")

    books = discover_books()
    if not books:
        sys.exit("No chapter packages found in sdist/ -- nothing to build meta packages from.")

    if args.book:
        if args.book not in books:
            sys.exit(f"No chapters found for book={args.book}")
        books = {args.book: books[args.book]}

    for book in sorted(books):
        pkgs = books[book]
        out = build_meta_package(
            f"audiobible-{book}",
            pkgs,
            f"Complete audio for book {book}\n"
            f" Depends on every chapter package for book {book}, pinned to its\n"
            f" exact built version.",
        )
        print(f"built {out}")

    if args.book:
        print(f"\n1 book meta package built (corpus meta package skipped -- single book)")
        return

    all_chapter_pkgs = sorted(pkg for pkgs in books.values() for pkg in pkgs)
    out = build_meta_package(
        "audiobible",
        all_chapter_pkgs,
        "Complete audiobible corpus (original/cloned/english)\n"
        " Depends on every per-chapter package, pinned to its exact built\n"
        " version. Installing this pulls the entire corpus; a missing or\n"
        " stale chapter package makes this fail to install.",
    )
    print(f"built {out}")

    print(f"\n{len(books)} book meta packages, 1 corpus meta package")


if __name__ == "__main__":
    main()
