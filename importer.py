from __future__ import print_function

import os
import sys
import imp

__all__ = ['import_function']

def import_function(pkgmodfunc):
    steps = pkgmodfunc.split('.')
    if len(steps) in (0, 1):
        return None
    elif len(steps) == 2:
        path = '.'
        (modname, funcname) = steps
        pkgmod = modname
    else:
        funcname = steps.pop()
        pkgmod = '.'.join(steps)
        modname = steps.pop()
        path = os.path.join(*steps)

    if not imp.lock_held():
        imp.acquire_lock()

    try:
        (file, filename, (suffix, mode, type)) = imp.find_module(modname, [path])
        module = imp.load_module(modname, file, filename, (suffix, mode, type))
        return getattr(module, funcname, None)
    finally:
        imp.release_lock()

if __name__ == "__main__":
    print(repr(import_function(sys.argv[1])))
