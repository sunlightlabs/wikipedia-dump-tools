#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

import sys
import os
import argparse
import bz2
import logging
import lxml.etree

from operator import isCallable

from functional import compose

from util import progress
from exceptions import DropPage
from importer import import_function

Log = logging.getLogger(os.path.basename(__file__)
                        if __name__ == "__main__"
                        else __name__)

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

def main(archive_path, proc, progress_cb):
    fil = bz2.BZ2File(archive_path, 'rU')

    try:
        try:
            for (ix, raw_page_bytes) in enumerate(generate_pages(fil)):
                page_dom = lxml.etree.fromstring(raw_page_bytes)
                try:
                    apply(proc, [page_dom])
                except DropPage as e:
                    Log.info(unicode(e))
                if isCallable(progress_cb):
                    progress_cb(ix)
        except lxml.etree.XMLSyntaxError as e:
            print("Could not parse page", ix, str(e), ":")
            print(raw_page_bytes)
    except KeyboardInterrupt:
        pass

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
    parser.add_argument('--progress', action='store_true', default=False,
                        help='Display progress.')
    parser.add_argument('--loglevel', metavar='LEVEL', type=str,
                        help='Logging level (default: info)',
                        default='notice',
                        choices=('debug', 'info', 'warning',
                                 'error', 'critical'))
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

    progress_cb = progress if args.progress else None
    logging.basicConfig(level=getattr(logging, args.loglevel.upper()))
    main(args.archive_path, proc, progress_cb)

