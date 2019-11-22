from pyomics.task.module_task import ModuleTask
from pyomics.task.complex_task import ComplexTask
from pyomics.task.task import run_after, run_before
from pyomics.data.data_manager import DataManager
from pyomics.core.project import default_project, Project


def submit_module(module, inputs, params={}, depends_on=[], id=None):
    return ModuleTask(module, inputs, params, depends_on, id).submit()


def submit_module_and_wait(module, inputs, params={}, depends_on=[], id=None):
    from pyomics.core.runtime import wait_for
    m = ModuleTask(module, inputs, params, depends_on, id).submit()
    wait_for(m)
    return m


def submit_complex_task(ctask, arguments=[], depends_on=[]):
    return ComplexTask(ctask, arguments, depends_on).submit()

