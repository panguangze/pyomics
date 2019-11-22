class DataBaseOperationFailed(Exception):
    pass


class ModuleDoesNotExist(Exception):
    """The requested module does not exist"""
    pass


class DockerDoesNotExist(Exception):
    """The requested docker container does not exist"""
    pass


class ProjectDoesNotExist(Exception):
    """The requested project does not exist"""
    pass


class ModuleTaskDoesNotExist(Exception):
    """The requested module task does not exist"""
    pass


class ModuleInputsNotComplete(Exception):
    """The required module inputs are not completely provided"""
    pass


class ModuleOutputNotExist(Exception):
    """The requested output does not exist."""
    pass


class ModuleParametersNotComplete(Exception):
    """The required module parameters are not completely provided"""
    pass


class RuntimeNotReady(Exception):
    pass

class TaskSubmissionFailed(Exception):
    """The submission of task to FlowSmart failed"""
    pass
