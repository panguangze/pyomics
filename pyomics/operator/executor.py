from pyomics.operator import builtins
from pyomics.operator.parser import Parser
from pyomics.data.operator import Operator
import re

class OperatorsExecutor:
    def __init__(self, env={}):
        self.__globals__ = {
            f: getattr(builtins, f) for f in dir(builtins) if not re.match(r"^_", f)
        }
        self.__locals__ = env
        self._ops = []
        self._registered = {}

    def add_operator(self, op, op_type="file", op_name=None):
        self._ops.append(Operator(op, op_type, op_name))

    def remove_operator(self, op):
        self._ops = filter(lambda x: x.name != op, self._ops)

    @property
    def operators(self):
        return self._ops

    def execute(self):
        for _ in self._ops:
            parser = Parser()
            loc, glob = parser.parse(_._op, self.__globals__, self.__locals__)
            self.__locals__.update(glob)
            self._registered.update({**loc, **glob})
        return self._registered
