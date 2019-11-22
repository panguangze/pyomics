from pyomics.conf import config


VERBOSE = 1
DEBUG = 2
WARNING = 3
ERROR = 4

log_level = {
    VERBOSE: 'v',
    DEBUG: 'd',
    WARNING: 'w',
    ERROR: 'e'
}

if config.DEBUG:
    user_log_level = config.DEBUG_OPTIONS.get('LOG_LEVEL', DEBUG)
else:
    user_log_level = WARNING


def get_logger(label):
    return Logger(label)


class Logger:
    def __init__(self, label):
        self.label = label

    def log(self, level, message):
        if level < user_log_level:
            return
        print("[%s][%s] %s" % (self.label, log_level[level], message))

    def verbose(self, message):
        self.log(VERBOSE, message)

    def debug(self, message):
        self.log(DEBUG, message)

    def warning(self, message):
        self.log(WARNING, message)

    def error(self, message):
        self.log(ERROR, message)
