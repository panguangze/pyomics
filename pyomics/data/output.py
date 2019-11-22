from pyomics.core.exceptions import ModuleOutputNotExist, ModuleTaskDoesNotExist
from pyomics.data import models
from pyomics.data import module as _module
import os
import glob
import json


class Output:
    def __init__(self, task_id, name):
        """
        :param task_id: Task record id in sql table. Not task name.
        :param name: output label
        """
        self.name = name
        self.task_id = task_id
        self.root_dir = ''
        self.module = None
        self.__load_task_model()
        self.files = self.__find_output()

    @models.model_operation
    def __load_task_model(self):
        if models.Task.select().where(models.Task.id == self.task_id).count() != 1:
            raise ModuleTaskDoesNotExist("Failed to find task with id %s" % self.task_id)
        task_model = models.Task.get_by_id(self.task_id)
        self.root_dir = os.path.join(task_model.project.root_dir, task_model.module_label, task_model.name)
        self.module = _module.get_module("%s@%s" % (task_model.module_label, task_model.module_version))

    @models.model_operation
    def __find_output(self):
        """
        Get from TaskOutput table if record exists.
        Otherwise, use glob to match output files.
        :return:
        """
        if models.TaskOutput.select().where((models.TaskOutput.label == self.name) &
                                            (models.TaskOutput.task == self.task_id)).count() == 1:
            task_output_model = models.TaskOutput.get((models.TaskOutput.label == self.name) &
                                                      (models.TaskOutput.task == self.task_id))
            return json.loads(task_output_model.files)
        else:
            matching_files = []
            all_task_outputs = self.module.outputs

            if self.name not in all_task_outputs:
                raise ModuleOutputNotExist("No output named %s in module %s" % (self.name, self.module))

            for regex in all_task_outputs[self.name]['glob']:
                path_glob = os.path.join(self.root_dir, 'output', regex)  # root_dir/output & root_dir/shell
                matching_files = glob.glob(path_glob)
            # remove duplicates
            return list(set(matching_files))
