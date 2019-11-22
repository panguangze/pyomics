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
    a = submit_module('DOAP_Hi-C_alignment', inputs, params, id='alignment')

    @run_after(a)
    def change(a):
        # change output name
        a.output.rename('R1.bam', 'changed.bam')

        # create new folder
        a.output.create_dir('NEW')

        # create file
        a.output.create_file('NEW/new.txt', 'bam1')

        # delete folder
        a.output.remove('NEW', True)


    inputs = {
        '-r': a.output('bam1'),
        '-m': a.output('bam2')
    }
    b = submit_module('DOAP_Hi-C_sort', inputs, id='sort')




runtime.end()


