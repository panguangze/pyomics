def guard_import():
    """
    Add additional guard for builtin `__import__`.
    This code should be prepended to each user script.
    """

    # Stash original import
    import builtins
    orig_import = builtins.__import__

    # a blacklist of disabled modules
    blacklist = ['os']

    def __import_guard__(name, globals=None, locals=None, fromlist=(), level=0):
        # Only guard imports from __main__.
        # Note that if global is None, the check will run by default. This might affect some third-party libs which use
        # bare `__import__`. A better way may be searching user's code for `__import__` calls before running.
        if not globals or globals['__name__'] == '__main__':
            # Only allow pyomics.core
            if name.startswith('pyomics') and not name.startswith('pyomics.core'):
                raise RuntimeError("You can only import from pyomics.core!")
            # Check blacklist
            for p in blacklist:
                if name.startswith(p):
                    raise RuntimeError("You are not allowed to import this package!")

        # Call original import
        return orig_import(name, globals, locals, fromlist, level)

    # Replace
    builtins.__import__ = __import_guard__


# Install the guard and delete itself
guard_import()
del locals()['guard_import']
