import socket
import json
import os
import pwd
import time


HOST, PORT = '10.37.0.76', 23333
ENCRYPTION = False
CONNECTION_TIMEOUT = 15  # timeout for socket connection, in seconds


class Actions:
    TEST_CONNECTION = 'TEST'
    REFRESH = 'REFRESH'
    STOP = 'STOP'
    SKIP = 'SKIP'
    KILL = 'KILL'
    SUSPEND = 'SUSPEND'
    SUSPEND_SOFT = 'SUSPEND_SOFT'
    SUSPEND_HARD = 'SUSPEND_HARD'
    RESUME = 'RESUME'
    RERUN = 'RERUN'
    RERUN_RECURSIVE = 'RERUN_RECURSIVE'
    RETRY = 'RETRY'
    QUERY = 'QUERY'
    QUERY_WITH_USAGE = 'QUERY_WITH_USAGE'
    CREATE_PIPELINE = 'ADD'
    DELETE = 'DELETE'


def do(action, **kwargs):
    """
    Usage:

    This is a independent portal to connect to FlowSmart's server. Use this the
    same way you would use a third party library:
        e.g.
        >>> import FSClient
        >>> FSClient.HOST, FSClient.PORT = '10.37.1.158', 23333

    Every operation is handled by this do() function. Possible actions are
    included in FSClient.Actions class.
        e.g.
        >>> FSClient.do(FSClient.Actions.CREATE_PIPELINE, config={...})
        >>> FSClient.do(FSClient.Actions.SUSPEND, pipeline='test_pipeline',
        ...             modules=['1a'], units=[1,2,3], using_line_no=True)


    All options supported:
        Actions.TEST_CONNECTION
            > A simple test of connection, returns "hello there!" if connection
              is successful.
        Actions.CREATE_PIPELINE
            > Create a pipeline, returns the pipeline status JSON string.
            > kwargs:
                config  (dict): Pipeline config in python dict format.
        Actions.REFRESH
            > Refresh the pipeline. Usually this is not needed since FlowSmart
              refreshes pipelines in the background.
            > kwargs:
                pipeline (str): Pipeline key.
        Actions.STOP
        Actions.SKIP
        Actions.KILL
        Actions.DELETE
        Actions.SUSPEND
        Actions.SUSPEND_SOFT
        Actions.SUSPEND_HARD
        Actions.RESUME
        Actions.RERUN
            > kwargs:
                new_module_config (dict): Add this when you need to update the
                                           module configuration before rerun.
        Actions.RERUN_RECURSIVE
        Actions.RETRY
            > kwargs of ABOVE(STOP~RETRY) actions:
                pipeline (str): Pipeline key.
                modules (list): List of module keys. (optional)
                units   (list): List of unit_task keys. (optional)
                using_line_no
                        (bool): Unit keys are not named in a transparent
                                 way to users, due to the possible naming
                                 conflict(hence the need for "unique_with").
                                 However, units can be identified by specifying
                                 which row the unit is recorded in the sample
                                 list.
                                 Note that if the unit occupies more than one
                                 rows in the sample list, e.g. if row 5,6,7,8
                                 all belongs to sample T001, then you only
                                 need to specify a subset of the rows since
                                 any subset of {5,6,7,8} can identify this unit.
        Actions.QUERY
            > Query the status of the pipeline.
            > kwargs:
                pipeline (str): Pipeline key.
        Actions.QUERY_WITH_USAGE
            > Query the status of the pipeline, along with all resource usage
              history.
            > kwargs:
                pipeline (str): Pipeline key.

    """
    all_actions = ('REFRESH', 'STOP', 'SKIP', 'SUSPEND', 'SUSPEND_SOFT',
                   'KILL', 'SUSPEND_HARD', 'RESUME', 'RERUN',
                   'RERUN_RECURSIVE', 'RETRY', 'QUERY', 'QUERY_WITH_USAGE',
                   'TEST', 'ADD', 'DELETE')
    if action not in all_actions:
        return _getErrJSONStr('Wrong action type {}'.format(action))
    msg_dict = {'ACTION': action,
                'PIPELINE': kwargs.get('pipeline', None),
                'MODULES': kwargs.get('modules', []),
                'UNITS': kwargs.get('units', []),
                'USER': _getCurrentUsername(),
                'TIMESTAMP': time.time(),
                'USING_LINE_NO': kwargs.get('using_line_no', True),
                'FROM_IP': socket.gethostbyname(socket.gethostname()),
                'MODULE_JSON': kwargs.get('new_module_json', None),
                }
    if action == 'ADD':
        msg_dict.update({'CONFIG': kwargs['config']})
    msg = json.dumps(msg_dict)
    return _client(msg)


def _client(message):
    global HOST, PORT, CONNECTION_TIMEOUT
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(CONNECTION_TIMEOUT)  # Into non-blocking mode.
        sock.connect((HOST, PORT))
        sock.settimeout(None)  # Change back into blocking mode.
        if len(message) > 0xffffff:  # 16MB
            return json.dumps({'STATUS': 'FAILED', 'ERROR': 'Message too long'})
        sock.sendall('{:06x}{}'.format(len(message), message).encode())
        response = []
        packet = sock.recv(1024).decode()
        len_field_len = packet.find('{')  # "{" is the end of the length field
        msg_len = int(packet[:len_field_len], 16)
        response.append(packet[len_field_len:])
        while len(response) < msg_len:
            packet = sock.recv(msg_len - len(response)).decode()
            if not packet:
                break
            response.append(packet)
        response = ''.join(response)
    except Exception as e:
        response = _getErrJSONStr(str(e))
    finally:
        sock.close()
    return response


def _encryptMsg(msg):
    global ENCRYPTION
    if ENCRYPTION:
        pass


def _getCurrentUsername():
    # return 'platform'
    return pwd.getpwuid(os.getuid()).pw_name


def _getErrJSONStr(msg):
    return json.dumps({'STATUS': 'FAILED',
                       'INFO': msg})


def beautify(response):
    """Beautify and print returned json."""
    from pprint import pprint
    a = json.loads(response)
    b = json.loads(a['INFO'])
    print('STATUS: ' + a['STATUS'])
    pprint(b)
