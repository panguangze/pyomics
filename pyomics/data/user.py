import os
from pyomics.conf import config


def get_user(username):
    return User(username)


class User:
    def __init__(self, username):
        self.username = username
        self.proj_root = os.path.join(config.DOAP_MEDIA_ROOT, "user", username, "project")
        self.data_root = os.path.join(config.DOAP_MEDIA_ROOT, "user", username, "data")

    def __setattr__(self, attr_name, attr_value):
        """this is to avoid changing attribute value after initialization"""
        if attr_name not in self.__dict__:
            self.__dict__[attr_name] = attr_value
