#!/usr/bin/env python

"""
Description: generate shell scripts for FlowSmart to execute. Encapsulation of module instance.
Parameters:
 [1]: -w. project base directory
 [2]: -s.  shell output file absolute path.
 [3]: -c.  module task shell command.

Outputs: Shell scripts
"""

from optparse import OptionParser

class FSWrapper:
    DOAP_ENV_PATH = '/home/platform/omics_rails/current/backend/platform_env.sh'
    DOAP_AUTO_ENV_PATH = '/home/platform/omics_rails/current/backend/platform_db_auto_env.sh'

    def __init__(self, options):
        self.workdir = options.workdir  # project base directory
        self.shelldir = options.shelldir  # shell output directory
        self.command = options.command[1:-1]  # remove the single quotes
        self.sourcedir = options.basedir

    def create_shell(self):
        shstr = ''

        for line in self.command.split('\\n'):
            if line:
                subshstr = "(echo starts at: `date`) && "

                subshstr += "(cd %s; (source %s; source %s; %s))" % (self.workdir, FSWrapper.DOAP_ENV_PATH,
                                                                     FSWrapper.DOAP_AUTO_ENV_PATH, line)
                subshstr += " && (echo finishes at: `date`)\n"

                shstr += subshstr

        # FS passes absolute file path here
        with open(self.shelldir, 'w') as shfile:
            shfile.write(shstr)


if __name__ == '__main__':
    parser = OptionParser(usage="usage: %prog [options]",
                          version="%prog 1.0")
    parser.add_option('-w', '--work-dir',
                      action='store',
                      dest='workdir',
                      type='string',
                      help="the whole work directory. <required>", )
    parser.add_option('-s', '--shell-output-dir',
                      action='store',
                      dest='shelldir',
                      type='string',
                      help="the shell file which will be created. <required>", )
    parser.add_option('-c', '--command',
                      action='store',
                      dest='command',
                      type='string',
                      help="the module execution command string. <required>", )
    parser.add_option('-b', '--base',
                      action='store',
                      dest='basedir',
                      type='string',
                      help="the directory of module main program. <required>", )

    (options, args) = parser.parse_args()

    # call FS Wrapper to start building the shell
    fshell = FSWrapper(options)
    fshell.create_shell()


