import asyncio
import datetime
import os
from pyomics.data import module, models
from pyomics.utils.logger import get_logger
from pyomics.core import project as _project
from pyomics.core.exceptions import ModuleInputsNotComplete, ModuleParametersNotComplete, TaskSubmissionFailed
from pyomics.backend import fs_tool
from pyomics.conf import config
from .task import Task
from pyomics.data.output_controller import OutputController
from .pending_output import PendingOutput


logger = get_logger('module_task')


class ModuleTask(Task):
    def __init__(self, module_name, inputs, params, depends_on=[], id=None):
        super().__init__(depends_on, id)
        self.module = module.get_module(module_name)
        self.inputs = inputs
        self.params = params
        self.root_dir = ''
        self._add_input_dependencies()
        logger.debug("Created task %s with dependencies: %s" % (self, self.dependencies))
        self._create_model()
        self.output = OutputController(self)

    @models.model_operation
    def submit(self, project=_project.default_project):
        super().submit(project)
        self.model.project = project.model
        self.model.save()
        self.root_dir = os.path.join(self.project.root_dir, self.module.name, self.id)
        return self

    def _add_input_dependencies(self):
        """Add dependencies from task's input."""
        for k, v in self.inputs.items():
            if isinstance(v, PendingOutput):
                self.add_dependency(v.task)
            elif type(v) is list:
                for sub_v in v:
                    if isinstance(sub_v, PendingOutput):
                        self.add_dependency(sub_v.task)

    def _check_inputs(self):
        for key, m_input in self.module.inputs.items():
            if m_input['required'] and m_input['prefix'] not in self.inputs:
                raise ModuleInputsNotComplete('Missing input %s in module %s' % (m_input['prefix'], self))
        logger.verbose("Input check passed: %s" % self)

    def _check_parameters(self):
        for key, m_param in self.module.parameters.items():
            if m_param['required'] and not m_param['default'] and m_param['prefix'] not in self.params:
                raise ModuleParametersNotComplete('Missing parameter %s in module %s' % (m_param['prefix'], self))
        logger.verbose("Parameter check passed: %s" % self)

    @models.model_operation
    def _create_model(self):
        self.model = models.Task()
        self.model.name = self.id
        self.model.created_at = datetime.datetime.now()
        self.model.task_type = 'N'
        self.model.module_label = self.module.name
        self.model.module_version = self.module.version
        self.model.save()

    async def _submit_and_wait_until_finished(self):
        """Submit to FlowSmart and block until task finished."""
        fs_task_json = fs_tool.task_json(self)
        logger.debug("Submitting Task %s [%s]" % (self, self.id))
        logger.verbose("FS json: %s" % fs_task_json)
        (succeeded, message) = fs_tool.task_submit(self,fs_task_json)
        if not succeeded:
            raise TaskSubmissionFailed(message)
        # Run loop
        status = Task.READY
        while status == Task.READY or status == Task.RUNNING:
            await asyncio.sleep(10)
            status = fs_tool.task_status(self)
            self.status = status
            logger.verbose("Task %s [%s] status %s" % (self, self.id, self.get_status_display()))

    async def exec(self):
        self._check_inputs()
        self._check_parameters()
        if config.DEBUG_OPTIONS.get('FAKE_FLOWSMART'):
            from random import randrange
            r = config.DEBUG_OPTIONS.get('FAKE_FLOWSMART_RUN_DELAY', (1, 5))
            await asyncio.sleep(randrange(r[0], r[1]))
            self.status = Task.FINISHED
        else:
            await self._submit_and_wait_until_finished()
        self.output.find_output()

    @models.model_operation
    def finish(self):
        self.model.finished_at = datetime.datetime.now()
        self.model.save()

    def __str__(self):
        return "<%s>" % self.module.name

    __repr__ = __str__
