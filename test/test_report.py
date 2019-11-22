import os
import sys
import argparse
from pyomics.core import runtime
from pyomics.core.shortcuts import *
from pyomics.core import report
print('Python %s on %s' % (sys.version, sys.platform))
sys.path.extend(['/home/platform/pyomics_for_rails'])

parser = argparse.ArgumentParser(description='Test Report')
parser.add_argument('-i', dest='input_fns')
args, unknown = parser.parse_known_args()

runtime.begin()

inputs = {
    '-i': args.input_fns
}

params = {
}

a = submit_module('SV_Linkage_Heatmap', inputs)

runtime.end()

categories = [
  report.category('sample_category',
    [
      report.analysis('sample_analysis',
        report.visualization('lingxi-heatmap',
          [
            report.data('lingxi-heatmap', a.output('matrix_fns'))
          ]
        )
      )
    ]
  )
]

report.write_report(categories)
