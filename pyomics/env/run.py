import sys
sys.path.extend(['/home/platform/pyomics_for_rails'])
import os
import docker
from pyomics.conf import config
from pyomics.env.container import Container
import shortuuid
from pyomics.utils.logger import get_logger
import json

logger = get_logger('run')

IMAGE = "pyomics:latest"
FS_PORT = 23333


def mounts(*paths):
    conf = {}
    for path, mode in paths:
        conf[path] = {
            'bind': path, 'mode': mode
        }
    return conf


if __name__ == "__main__":
    """Command: python run.py pyomics/script/path.py [username] [project_root] [param_records]"""
    abs_path = os.path.abspath(sys.argv[1])
    usr_path = os.path.dirname(abs_path)

    if len(sys.argv) > 2:
        username = sys.argv[2]
    else:
        username = config.DEFAULT_USER

    docker_name = shortuuid.uuid()

    logger.verbose("Docker %s started" % docker_name)

    COMMAND = "env PYTHONPATH=%s python %s %s %s " % (config.ENV_PATH, abs_path, docker_name, username)
    # if len(sys.argv) > 3:
    #     COMMAND += " " + sys.argv[3]
    # if len(sys.argv) > 4:
    #     COMMAND += " " + sys.argv[4]
    if len(sys.argv) > 3:
        COMMAND += " ".join(sys.argv[3:])
    client = docker.from_env()
    docker_container = client.containers.run(IMAGE, COMMAND,
                                      detach=True,
                                      remove=False,
                                      network_mode='host',
                                      volumes=mounts((usr_path, 'ro'),
                                                     ('/home/platform/omics_rails/current/media/user/'+username, 'ro'),
                                                     ('/disk2/media/', 'rw'),
                                                     ('/mnt/delta_adam/User/chelijia', 'ro'),
                                                     (sys.argv[3], 'rw'),
                                                     (config.ENV_PATH, 'ro')))

    container = Container(docker_name, username, docker_container.short_id)
    container.create_model()

    logger.debug(docker_container.short_id)

    import time

    while container.status == 'running':
        time.sleep(5)
        logger.debug(container.status)
        logger.debug(container.logs)

