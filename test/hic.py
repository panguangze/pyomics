import sys
print('Python %s on %s' % (sys.version, sys.platform))
sys.path.extend(['/home/platform/pyomics_for_rails'])

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

    inputs = {
        '-r': a.output('bam1'),
        '-m': a.output('bam2')
    }
    b = submit_module('DOAP_Hi-C_Sort', inputs)

    inputs = {
        '-i': b.output('sorted'),
    }
    c = submit_module('DOAP_Extract_Contacts', inputs)

    inputs = {
        '-i': c.output('contacts')
    }
    d = submit_module('DOAP_generate_contact_map', inputs)



runtime.end()


