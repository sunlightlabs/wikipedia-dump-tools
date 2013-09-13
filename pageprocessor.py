#!/usr/bin/env python

from __future__ import division, print_function

import sys
import os
import argparse
import bz2
import lxml.etree

from functional import compose

from util import progress
from importer import import_function

def generate_pages(fil):
    lines = []
    for ln in fil.xreadlines():
        clean_ln = ln.strip()
        if clean_ln == '<page>':
            lines = []
        lines.append(ln)
        if clean_ln == '</page>':
            page = ''.join(lines)
            yield page

def main(archive_path, proc):
    fil = bz2.BZ2File(archive_path, 'rU')

    for (ix, raw_page_bytes) in enumerate(generate_pages(fil)):
        try:
            page_dom = lxml.etree.fromstring(raw_page_bytes)
            apply(proc, [page_dom])
            progress(ix)
        except lxml.etree.XMLSyntaxError as e:
            print("Could not parse page", ix, str(e), ":")
            print(raw_page_bytes)

    # Signal end of pages
    apply(proc, [None])

def compose_many(first, *rest):
    return reduce(compose, rest, first)

def printproc(page):
    print(page)
    return page

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pass each page to a given function.")
    parser.add_argument('archive_path', metavar='wikipedia_archive', action='store',
                        help='Path to the .xml.bz2 Wikipedia archive.')
    parser.add_argument('pkg_mod_func', action='store', nargs='+',
                        help='Function(s) to pass each page to, e.g. wikitools.examples.print_page')
    args = parser.parse_args()

    if not os.path.exists(args.archive_path):
        print("No such path", args.archive_path)
        sys.exit(1)

    procs = [(pkg_mod_func, import_function(pkg_mod_func))
             for pkg_mod_func in args.pkg_mod_func]
    broken = [pkg_mod_func
              for (pkg_mod_func, func) in procs
              if func is None]
    if len(broken) > 0:
        for pkg_mod_func in broken:
            print("Could not import", pkg_mod_func)
        sys.exit(1)
    proc = compose_many(*[func for (_, func) in procs])

    main(args.archive_path, proc)

