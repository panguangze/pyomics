import os
import json
import codecs
from . import fs_client
from pyomics.task.task import Task
from pyomics.task.pending_output import PendingOutput
from pyomics.data.output import Output
from pyomics.utils.logger import get_logger
from pyomics.conf import config


logger = get_logger('fs_tool')
SEPARATOR = [' ', ',', ';']

def task_json(task):
    """
    Generate module task json for flowsmart.
    :param task: ModuleTask object.
    :return:
    """
    # create output and shell folder for module task
    output_dir = os.path.join(task.root_dir, 'output')
    shell_dir = os.path.join(task.root_dir, 'shell')

    if os.path.isdir(output_dir):
        raise FileExistsError("Task working directory already exists: %s" % output_dir)
    else:
        os.makedirs(output_dir)
        logger.debug("Task %s %s output folder created: %s" % (task, task.id, output_dir))

    if os.path.isdir(shell_dir):
        raise FileExistsError("Task working directory already exists: %s" % shell_dir)
    else:
        os.makedirs(shell_dir)
        logger.debug("Task %s %s shell folder created: %s" % (task, task.id, shell_dir))

    fs_json = {
        'pipeline': str(task),
        'pipeline_key': task.id,
        'user': 'platform',
        'admins': ['xuchang', 'platform'],
        'job_controller': 'docker',
        'docker': {
            'mount': [
                '{0}:{0}:ro'.format(task.module.source_root),
                # '{0}:{0}:ro'.format(os.path.join('/home/platform/omics_rails/current', task.module.source_root)) if "/home/platform/rma_platform_v3" not in task.module.source_root,
                '{0}:{0}:ro'.format('/mnt'),
                '{0}:{0}:ro'.format('/disk2'),
                '{0}:{0}:ro'.format('/home/platform'),
                '{0}:{0}:rw'.format('/home/platform/juicebox/'),
                '{0}:/media/:ro'.format('/disk2/media'),
            ],
            'user': 'platform',
        },

        'max_number_of_jobs': 10,

        'WORKING_DIRECTORY': {
            'alias': '-w',
            'value': output_dir
        },

        'SHELL_OUTPUT_DIR': {
            'alias': '-s',
            'value': shell_dir
        },

        'SAMPLE_LIST': {
            'alias': '-l',
            'type':  'csv',
            'value': None,
            'sub_list_dir': None
        }
    }
    # if "/home/platform/rma_platform_v3" in task.module.source_root:
    #     fs_json['docker']['mount'].append('{0}:{0}:ro'.format(task.module.source_root))
    # else:
    #     fs_json['docker']['mount'].append('{0}:{0}:ro'.format(os.path.join('/home/platform/omics_rails/current', task.module.source_root)))

    module_info = {
        'key': '1',
        'name':	task.module.name,
        'skip':	False,
        'stop':	False,
        'auto_retry': 0,
        'executor': 'python',
        'script': config.FS_WRAPPER_PATH,
        'unit': None,
        'unique_with': [],
        'create_shell':	True,
        'split_shell': 1,
        'prev_module': [],
        'depth_first': True,
        'parameters': {
            '-c': "'%s'" % _build_task_command(task),
            '-b': os.path.dirname(task.module.source)
        },
        'default_params': {
          'sample_list': None
        },
        'docker': {
            'cpu': task.module.cpu,
            'mem': "%sMB" % task.module.memory,
            'mount': [
                '{0}:{0}:rw'.format(output_dir),
                '{0}:{0}:rw'.format(shell_dir),
            ]
        },
    }

    fs_json['MODULES'] = {
        '1': module_info
    }

    return fs_json


