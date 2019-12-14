from pyomics.operator.parser import Parser
import inspect

def _retrieve_varname(v):
    for fi in reversed(inspect.stack()):
        names = [varname for varname, var_val in fi.frame.f_locals.items() if var_val is v]
        if len(names) > 0:
            return names[0]


@Parser()
def _register(v, vname, tp):
    vname = vname if vname != None else _retrieve_varname(v)
    print(vname)
    print(tp)
    return {vname: v}, tp


def register_global(v, vname=None):
    return _register(v, vname, "global")


def register_local(v, vname=None):
    return _register(v, vname, "local")


def register(v, vname=None, tp="local"):
    if tp == "global":
        return register_global(v, vname)
    elif tp == "local":
        return register_local(v, vname)
    else:
        raise Exception("Invalid variable type")
