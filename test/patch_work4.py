import os
from pyomics.core import runtime, visualization
from pyomics.core.shortcuts import *

runtime.begin()



inputs = {
    '-i': '/disk2/media/user/xuchang/data/Patient_13'
}

params = {
    '-cn2': 1.03,
    '-delta': 0.385,
    '-het': 0.25,
    '-hom': 0.75,
    '-patient': 'Patient_13',
}
d = submit_module('DOAP_Patchwork_4_PlotCopyNumber', inputs, params)

runtime.end()

print(d.output.files)
visualization.visualize('CNV: Single Sample',
                        files=os.path.join(d.output.files['Patchwork_CNPlot_Dir'][0],
                                           'Patient_13',
                                           '13t_Copynumbers.csv'))
url = visualization.get_url()

print(url)
