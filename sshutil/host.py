# -*- coding: utf-8 -*-#
#
# Copyright (c) 2015, Deutsche Telekom AG.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from __future__ import absolute_import, division, unicode_literals, print_function, nested_scopes
import functools
from sshutil.cmd import shell_escape_single_quote, SSHCommand, ShellCommand

__author__ = 'Christian Hopps'
__version__ = '1.0'
__docformat__ = "restructuredtext en"


class Host (object):
    def __init__ (self, server=None, port=22, cwd=None, username=None, password=None, debug=False):
        """
        A host object is either local or remote and provides easy access
        to the given local or remote host
        """
        self.cwd = cwd
        if server:
            self.cmd_class = functools.partial(SSHCommand,
                                               host=server,
                                               port=port,
                                               username=username,
                                               password=password,
                                               debug=debug)
        else:
            self.cmd_class = functools.partial(ShellCommand, debug=debug)

        if not self.cwd:
            self.cwd = self.cmd_class("pwd").run().strip()

    def get_cmd (self, command):
        return "bash -c 'cd {} && {}'".format(self.cwd, shell_escape_single_quote(command))

    def run_status_stderr (self, command):
        """
        Run a command return exit code, stdout and stderr.
        >>> host = Host()
        >>> status, output, error = host.run_status_stderr("ls -d /etc")
        >>> status
        0
        >>> print(output, end="")
        /etc
        >>> print(error, end="")
        >>> status, output, error = host.run_status_stderr("grep foobar doesnt-exist")
        >>> status
        2
        >>> print(output, end="")
        >>>
        >>> print(error, end="")
        grep: doesnt-exist: No such file or directory
        """
        return self.cmd_class(self.get_cmd(command)).run_status_stderr()

    def run_status (self, command):
        return self.cmd_class(self.get_cmd(command)).run_status()

    def run_stderr (self, command):
        return self.cmd_class(self.get_cmd(command)).run_stderr()

    def run (self, command):
        return self.cmd_class(self.get_cmd(command)).run()
