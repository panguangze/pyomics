from pyomics.core import runtime
from pyomics.core.shortcuts import *

runtime.begin()

csv_data = [
    {
        'read': '/disk2/media/user/csz/data/Hi-C/R1.fq.gz',
        'mate': '/disk2/media/user/csz/data/Hi-C/R2.fq.gz'
    }
]

for sample in csv_data:
    inputs = {
        '-r': sample['read'],
        '-m': sample['mate']
    }
    params = {
        '-g': 'hg19'
    }
    a = submit_module('DOAP_Hi-C_alignment', inputs, params)

    b = submit_module('DOAP_Hi-C_sort', inputs)

    c = submit_module('DOAP_Extract_Contacts', inputs)

    d = submit_module('DOAP_Generate_Contact_Map', inputs)

runtime.end()


