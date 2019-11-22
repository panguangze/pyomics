from pyomics.data import models
from pyomics.conf import config
from pyomics.data import user as _user
import datetime
import shortuuid
import sys
import os


class Project:
    def __init__(self, id=None):
        self.id = id or shortuuid.uuid()
        self.tasks = []
        self.runtime = None

        # get dockername and username in argv, if no, use default
        if len(sys.argv) > 2:
            self.docker = sys.argv[1]
            self.username = sys.argv[2]
        else:
            self.docker = None
            self.username = config.DEFAULT_USER
        user = _user.get_user(self.username)
        config.USER = user

        # get project root dir in argv, if no, use default
        if len(sys.argv) > 3:
            self.root_dir = sys.argv[3]
        else:
            self.root_dir = os.path.join(user.proj_root, self.id)
        self.__create_model()

    def all_tasks_finished(self):
        from pyomics.task.task import Task
        for task in self.tasks:
            if task.status != Task.FINISHED:
                return False
        return True

    @models.model_operation
    def finish(self):
        self.model.finished_at = datetime.datetime.now()
        self.model.save()

    @models.model_operation
    def __create_model(self):
        p = models.Project()
        p.name = self.id
        p.root_dir = self.root_dir
        p.username = self.username
        p.created_at = datetime.datetime.now()
        if self.docker and models.Docker.select().where((models.Docker.name == self.docker) &
                                                        (models.Docker.username == self.username)).count() == 1:
            p.docker = models.Docker.get((models.Docker.name == self.docker) &
                                         (models.Docker.username == self.username))
        p.save()
        self.model = p


default_project = Project()
