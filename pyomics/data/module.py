import records
import pymysql
from pyomics.utils import decode
from pyomics.conf import config
from pyomics.core.exceptions import ModuleDoesNotExist
import sys
import json

def get_module(label):
    return Module(label)


class Module:
    def __init__(self, label):
        """
        Initialize module object with name. The program will find the matching item from
        public modules with latest versions.
        E.g. DOAP_Alignment

        If you want to use a specific version, please use @version.
        E.g. DOAP_Alignment@1
        :param label: unique label of DOAP modules.
        """
        if '@' in label:
            self.name = label.split('@')[0]
            self.version = label.split('@')[1]
        else:
            self.name = label
            self.version = None

        if config.DEBUG_OPTIONS.get('FAKE_MODULES'):
            self.version = '1'
            self.inputs = {}
            self.outputs = {}
            self.parameters = {}
            self.interpreter = 'dummy'
            self.source = ''
            self.source_root = ''
            self.base_commands = ''
            self.cpu = 1
            self.memory = 6666  # MB
            return
        if len(sys.argv) > 4:
            params_json_file = sys.argv[4]
            with open(params_json_file, 'r') as input:
                self.param_records = json.loads(input.read().strip())
        else:
            self.param_records = {}
        self.__connect_sql()

        # check module's existence, and load module information
        self.__load_module()

    def __connect_sql(self):
        # Connect to mysql database
        pymysql.install_as_MySQLdb()

        db = records.Database(config.DOAP_DB)
        self.__db = db

    def __load_module(self):
        """
        check whether module's existence, and load module information
        :return:
        """
        if self.version:
            query_statement = ("SELECT * FROM apps "
                               "where is_public='1' "
                               "and auto_version={version} "
                               "and label='{name}'").format(version=self.version, name=self.name)
        else:
            query_statement = ("SELECT * FROM apps "
                               "where is_public='1' "
                               "and label='{name}'").format(name=self.name)

        rows = self.__db.query(query_statement).all()

        if len(rows) == 0:
            if self.version:
                errormsg = "Failed to find matching module with name {0}, version {1}".format(self.name, self.version)
            else:
                errormsg = "Failed to find matching module with name {0}".format(self.name)

            raise ModuleDoesNotExist(errormsg)
        else:
            # if there are multiple matching modules, select the last module with highest version.
            highest_version = 0
            matched_module = None

            for module_record in rows:
                if module_record['auto_version'] > highest_version:
                    matched_module = module_record

        self.version = matched_module['auto_version']
        self.base_commands = matched_module['base_commands']
        self.interpreter = self.__load_interpreter(matched_module['interpreter_id'])
        self.inputs = self.__load_inputs(matched_module['id'])
        self.outputs = self.__load_outputs(matched_module['id'])
        self.parameters = self.__load_parameters(matched_module['id'])
        (self.cpu, self.memory) = self.__load_docker_config(matched_module['id'])

        program = matched_module['program']
        source = self.__load_source(matched_module['source_id'])
        self.source_root = source

        if program and program.startswith('/'):
            source += program
        else:
            source += '/' + program

        self.source = source

    def __load_docker_config(self, module_id):
        """
        Get docker information.
        :param module_id: module id. (not module instance)
        :return:
        """
        query_statement = ("SELECT * FROM apps "
                           "WHERE id={module_id}").format(module_id=module_id)

        module_record = self.__db.query(query_statement).first()
        cpu = module_record['cpu']
        memory = module_record['memory'] or 6666
        return cpu, memory

    def __load_source(self, source_id):
        """
        Get instance source location.
        :param source_id: FileSystem id.
        :return:
        """
        query_statement = ("SELECT * FROM file_systems "
                           "WHERE id={source_id}").format(source_id=source_id)

        filerecord = self.__db.query(query_statement).first()
        if filerecord['path'].startswith('/home/platform/rna_platform_v3'):
            return filerecord['path']
        else:
            return '/disk2/' + filerecord['path']
        return filerecord['path']

    def __load_interpreter(self, interpreter_id):
        """
        Get interpreter name.
        :param interpreter_id: interpreter id.
        :return:
        """
        query_statement = ("SELECT * FROM program_languages "
                           "WHERE id={interpreter_id}").format(interpreter_id=interpreter_id)

        interpreter = self.__db.query(query_statement).first()
        return interpreter['command']

    def __load_inputs(self, module_id):
        """
        Get inputs information.
        :param module_id: module id. (not module instance)
        :return:
        """
        query_statement = ("SELECT * FROM app_inputs "
                           "WHERE app_id={module_id}").format(module_id=module_id)

        rows = self.__db.query(query_statement).all()
        inputs = {}

        for input_record in rows:
            inputs[input_record['label']] = {
                'name': input_record['name'],
                'label': input_record['label'],
                'required': bool(input_record['required']),
                'format': input_record['file_format'],
                'prefix': input_record['prefix'],
                'is_array': bool(input_record['is_array']),
                'separator': input_record['separator'],
                'is_samples': bool(input_record['is_samples'])
            }

        return inputs

    def __load_outputs(self, module_id):
        """
        Get outputs information.
        :param module_id: module id. (not module instance)
        :return:
        """
        query_statement = ("SELECT * FROM app_outputs "
                           "WHERE app_id={module_id}").format(module_id=module_id)

        rows = self.__db.query(query_statement).all()
        outputs = {}

        for output_record in rows:
            outputs[output_record['label']] = {
                'name': output_record['name'],
                'label': output_record['label'],
                'required': bool(output_record['required']),
                'format': output_record['file_format'],
                'glob': output_record['glob'],
            }

        return outputs

    def __load_parameters(self, module_instance_id):
        """
        Get parameters information.
        :param module_instance_id: module instance id.
        :return:
        """
        rows = []
        if self.name in self.param_records:
            rows = self.param_records[self.name]
        parameters = {}

        for param_record in rows:
            parameters[param_record['prefix']] = {
                'name': param_record['name'],
                'type': param_record['param_type'],
                'required': bool(param_record['required']),
                'advanced': bool(param_record['advanced']),
                'default': param_record['default'],
                'prefix': param_record['prefix'],
            }
        query_statement = ("SELECT * FROM app_parameters "
                            "WHERE app_id={instance_id}").format(instance_id=module_instance_id)

        rows = self.__db.query(query_statement).all()
        for param_record in rows:
            if param_record['prefix'] not in parameters:
                parameters[param_record['prefix']] = {
                    'name': param_record['name'],
                    'type': param_record['param_type'],
                    'required': bool(param_record['required']),
                    'advanced': bool(param_record['advanced']),
                    'default': param_record['default'],
                    'prefix': param_record['prefix'],
                }
        return parameters

    def __str__(self):
        return self.name
