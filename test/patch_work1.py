from pyomics.core import runtime
from pyomics.core.shortcuts import *

runtime.begin()

csv_data = {
    'patient1': {
        'T1': '/disk2/media/user/xuchang/data/T1.bam',
        'N1': '/disk2/media/user/xuchang/data/N1.bam',
    }
}

for patient in csv_data:
    vcfs = []

    for sample in csv_data[patient]:
        inputs = {
            '-b': csv_data[patient][sample],
        }
        params = {
            '-sample': sample
        }
        print("patch work 1:  %s started" % sample)
        a = submit_module('DOAP_Patchwork_1_GetBcf', inputs, params)
runtime.end()
