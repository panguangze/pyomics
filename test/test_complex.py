from pyomics.core import runtime
from pyomics.core.shortcuts import *

runtime.begin()


async def run_a(ctx, args):
    result = None
    threshold = args[0]
    ret = 0
    while ret < threshold:
        result = await ctx.submit_module_and_wait('ModuleA', {}, {})
        ret += 1
        print("A: ret is %d" % ret)
    ctx.set_result(result)


async def run_b(ctx, _):
    result = None
    ret = 0
    while ret < 4:
        result = await ctx.submit_module_and_wait('ModuleB', {}, {})
        ret += 1
        print("B: ret is %d" % ret)
    ctx.set_result(result)


a = submit_complex_task(run_a, [3])
b = submit_complex_task(run_b)

submit_module('ModuleC', {'a': a.output('x'), 'b': b.output('y')}, {})

runtime.end()
