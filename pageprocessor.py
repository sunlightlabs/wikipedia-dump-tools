from __future__ import division, print_function

import sys
import os
import argparse
import bz2
import lxml.etree

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
    if archive_path == '-':
        fil = bz2.BZ2File(sys.stdin)
    else:
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

def printproc(path):
    print(path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pass each page to a given function.")
    parser.add_argument('archive_path', metavar='WIKIPEDIA_ARCHIVE', action='store')
    parser.add_argument('proc', metavar='[PKG.]MOD.FUNC', action='store')
    args = parser.parse_args()

    if args.archive_path == '-':
        pass
    elif not os.path.exists(args.archive_path):
        print("No such path", args.archive_path)
        sys.exit(1)

    proc = import_function(args.proc)
    if proc is None:
        print("Could not import", args.proc)
        sys.exit(1)

    main(args.archive_path, proc)

