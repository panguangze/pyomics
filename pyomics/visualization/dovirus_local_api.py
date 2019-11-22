import socket
import json

HOST = 'localhost'
PORT = 25252
CONNECTION_TIMEOUT = 15


class ArgNotFound(Exception):
    def __init__(self, name):
        self.name = name

    def __unicode__(self):
        return "Argument \"{0}\" must be provided.".format(self.name)


def get_all_analyses(**kwargs):
    try:
        return _connect({
            'entry_point': 'analyses-list',
            'arguments': {}
        })
    except ArgNotFound as e:
        return {'status': "failed", 'message': e.__unicode__()}


def create_project(**kwargs):
    try:
        return _connect({
            'entry_point': 'create-project',
            'arguments': {
                'name': _get_or_error(kwargs, 'name'),
                'user': _get_or_error(kwargs, 'user', '')
            }
        })
    except ArgNotFound as e:
        return {'status': "failed", 'message': e.__unicode__()}


def upload_file(**kwargs):
    try:
        return _connect({
            'entry_point': 'upload-files',
            'arguments': {
                'project': _get_or_error(kwargs, 'project'),
                'analysis': _get_or_error(kwargs, 'analysis'),
                'files': _get_or_error(kwargs, 'files')
            }
        })
    except ArgNotFound as e:
        return {'status': "failed", 'message': e.__unicode__()}


def get_analysis_url(**kwargs):
    try:
        return _connect({
            'entry_point': 'analysis-url',
            'arguments': {
                'project': _get_or_error(kwargs, 'project'),
                'analysis': _get_or_error(kwargs, 'analysis'),
            }
        })
    except ArgNotFound as e:
        return {'status': "failed", 'message': e.__unicode__()}


def _connect(data):
    global HOST, PORT, CONNECTION_TIMEOUT
    sock = None
    try:
        sock = socket.create_connection((HOST, PORT), CONNECTION_TIMEOUT)
        sock.settimeout(None)

        message = json.dumps(data)
        sock.sendall('{:08x}{}'.format(len(message), message).encode('utf-8'))

        response = []
        msg_len = int(sock.recv(8), 16)
        while len(response) < msg_len:
            packet = sock.recv(msg_len - len(response)).decode('utf-8')
            if not packet:
                break
            response.append(packet)
        response = ''.join(response)
    except Exception as e:
        return {'status': "failed", 'message': "Client error: {0}".format(str(e))}
    finally:
        if sock:
            sock.close()
    return json.loads(response)


def _get_or_error(args, name, default_value=None):
    if default_value is None:
        if not name in args:
            raise ArgNotFound(name)
    return args.get(name, default_value)
