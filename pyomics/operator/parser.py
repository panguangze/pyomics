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
            print(variable, tp)
            if tp == "local":
                self._locals.update(variable)
            if tp == "global":
                self._globals.update(variable)
        return __wrapper__

    def parse(self, content, globs, locs):
        exec(content, globs, locs)
        print(self._locals)
        print(self._globals)
        return self._locals, self._globals


# def parser(content, globs, locs):
#     # run parser
#     print("this is content: ", content)
#     parser_model = ParserModel()
#     globs.update({"__parser__": parser_model})
#     exec(content, globs, locs)
#     # get information
#     # print("this is locals")
#     # for k1, v1 in locals().items():
#     #     print(k1, v1)
#     # reg = locals()["__register__"]
#     return parser_model._locals, parser_model._globals
