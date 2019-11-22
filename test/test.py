from pyomics.core import runtime
from pyomics.core.shortcuts import *
from pyomics.core import visualization

runtime.begin()

csv_data = [1, 2, 3]

all_b = []
for sample in csv_data:
    inputs = {
        '-i1': sample
    }
    params = {
        '-p1': 8
    }
    a = submit_module('ModuleA', inputs, params)

    inputs = {
        '-i1': a.output('out1')
    }
    b = submit_module('ModuleB', inputs, {})
    all_b.append(b)

    # runtime.wait_for(b)

c = submit_module('ModuleC', {str(idx): b.output('out') for idx, b in enumerate(all_b)}, {})
runtime.wait_for(c)

ret = 0
while ret < 3:
    d = submit_module_and_wait('ModuleD', {}, {})
    ret += 1
    print("ret is %d" % ret)

runtime.end()


visualization.visualize("", files=)