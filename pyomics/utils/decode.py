from base64 import b64decode
from zlib import decompress
import pickle


def dbsafe_decode(value, compress_object=False):
    '''
    Decode django picklefield string to python object
    '''
    value = value.encode()  # encode str to bytes
    value = b64decode(value)
    if compress_object:
        value = decompress(value)
    return pickle.loads(value)
