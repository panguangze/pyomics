import asyncio
from pyomics.task.task import Task
from pyomics.core import project as _project
from pyomics.core.exceptions import RuntimeNotReady
from pyomics.utils.logger import get_logger
from .runtime_message import Message
from pyomics.backend import fs_tool


logger = get_logger('runtime')


def begin(project=_project.default_project):
    logger.verbose("Project %s started." % project.id)
    runtime = RunTime(project)
    project.runtime = runtime
    runtime.start()


def end(project=_project.default_project):
    logger.verbose("Project %s end." % project.id)
    runtime = project.runtime
    if not runtime:
        raise RuntimeNotReady("You must call runtime.init on this project!")
    runtime.no_more_to_submit = True
    runtime.send_message(Message(Message.REFRESH))
    runtime.block_run()


def wait_for(*args, project=_project.default_project):
    modules = []
    for arg in args:
        if isinstance(arg, Task):
            modules.append(arg)

    runtime = project.runtime
    if not runtime:
        raise RuntimeNotReady("You must call runtime.init on this project!")
    runtime.wait_for(modules)


class RunTime:
    """
    The main class to control the task execution flow.
    It has one-to-one relationship with Project.
    """
    def __init__(self, project):
        self.project = project
        self.is_started = False
        self.is_finished = False
        self.has_error = False
        self.no_more_to_submit = False
        self.event_loop = asyncio.get_event_loop()
        self.message_queue = asyncio.Queue(loop=self.event_loop)

    def start(self):
        """
        Start the main loop so that it can dispatch tasks to FlowSmart.
        :return: None
        """
        asyncio.ensure_future(self._main_loop(), loop=self.event_loop)
        self.is_started = True

    def check_tasks(self):
        """
        Check if there are any task that is ready for submit, and submit them.
        :return: None
        """
        for task in self.project.tasks:
            logger.verbose("Checking task status: %s [%s] %s" % (task, task.id, task.get_status_display()))
            if task.status == Task.READY and task.dependency_met():
                task.status = Task.RUNNING
                asyncio.ensure_future(task.run(), loop=self.event_loop)
                logger.debug("Task submitted: %s" % task.__str__())
            elif task.status == Task.ERROR:
                self.has_error = True

    def delete_tasks(self):
        """
        Delete all submitted tasks from FlowSmart if there is a task failed.
        :return: None
        """
        for task in self.project.tasks:
            logger.debug("Deleting task: %s" % task)
            (succeeded, message) = fs_tool.task_delete(task)
            if succeeded:
                logger.debug("Task deleted: %s" % task)
            else:
                logger.debug("Task deletion encountered error: %s %s" % (task, message))

    def block_run(self):
        """
        Run the event loop forever.
        :return: None
        """
        self.event_loop.run_forever()
        self.event_loop.close()

    def wait_for(self, modules):
        """
        Block until modules are all finished.
        :param modules: a list of Module object.
        :return: None
        """
        self.event_loop.run_until_complete(self.block_until_modules(modules))

    def shutdown(self):
        self.event_loop.stop()
        self.project.finish()

    def send_message(self, msg):
        """
        Add a message to message queue so that it can be handled later.
        :param msg: a Message object.
        :return: None
        """
        self.message_queue.put_nowait(msg)

    async def _main_loop(self):
        logger.debug("Start main loop")

        while not self.is_finished:
            # Get message
            msg = await self.message_queue.get()
            if not isinstance(msg, Message):
                continue
            msg_type = msg.msg_type
            logger.debug("(%s)" % msg_type)
            # Check message type
            if msg_type == Message.REFRESH:
                # Check and submit tasks
                self.check_tasks()
                # Shutdown if all tasks are finished
                if (self.project.all_tasks_finished() and self.no_more_to_submit) or self.has_error:
                    self.is_finished = True
                    self.event_loop.call_soon(self.shutdown)

        if self.has_error:
            self.delete_tasks()

    async def block_until_modules(self, modules):
        logger.debug("Waiting for %s" % modules)
        while True:
            await asyncio.sleep(0.5)
            for m in modules:
                if m.status != Task.FINISHED:
                    break
            else:
                logger.debug("Continue")
                return
