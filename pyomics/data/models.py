from peewee import *
from playhouse.db_url import connect
from pyomics.conf import config
from pyomics.core.exceptions import DataBaseOperationFailed
from pyomics.utils.logger import get_logger

db = connect(config.PYOMICS_DB)
logger = get_logger("models")


def model_query_begin():
    models = [Docker, Project, Task, TaskOutput]
    try:
        for model in models:
            if not model.table_exists():
                logger.debug("Table not found, creating table for %s" % model.__name__)
                db.create_tables([model])
        logger.verbose("Connecting database...")
        db.connect(reuse_if_open=True)
    except OperationalError as error:
        raise DataBaseOperationFailed(error.args)


def model_query_end():
    logger.verbose("Closing database...")
    db.close()


def model_operation(fn):
    def wrapped(*args, **kwargs):
        model_query_begin()
        result = fn(*args, **kwargs)
        model_query_end()
        return result
    return wrapped


class BaseModel(Model):
    class Meta:
        database = db


class Docker(BaseModel):
    DOCKER_STATUSES = (
        ('restarting', 'restarting'),
        ('running', 'running'),
        ('paused', 'paused'),
        ('exited', 'exited'),
    )
    name = CharField(null=False, unique=True, max_length=127)
    container_id = CharField(null=False, max_length=50)
    username = CharField(null=False)
    status = CharField(max_length=10, default='running', choices=DOCKER_STATUSES, null=False)
    log = TextField(null=True)
    viz_id = IntegerField(null=True)


class Project(BaseModel):
    name = CharField(null=False, max_length=127)
    root_dir = CharField(null=False)
    username = CharField(null=False)
    docker = ForeignKeyField(Docker, backref='projects', null=True)

    created_at = DateTimeField()
    finished_at = DateTimeField(null=True, default=None)

    class Meta:
        indexes = (
            (('name', 'username'), True),
        )


class Task(BaseModel):
    TASK_TYPES = (('N', "Normal Task"), ('C', "Complex Task"))

    task_type = CharField(max_length=1, default='N', choices=TASK_TYPES, null=False)
    name = CharField(null=False, max_length=127)
    module_label = CharField(max_length=150, null=False)
    module_version = IntegerField(null=False)

    project = ForeignKeyField(Project, backref='tasks', null=True)

    created_at = DateTimeField()
    finished_at = DateTimeField(null=True, default=None)

    class Meta:
        indexes = (
            (('name', 'project'), True),
        )


class TaskOutput(BaseModel):
    task = ForeignKeyField(Task, backref='outputs')
    label = CharField(max_length=100, null=False)
    files = TextField(null=False)

    class Meta:
        indexes = (
            (('task', 'label'), True),
        )
