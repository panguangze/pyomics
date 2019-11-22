import sys
import os
import json


def generate_report(category_analysis_list, report_path):
    data = {'categories': category_analysis_list}
    with open(report_path, 'w') as report_file:
        json.dump(data, report_file)
    return 0

'''
report(
  [
    category('name',
      [
        analysis('name',
          visualization('name',
            [
              data('filekey', 'url')
            ]
          )
        )
      ]
    )
  ]
)
'''

def write_report(categories, filepath=None):
  if not filepath:
    filepath = os.path.join(sys.argv[3], ".report.json")
  print("report json path=%s" % filepath)
  report = {'categories': categories}
  with open(filepath, 'w') as report_json:
    json.dump(report, report_json)
  return 0

def category(name, analyses=[]):
  return {'name': name, 'analyses': analyses}

def analysis(name, visualization):
  return {'name': name, 'visualization': visualization}

def visualization(name, datum=[]):
  return {'name': name, 'datum': datum}

def data(fileKey, file_url):
  # 'fileKey' is case-sensitive
  return {'fileKey': fileKey, 'url': file_url}
