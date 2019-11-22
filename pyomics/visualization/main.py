from .dovirus_local_api import *
from pyomics.data.models import Docker, model_operation
from pyomics.utils.logger import get_logger
import sys


logger = get_logger("vis")


class LazyObject:
    def __init__(self, getter=None):
        self.getter = getter
        self.cached = None

    def get(self):
        if self.cached is not None:
            return self.cached
        value = self.getter()
        self.cached = value
        return value


@model_operation
def __get_project():
    response = create_project(user='test', name='test')
    if response['status'] == 'error':
        raise RuntimeError(response['message'])

    pid = response['message']['id']
    logger.debug("Created project: %s" % pid)

    docker = Docker.get(name=sys.argv[1])
    docker.viz_id = pid
    docker.save()
    return pid


def __get_analyses():
    response = get_all_analyses()
    if response['status'] == 'error':
        raise RuntimeError(response['message'])
    return response['message']


PROJECT_ID = LazyObject(getter=__get_project)
ANALYSES_LIST = LazyObject(getter=__get_analyses)
LAST_ANALYSIS_ID = None


def get_analysis_by_name(name):
    """Find the first analysis with the same name"""
    return next((x for x in ANALYSES_LIST.get() if x['name'] == name), None)


def get_analyses():
    return ANALYSES_LIST.get()


def visualize(viz_name, files=None):
    """
    Submit file for a visualization
    :param viz_name: Name of the visualization
    :param files: A string if this visualization only requires one file key. Otherwise,
                  a dictionary with format { file_key: file_path }.
    """
    logger.debug("Visualize: %s, files= %s" % (viz_name, files))

    global LAST_ANALYSIS_ID
    project = PROJECT_ID.get()
    analysis = get_analysis_by_name(viz_name)

    # record last used analysis ID
    LAST_ANALYSIS_ID = analysis['id']

    # check files
    if files is None:
        files = {}
    elif isinstance(files, str):
        file_keys = analysis['file_requirements']
        if len(file_keys) != 1:
            raise RuntimeError("You can supply the path as string only when this visualization requires one file.")
        file_path = files
        files = {}
        files[file_keys[0]['name']] = file_path

    file_list = []
    for k, v in files.items():
        file_list.append({'path': v, 'file_key': k})

    logger.debug("Upload file: project= %s, analysis= %s, files= %s" % (project, analysis, file_list))
    response = upload_file(project=project, analysis=analysis['id'], files=file_list)
    logger.debug("File uploaded: %s" % response)


def get_url():
    if LAST_ANALYSIS_ID is None:
        raise RuntimeWarning("You are trying to access the visualization project without submitting any file.")
    response = get_analysis_url(project=PROJECT_ID.get(), analysis=LAST_ANALYSIS_ID)
    if response['status'] == 'error':
        raise RuntimeError(response['message'])
    return response['message']
