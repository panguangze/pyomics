import os
from pyomics.utils.logger import get_logger
from pyomics.data import models
from pyomics.data import module as _module
from pyomics.core.exceptions import ProjectDoesNotExist, ModuleTaskDoesNotExist
from pyomics.data.output import Output
from pyomics.conf import config


logger = get_logger('data_manager')


class DataManager:
    """Data manager for retrieving project data"""

    def __init__(self):
        pass

    @classmethod
    def find(cls, project_name, module_name=None, task_name=None, output_name=None):
        """
        Case 1: project_name
        Case 2: project_name & module_name
        Case 3: project_name & task_name
        Case 4: project_name & task_name & output_name
        """
        logger.verbose("Finding output files of [project] %s [module] %s [task] %s [output label] %s " %
                       (project_name, module_name, task_name, output_name))

        if project_name and module_name:
            return cls.__get_module_output_files(project_name, module_name)

        if project_name and task_name and output_name:
            return cls.__get_single_output_files(project_name, task_name, output_name)

        if project_name and task_name:
            return cls.__get_task_output_files(project_name, task_name)

        if project_name:
            return cls.__get_project_output_files(project_name)

        return

    @classmethod
    @models.model_operation
    def __get_project_output_files(cls, project_name):
        """
        Get project's all outputs
        :return: a dict.
        E.g.
        {
            task1: {
                'output1': [file1]
                'output2': [file2, file3]
            },
            task2: {
                'output1': [file1]
                'output2': [file2, file3]
            }
        }
        """
        if models.Project.select().where((models.Project.name == project_name) & (models.Project.username == config.USER.username)).count() != 1:
            raise ProjectDoesNotExist("Failed to find project with id %s" % project_name)
        tasks = models.Project.get((models.Project.name == project_name) & (models.Project.username == config.USER.username)).tasks

        results = {}

        for task_model in tasks:
            results[task_model.name] = cls.__get_task_output_files(project_name, task_model.name)

        return results

    @classmethod
    @models.model_operation
    def __get_module_output_files(cls, project_name, module_name):
        """
        Get all tasks' output which belong to the same module
        :return: a dict.
        E.g.
        {
            task1: {
                'output1': [file1]
                'output2': [file2, file3]
            },
            task2: {
                'output1': [file1]
                'output2': [file2, file3]
            }
        }
        """
        if models.Project.select().where((models.Project.name == project_name) & (models.Project.username == config.USER.username)).count() != 1:
            raise ProjectDoesNotExist("Failed to find project with id %s" % project_name)

        tasks = models.Task.select().join(models.Project).where(
                            (models.Project.name == project_name) &
                            (models.Task.module_label == module_name)
                        )

        results = {}

        for task_model in tasks:
            results[task_model.name] = cls.__get_task_output_files(project_name, task_model.name)

        return results

    @classmethod
    @models.model_operation
    def __get_task_output_files(cls, project_name, task_name):
        """
        Get task's all outputs
        :return: a dict with output label name as key and corresponding output files list as value.
        E.g.
        {
            'output1': [file1]
            'output2': [file2, file3]
        }
        """
        if models.Task.select().join(models.Project).where(
                (models.Task.name == task_name) &
                (models.Project.name == project_name) &
                (models.Project.username == config.USER.username)).count() != 1:
            raise ModuleTaskDoesNotExist("Failed to find task with id %s" % task_name)

        task_model = models.Task.select().join(models.Project).where(
            (models.Task.name == task_name) &
            (models.Project.name == project_name) &
            (models.Project.username == config.USER.username))[0]
        module = _module.get_module("%s@%s" % (task_model.module_label, task_model.module_version))

        results = {}

        for output_name in module.outputs:
            results[output_name] = cls.__get_single_output_files(project_name, task_name, output_name)

        return results

    @classmethod
    @models.model_operation
    def __get_single_output_files(cls, project_name, task_name, output_name):
        """
        Get single output of the task
        :return: a list containing output file paths.
        E.g. [file2, file3]
        """
        if models.Task.select().join(models.Project).where(
                (models.Task.name == task_name) &
                (models.Project.name == project_name) &
                (models.Project.username == config.USER.username)).count() != 1:
            raise ModuleTaskDoesNotExist("Failed to find task with id %s" % task_name)

        task_model = models.Task.select().join(models.Project).where(
            (models.Task.name == task_name) &
            (models.Project.name == project_name) &
            (models.Project.username == config.USER.username))[0]
        output = Output(task_model.id, output_name)

        return output.files
