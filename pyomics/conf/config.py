DEBUG = False
DEBUG_OPTIONS = {}
DOAP_DB = 'postgresql://omics:WH#t%vx9D=_^h4ZB@localhost:5432/omics_platform_production'
PYOMICS_DB = 'mysql://omics:omics2017@localhost/pyomics'
DEFAULT_USER = 'test'
USER = None
DOAP_MEDIA_ROOT = '/disk2/media/'
FS_WRAPPER_PATH = '/home/platform/pyomics_for_rails/pyomics/backend/fs_wrapper.py'
ENV_PATH = '/home/platform/pyomics_for_rails'
LOG_PATH = '/home/platform/pyomics_for_rails/logs'

try:
    from .config_ex import *
except:
    pass
