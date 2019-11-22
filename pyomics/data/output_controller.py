import os
from shutil import rmtree
from pyomics.task.pending_output import PendingOutput
from .output import Output
from pyomics.data import models


class OutputController:
    def __init__(self, mtask):
        self.task = mtask
        self.files = {}

    def __call__(self, name):
        """
        Get (pending) output for a name. Used for inputs only.
        :param name: name for the output.
        :return: a PendingOutput object.
        """
        return PendingOutput(self.task, name)

    def find_output(self):
        """Find all output and save them to self.files"""
        for name, value in self.task.module.outputs.items():
            self.files[name] = Output(self.task.model.id, name).files

    @models.model_operation
    def _update_model(self):
        import json
        for name, files in self.files.items():
            output_model, is_new_created = models.TaskOutput.get_or_create(
                task=self.task.model,
                label=name,
                defaults={'files': json.dumps(files)})

            if not is_new_created:
                output_model.files = json.dumps(files)
                output_model.save()

    def rename(self, src, dst):
        """
        Rename or move a file or directory.
        :param src: relative path of the source file.
        :param dst: relative path of the destination file.
        """
        src_ = self.__abs_path(src)
        dst_ = self.__abs_path(dst)
        os.rename(src_, dst_)
        for name, files in self.files.items():
            self.files[name] = [f.replace(src_, dst_) if f.startswith(src_) else f for f in files]
        self._update_model()
        return self

    def create_dir(self, path):
        """
        Create a directory.
        :param path: relative path of the directory.
        """
        path_ = self.__abs_path(path)
        os.mkdir(path_)
        return self

    def create_file(self, path, output_name):
        """
        Create a file.
        :param path: relative path of the file.
        :param output_name: add this file to an output name.
        """
        path_ = self.__abs_path(path)
        # create file
        with open(path_, 'a'):
            os.utime(path_, None)
        # append to self.files
        if output_name:
            if output_name not in self.files:
                self.files[output_name] = []
            self.files[output_name].append(path_)
            self._update_model()
        return self

    def remove(self, path, recursive=False):
        """
        Remove a file or a directory.
        :param path: relative path of the directory.
        :param recursive: set to true when removing a directory.
        """
        path_ = self.__abs_path(path)
        if recursive:
            # remove dir
            rmtree(path_)
        else:
            # remove file
            os.remove(path_)
        # update self.files
        for name, files in self.files.items():
            self.files[name] = [f for f in files if not f.startswith(path_)]
        self._update_model()
        return self

    def __abs_path(self, rpath=None):
        """
        Get absolute path for a path related to current task.
        :param rpath: the related path.
        :return the joined absolute path, or the root path of current task if rpath is None.
        """
        if rpath is None:
            return os.path.join(self.task.project.root_dir, self.task.module.name, self.task.name, 'output')
        else:
            return os.path.join(self.task.project.root_dir, self.task.module.name, self.task.name, 'output', rpath)