def _build_task_command(task):
    """
    Build task command by inputs and parameters
    :param task: ModuleTask object.
    """
    input_str = ''
    param_str = ''

    for label, minput in task.module.inputs.items():
        if minput['prefix'] not in task.inputs:
            continue

        task_input = task.inputs[minput['prefix']]

        if isinstance(task_input, PendingOutput):
            output = Output(task_input.task.model.id, task_input.name)
            if minput['is_array']:
                separator = SEPARATOR[minput['separator']]
                input_val = separator.join(output.files)
            else:
                input_val = output.files[0] if len(output.files) > 0 else ''
        elif type(task_input) is list:
            input_val = []
            for sub_input in task_input:
                if isinstance(sub_input, PendingOutput):
                    output = Output(sub_input.task.model.id, sub_input.name)
                    input_val += output.files
                else:
                    input_val.append(sub_input)
            if minput['is_array']:
                separator = minput['separator']
                input_val = separator.join(input_val)
            else:
                input_val = input_val[0] if len(input_val) > 0 else ''
        else:
            input_val = task_input

        input_str += "%s %s " % (minput['prefix'], input_val)

    loop_split_chr = False
    split_chr_prefix = ''
    need_chr_m = False

    for prefix, param in task.module.parameters.items():
        if prefix == '-w':
            continue

        if prefix in task.params:
            param_val = task.params[prefix]
        else:
            param_val = param['default']

        if param['type'] == 'boolean':
            if str(param_val).lower() == 'true':
                param_str += "%s " % prefix
        elif param['type'] == 'splitchr':
            loop_split_chr = True
            split_chr_prefix = prefix
            if str(param_val).lower() == 'true':
                need_chr_m = True
            else:
                need_chr_m = False
        else:
            # ignore parameter if value is empty
            if str(param_val).strip() != '':
                param_str += "%s %s " % (prefix, param_val)
    # if "/home/platform/rna_platform_v3" in task.module.source:
    if '-w' in task.module.parameters:
        command = "{0} {1} {2} -w {3} {4} {5}".format(task.module.interpreter, task.module.source,
                                              task.module.base_commands, os.path.join(task.root_dir, 'output'),
                                              input_str, param_str)
    else:
        command = "{0} {1} {2} {3} {4}".format(task.module.interpreter, task.module.source,
                                              task.module.base_commands, input_str, param_str)
    # else:
    #     command = "{0} /home/platform/omics_rails/current/{1} {2} -w {3} {4} {5}".format(task.module.interpreter, task.module.source,
    #                                               task.module.base_commands, os.path.join(task.root_dir, 'output'),
    #                                               input_str, param_str)
    # for splitchr type parameter, we need to loop from chr1 to 22, x, y. include chrM if
    if loop_split_chr:
        chr_range = list(range(1, 23)) + ['X', 'Y']
        if need_chr_m:
            chr_range += ['M']

        batch_command = ''
        for chr in chr_range:
            batch_command += "{0} {1} chr{2} \n".format(command, split_chr_prefix, chr)
        command = batch_command

    return command


def task_submit(task,task_json):
    """
    Submit a task and return the result.
    :param task_json: the json string.
    :return: (success, message) Whether the submission is success and error message in case of error.
    """
    with open(os.path.join(task.root_dir, ".config.json"), 'w') as output:
        output.write(json.dumps(task_json))
    fs_feedback = json.loads(fs_client.do(fs_client.Actions.CREATE_PIPELINE, config=task_json))

    if fs_feedback['STATUS'] != 'OK':
        if 'EXCEPTION' in fs_feedback:
            error_msg = fs_feedback['EXCEPTION']
        else:
            error_msg = fs_feedback['INFO']
        return False, error_msg

    return True, None


def task_delete(task):
    """
    Delete a task and return the result.
    :param task: ModuleTask object.
    :return: (success, message) Whether the deletion success and error message in case of error.
    """
    fs_feedback = json.loads(fs_client.do(fs_client.Actions.KILL, pipeline=task.id))

    if fs_feedback['STATUS'] != 'OK':
        if 'EXCEPTION' in fs_feedback:
            error_msg = fs_feedback['EXCEPTION']
        else:
            error_msg = fs_feedback['INFO']
        return False, error_msg

    return True, None


def task_status(task):
    """
    Query the status of module task
    :param task: ModuleTask object.
    """
    fs_client.do(fs_client.Actions.REFRESH, pipeline=task.id)
    fs_feedback = json.loads(fs_client.do(fs_client.Actions.QUERY, pipeline=task.id))
    logger.verbose("checking status for %s %s" % (task, task.id))
    # failed to connect FlowSmart
    if fs_feedback['STATUS'] != 'OK':
        return task.status
    else:
        status = json.loads(fs_feedback["INFO"])['status']

        status_map = {
            'pipeline_created': Task.READY,
            'creation_failed': Task.ERROR,
            'in_progress': Task.RUNNING,
            'completed': Task.FINISHED,
            'in_progress_&_need_user_intervention': Task.ERROR,
            'not_active': Task.ERROR
        }

        return status_map[status]


def task_log(task):
    """
    Get task log
    :param task: ModuleTask object.
    """
    fs_feedback = json.loads(fs_client.do(fs_client.Actions.QUERY, pipeline=task))

    stderr = ""
    stdout = ""

    if fs_feedback['STATUS'] == 'OK':
        modules = json.loads(fs_feedback["INFO"])["modules"]
        for k1 in modules:
            for k2 in modules[k1]['unit_tasks']:
                for k3 in modules[k1]['unit_tasks'][k2]['jobs']:
                    std_stream = modules[k1]['unit_tasks'][k2]['jobs'][k3]['std_stream']
                    stderr_file = std_stream["stderr"]
                    stdout_file = std_stream["stdout"]
                    if os.path.isfile(stderr_file):
                        with codecs.open(stderr_file, 'r', encoding='utf8') as f:
                            stderr += "".join(f.readlines())
                    if os.path.isfile(stdout_file):
                        with codecs.open(stdout_file, 'r', encoding='utf8') as f:
                            stdout += "".join(f.readlines())

    return {
        "stderr": stderr,
        "stdout": stdout
    }
