from .task import Task
from .pending_output import PendingOutput


class ComplexTask(Task):
    def __init__(self, fn=None, arguments=[], depends_on=[]):
        super().__init__(depends_on)
        self.status = Task.READY
        self.fn = fn
        self.arguments = arguments
        self.context = ComplexTaskContext(self)
        self.result = None

    def output(self, name):
        """
        Get (pending) output for a name. Used for inputs only.
        :param name: name for the output.
        :return: a PendingOutput object.
        """
        # TODO: return real output if task is finished?
        return PendingOutput(self, name)

    async def exec(self):
        await self.fn(self.context, self.arguments)

    def __str__(self):
        return "<ComplexTask%s>" % self.__hash__()

    __repr__ = __str__


class ComplexTaskContext:
    def __init__(self, ctask):
        self.task = ctask
        self.result = None

    def submit_module(self, module, inputs, params):
        from .module_task import ModuleTask
        return ModuleTask(module, inputs, params).submit()

    async def wait_for(self, module):
        runtime = self.task.project.runtime
        await runtime.block_until_modules([module])

    async def submit_module_and_wait(self, module, inputs, params):
        from .module_task import ModuleTask
        m = ModuleTask(module, inputs, params).submit()
        runtime = self.task.project.runtime
        await runtime.block_until_modules([m])
        return m

    def set_result(self, result):
        self.task.result = result
