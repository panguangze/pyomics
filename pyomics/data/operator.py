import hashlib


class Operator:
    def __init__(self, op, op_type, op_name=None):
        if not self._is_valid(op_type, op_name):
            raise Exception("Invalid operator")
        self._type = op_type
        self._name = op_name if op_name != None else self._assign_name(op, op_type)
        self._op = op
        if self._type == "file":
            self._op = open(op).read()

    def __repr__(self):
        ret = "Operator name: {}\n".format(self._name)
        ret += "Operator type: {}\n".format(self._type)
        return ret

    def __str__(self):
        return self.__repr__()

    def _is_valid(self, op_type, op_name):
        valid_types = ["file", "code"]
        return op_type in valid_types

    def _assign_name(self, op, op_type):
        if op_type == "file":
            return op
        else:
            return hashlib.md5(op.encode("utf-8")).hexdigest()
