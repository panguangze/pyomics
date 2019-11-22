from pyomics.data import models
from pyomics.core.exceptions import DockerDoesNotExist
from docker.errors import NotFound, APIError
from pyomics.conf import config
import docker
import os
import sys


class Container:
    def __init__(self, name, username, container_id):
        self.name = name
        self.username = username
        self.container_id = container_id

    @models.model_operation
    def create_model(self):
        d = models.Docker()
        d.name = self.name
        d.username = self.username
        d.container_id = self.container_id
        d.save()

    @property
    @models.model_operation
    def status(self):
        """Get container's status by container name."""

        if models.Docker.select().where((models.Docker.name == self.name) &
                                        (models.Docker.username == self.username)).count() != 1:
            raise DockerDoesNotExist("Failed to find docker with id %s" % self.name)

        self.__update_container()

        pyomics_docker = models.Docker.get((models.Docker.name == self.name) &
                                           (models.Docker.username == self.username))

        return pyomics_docker.status

    @property
    @models.model_operation
    def logs(self):
        """Get container's log by container name"""
        if models.Docker.select().where((models.Docker.name == self.name) &
                                        (models.Docker.username == self.username)).count() != 1:
            raise DockerDoesNotExist("Failed to find docker with id %s" % self.name)

        self.__update_container()

        pyomics_docker = models.Docker.get((models.Docker.name == self.name) &
                                           (models.Docker.username == self.username))

        with open(pyomics_docker.log, 'r') as f:
            log_lines = f.readlines()
        return ''.join(log_lines)

    def __update_container(self):
        """Update status and logs from docker container"""
        try:
            pyomics_docker = models.Docker.get((models.Docker.name == self.name) &
                                               (models.Docker.username == self.username))
            client = docker.from_env()
            container = client.containers.get(pyomics_docker.container_id)
            pyomics_docker.status = container.status
            log_file = pyomics_docker.log
            if not log_file:
                # log_file = os.path.join(config.LOG_PATH, pyomics_docker.container_id)
                log_file = os.path.join(sys.argv[3], 'log.txt')

            with open(log_file, 'wb') as f:
                f.write(container.logs())

            pyomics_docker.log = log_file
            pyomics_docker.save()

            if container.status == 'exited':
                container.remove()

        except NotFound:
            pass
        except APIError:
            pass





