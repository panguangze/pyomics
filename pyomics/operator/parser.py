from functools import wraps
from singleton_decorator import singleton


@singleton
class Parser:
    def __init__(self):
        self._locals = {}
        self._globals = {}

    def __call__(self, fn):
        @wraps(fn)
        def __wrapper__(*args, **kwargs):
            variable, tp = fn(*args, **kwargs)
            if tp == "local":
                self._locals.update(variable)
            if tp == "global":
                self._globals.update(variable)
        return __wrapper__

    def parse(self, content, globs, locs):
        exec(content, globs, locs)
        return self._locals, self._globals
