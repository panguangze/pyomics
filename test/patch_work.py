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

        inputs = {
            '-sd': a.output('Patchwork_Chrom_Bcf_Dir'),
        }
        b = submit_module('DOAP_Patchwork_2_MergeBcf', inputs, params)
        print("patch work 2:  %s started" % sample)

        vcfs.append(b.output('Patchwork_Sample_Vcf'))
        print("vcfs: %s" % vcfs)

    inputs = {
        '-bams': [csv_data[patient]['N1'], csv_data[patient]['T1']],
        '-vcfs': vcfs
    }
    params = {
        '-tumor': 'T1',
        '-normal': 'N1',
        '-patient': 'patient1',
    }
    c = submit_module('DOAP_Patchwork_3_Plot', inputs, params)
    print("patch work 3:  %s started" % patient)

    inputs = {
        '-i': c.output('Patchwork_Plot_Dir')
    }

    params = {
        '-cn2': 0.8,
        '-delta': 0.2,
        '-het': 0.3,
        '-hom': 0.7,
        '-patient': 'patient1',
    }
    d = submit_module('DOAP_Patchwork_4_PlotCopyNumber', inputs, params)
    print("patch work 4:  %s started" % patient)


runtime.end()
