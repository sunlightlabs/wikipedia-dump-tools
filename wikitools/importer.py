from __future__ import print_function

import os
import sys
import imp
from operator import isCallable

__all__ = ['import_function']

def import_function(pkgmodfunc):
    steps = pkgmodfunc.split('.')
    if len(steps) in (0, 1):
        return None
    funcname = steps.pop()

    if not imp.lock_held():
        imp.acquire_lock()

    path = None
    try:
        for step in steps:
            (fil, filename, (suffix, mode, typ)) = imp.find_module(step, path)
            module = imp.load_module(step, fil, filename, (suffix, mode, typ))
            if hasattr(module, '__path__'):
                path = module.__path__
            else:
                if not hasattr(module, funcname):
                    raise ImportError(pkgmodfunc)
                try:
                    return getattr(module, funcname)
                except AttributeError:
                    raise ImportError(pkgmodfunc)
    finally:
        imp.release_lock()

if __name__ == "__main__":
    print(repr(import_function(sys.argv[1])))
