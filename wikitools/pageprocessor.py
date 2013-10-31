#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

import sys
import os
import re
import argparse
import bz2
import logging
import lxml.etree

from functools import partial

from functional import compose

from exceptions import DropPage, AbortProcess
from wikitools.importer import import_function

Log = logging.getLogger(os.path.basename(__file__)
                        if __name__ == "__main__"
                        else __name__)

def configure_logging(args):
    logging_config = {
        'level': getattr(logging, args.loglevel.upper())
    }
    if args.log == '-':
        logging_config['stream'] = sys.stdout
    else:
        logging_config['filename'] = args.log
    logging.basicConfig(**logging_config)

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

def main(archive_path, proc, ignore_exceptions=False):
    fil = bz2.BZ2File(archive_path, 'rU')

    try:
        try:
            for (ix, raw_page_bytes) in enumerate(generate_pages(fil)):
                page_dom = lxml.etree.fromstring(raw_page_bytes)
                try:
                    page_dom = apply(proc, [page_dom])
                except DropPage as e:
                    Log.info(unicode(e))
                except AbortProcess as e:
                    raise
                except Exception as e:
                    if ignore_exceptions == True:
                        Log.error(u"Uncaught exception: {e}".format(e=unicode(e)))
                        Log.error(raw_page_bytes)
                    else:
                        raise

        except lxml.etree.XMLSyntaxError as e:
            logging.warn(u"Could not parse page {ix} because {e}".format(ix=ix, e=unicode(e)))
            logging.warn(raw_page_bytes)
    except KeyboardInterrupt:
        print("Stopped by CTRL-C", file=sys.stderr)

    except AbortProcess as e:
        print("Aborted by user function:", unicode(e), file=sys.stderr)

def compose_many(first, *rest):
    return reduce(compose, rest, first)

def printproc(page):
    print(page)
    return page

def interleave_debug_calls(funclist):
    newlist = []
    def _dbg(funcname, page_dom):
        if funcname is None:
            print("Initial page DOM:", file=sys.stderr)
        else:
            print("Page DOM after calling", funcname, ":", file=sys.stderr)
        print(lxml.etree.tostring(page_dom))
        return page_dom

    for f in funclist:
        newlist.append(partial(_dbg, f.__name__))
        newlist.append(f)

    newlist.append(partial(_dbg, None))
    return newlist

def import_and_bind(s):
    match = re.compile(ur"^([_a-z0-9]+(?:\.[a-z0-9_]+)*)(\[.*\])?$", re.I).match(s)
    if match is None:
        raise ImportError(s)
    else:
        pkg_mod_func = match.group(1)
        func = import_function(pkg_mod_func)
        args_str = match.group(2)
        if args_str is not None:
            args = eval(args_str)
            func = partial(func, *args)
        return func

def compose_proc(args):
    procs = [(pkg_mod_func, import_and_bind(pkg_mod_func))
             for pkg_mod_func in args.pkg_mod_func]
    broken = [pkg_mod_func
              for (pkg_mod_func, func) in procs
              if func is None]
    if len(broken) > 0:
        for pkg_mod_func in broken:
            print("Could not import", pkg_mod_func, file=sys.stderr)
        sys.exit(1)
    funclist = [func for (_, func) in procs]
    if args.debug_composition == True:
        funclist = interleave_debug_calls(funclist)
    return compose_many(*funclist)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pass each page to a given function.")
    parser.add_argument('archive_path', metavar='wikipedia_archive', action='store',
                        help='Path to the .xml.bz2 Wikipedia archive.')
    parser.add_argument('pkg_mod_func', action='store', nargs='+',
                        help='Function(s) to pass each page to, e.g. wikitools.examples.print_page'),
    parser.add_argument('--debug-composition', action='store_true',
                        default=False, dest='debug_composition',
                        help='Dump the document after each function.'),
    parser.add_argument('--continue-on-error', action='store_true',
                        default=False, dest='continue_on_error',
                        help='Continue when an exception goes uncaught.'),
    parser.add_argument('--log', metavar='FILE', dest='log', default='-',
                        help='Where to write the log file.'),
    parser.add_argument('--loglevel', metavar='LEVEL', type=str,
                        help='Logging level (default: info)',
                        default='info',
                        choices=('debug', 'info', 'warning',
                                 'error', 'critical'))
    args = parser.parse_args()
    configure_logging(args)

    if not os.path.exists(args.archive_path):
        print("No such path", args.archive_path)
        sys.exit(1)

    proc = compose_proc(args)

    main(args.archive_path,
         proc,
         ignore_exceptions=args.continue_on_error)

