from pyomics.core import project as _project, runtime_message
from pyomics.core.runtime_message import Message
from pyomics.utils.logger import get_logger
import shortuuid


logger = get_logger('task')


class Task:
    READY = 0
    RUNNING = 1
    FINISHED = 3
    ERROR = 4

    def __init__(self, dependency, id=None):
        self.dependencies = []
        self.before_hooks = []
        self.after_hooks = []
        self.status = Task.READY
        self.project = None
        self.id = id or shortuuid.uuid()

        deps = dependency
        # if dependency is not a list, make a list first
        if not isinstance(dependency, list):
            deps = [dependency]

        # loop all dependencies
        for dep in deps:
            self.add_dependency(dep)

    def add_dependency(self, dep):
        """Add a dependency."""
        if not isinstance(dep, Task):
            raise RuntimeError('You must supply a task for dependency.')
        if dep in self.dependencies:
            return
        self.dependencies.append(dep)

    def dependency_met(self):
        """Returns whether all dependencies are met and the task is able to run."""
        if not self.dependencies:
            return True
        for task in self.dependencies:
            if task.status != Task.FINISHED:
                return False
        return True

    def before_run(self, hook):
        """
        Add a before hook.
        :param hook must accept the current task as the only argument.
        """
        self.before_hooks.append(hook)
        return self

    def after_run(self, hook):
        """
        Add an after hook.
        :param hook must accept the current task as the only argument.
        """
        self.after_hooks.append(hook)
        return self

    def submit(self, project=_project.default_project):
        """Submit the task to a project."""
        project.tasks.append(self)
        self.project = project
        # Only refresh runtime if it's already started.
        if project.runtime and project.runtime.is_started:
            project.runtime.send_message(Message(Message.REFRESH))
        return self

    def finish(self):
        pass

    async def run(self):
        """Run the task."""
        try:
            logger.debug("Running before_hooks for %s [%s]" % (self, self.id))
            for hook in self.before_hooks:
                hook(self)

            await self.exec()

            logger.debug("Running after_hooks for %s [%s]" % (self, self.id))
            for hook in self.after_hooks:
                hook(self)

            # save to db
            self.finish()
            logger.debug("Task Finished: %s [%s]" % (self, self.id))

        except Exception as e:
            self.status = Task.ERROR
            logger.error("Task %s [%s] failed: %s" % (self, self.id, e.args))

        self.project.runtime.send_message(runtime_message.Message(runtime_message.Message.REFRESH))

    async def exec(self):
        """Put the actual logic here."""
        pass

    def get_status_display(self):
        status_str_map = {
            0: 'READY',
            1: 'RUNNING',
            3: 'FINISHED',
            4: 'ERROR',
        }
        return status_str_map[self.status]


def run_after(*arg):
    """A shortcut to append an after hook to one or multiple tasks."""
    def after_decorator(f):
        for task in arg:
            task.after_run(f)
    return after_decorator


def run_before(*arg):
    """A shortcut to append a before hook to one or multiple tasks."""
    def before_decorator(f):
        for task in arg:
            task.before_run(f)
    return before_decorator

