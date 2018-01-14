# -*- coding: utf-8 eval: (yapf-mode 1) -*-
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
import logging
import os
import subprocess
from sshutil import conn
from sshutil.cache import _setup_travis

__author__ = 'Christian Hopps'
__version__ = '1.0'
__docformat__ = "restructuredtext en"

logger = logging.getLogger(__name__)


def setup_module(_):
    _setup_travis()


class CalledProcessError(subprocess.CalledProcessError):
    def __init__(self, code, command, output=None, error=None):
        try:
            super(CalledProcessError, self).__init__(code, command, output, error)
        except TypeError:
            super(CalledProcessError, self).__init__(code, command, output)
            self.stderr = error
            self.args = [code, command, output, error]


def read_to_eof(recvmethod):
    buf = recvmethod(conn.MAXSSHBUF)
    while buf:
        yield buf
        buf = recvmethod(conn.MAXSSHBUF)


def terminal_size():
    import fcntl
    import termios
    import struct
    h, w, unused, unused = struct.unpack('HHHH',
                                         fcntl.ioctl(0, termios.TIOCGWINSZ,
                                                     struct.pack('HHHH', 0, 0, 0, 0)))
    return w, h


def shell_escape_single_quote(command):
    """Escape single quotes for use in a shell single quoted string
    Explanation:

    (1) End first quotation which uses single quotes.
    (2) Start second quotation, using double-quotes.
    (3) Quoted character.
    (4) End second quotation, using double-quotes.
    (5) Start third quotation, using single quotes.

    If you do not place any whitespaces between (1) and (2), or between
    (4) and (5), the shell will interpret that string as a one long word
    """
    return command.replace("'", "'\"'\"'")


class SSHCommand(conn.SSHConnection):
    def __init__(self,
                 command,
                 host,
                 port=22,
                 username=None,
                 password=None,
                 debug=False,
                 cache=None,
                 proxycmd=None):
        """An command to execute over an ssh connection.

        :param command: The shell command to execute.
        :param host: The host to execute the command on.
        :param port: The ssh port to use.
        :param username: The username to authenticate with if `None` getpass.get_user() is used.
        :param password: The password or public key to authenticate with.
                         If `None` given will also try using an SSH agent.
        :type password: str or ssh.PKey
        :param debug: True to enable debug level logging.
        :param cache: A connection cache to use.
        :type cache: SSHConnectionCache
        :param proxycmd: Proxy command to use when making the ssh connection.
        """
        self.command = command
        self.exit_code = None
        self.output = ""
        self.debug = debug
        self.error_output = ""

        super(SSHCommand, self).__init__(host, port, username, password, debug, cache, proxycmd)

    def _get_pty(self):
        width, height = terminal_size()
        # try:
        #     width, height = terminal_size()
        # except IOError:
        #     # probably not running from a terminal.
        #     width, height = 80, 24
        #     os.environ['TERM'] = "vt100"
        return self.chan.get_pty(term=os.environ['TERM'], width=width, height=height)

    def run_status_stderr(self):
        """Run the command returning exit code, stdout and stderr.

        :return: (returncode, stdout, stderr)

        >>> status, output, error = SSHCommand("ls -d /etc", "localhost").run_status_stderr()
        >>> status
        0
        >>> print(output, end="")
        /etc
        >>> print(error, end="")
        >>> status, output, error = SSHCommand("grep foobar doesnt-exist", "localhost").run_status_stderr()
        >>> status
        2
        >>> print(output, end="")
        >>>
        >>> print(error, end="")
        grep: doesnt-exist: No such file or directory
        """
        if self.debug:
            logger.debug("RUNNING: %s", str(self.command))

        try:
            if isinstance(self, SSHPTYCommand):
                self._get_pty()
            self.chan.exec_command(self.command)
            self.exit_code = self.chan.recv_exit_status()

            self.output = "".join([x.decode('utf-8') for x in read_to_eof(self.chan.recv)])
            self.error_output = "".join(
                [x.decode('utf-8') for x in read_to_eof(self.chan.recv_stderr)])

            if self.debug:
                logger.debug("RESULT: exit: %s stdout: '%s' stderr: '%s'", str(self.exit_code),
                             str(self.output), str(self.error_output))
            return (self.exit_code, self.output, self.error_output)
        finally:
            self.close()

    def run_stderr(self):
        """
        Run a command, return stdout and stderr,

        :return: (stdout, stderr)
        :raises: CalledProcessError

        >>> cmd = SSHCommand("ls -d /etc", "localhost")
        >>> output, error = cmd.run_stderr()
        >>> print(output, end="")
        /etc
        >>> print(error, end="")
        >>> cmd = SSHCommand("grep foobar doesnt-exist", "localhost")
        >>> cmd.run_stderr()                                    # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        CalledProcessError: Command 'grep foobar doesnt-exist' returned non-zero exit status 2
        """
        status, unused, unused = self.run_status_stderr()
        if status != 0:
            raise CalledProcessError(self.exit_code, self.command, self.output, self.error_output)
        return self.output, self.error_output

    def run_status(self):
        """
        Run a command, return exitcode and stdout.

        :return: (status, stdout)

        >>> status, output = SSHCommand("ls -d /etc", "localhost").run_status()
        >>> status
        0
        >>> print(output, end="")
        /etc
        >>> status, output = SSHCommand("grep foobar doesnt-exist", "localhost").run_status()
        >>> status
        2
        >>> print(output, end="")
        """
        return self.run_status_stderr()[0:2]

    def run(self):
        """
        Run a command, return stdout.

        :return: stdout
        :raises: CalledProcessError

        >>> cmd = SSHCommand("ls -d /etc", "localhost")
        >>> print(cmd.run(), end="")
        /etc
        >>> cmd = SSHCommand("grep foobar doesnt-exist", "localhost")
        >>> cmd.run()                                   # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        CalledProcessError: Command 'grep foobar doesnt-exist' returned non-zero exit status 2
        """
        return self.run_stderr()[0]


class SSHPTYCommand(SSHCommand):
    """Instances of this class also obtain a PTY prior to executing the command"""


class ShellCommand(object):
    def __init__(self, command, debug=False):
        self.command_list = ["/bin/sh", "-c", command]
        self.debug = debug
        self.exit_code = None
        self.output = ""
        self.error_output = ""

    def run_status_stderr(self):
        """
        Run a command over an ssh channel, return exit code, stdout and stderr.

        >>> cmd = ShellCommand("ls -d /etc")
        >>> status, output, error = cmd.run_status_stderr()
        >>> status
        0
        >>> print(output, end="")
        /etc
        >>> print(error, end="")
        """
        """
        >>> status, output, error = ShellCommand("grep foobar doesnt-exist").run_status_stderr()
        >>> status
        2
        >>> print(output, end="")
        >>>
        >>> print(error, end="")
        grep: doesnt-exist: No such file or directory
        """
        try:
            if self.debug:
                logger.debug("RUNNING: %s", str(self.command_list))
            pipe = subprocess.Popen(
                self.command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
            output, error_output = pipe.communicate()
            self.output = output.decode('utf-8')
            self.error_output = error_output.decode('utf-8')
            self.exit_code = pipe.returncode
        except OSError as error:
            logger.debug("RESULT: OSError: %s stdout: '%s' stderr: '%s'", str(error),
                         str(self.output), str(self.error_output))
            self.exit_code = 1
        else:
            if self.debug:
                logger.debug("RESULT: exit: %s stdout: '%s' stderr: '%s'", str(self.exit_code),
                             str(self.output), str(self.error_output))

        return (self.exit_code, self.output, self.error_output)

    def run_stderr(self):
        """
        Run a command over an ssh channel, return stdout and stderr,
        Raise CalledProcessError on failure

        >>> cmd = ShellCommand("ls -d /etc")
        >>> output, error = cmd.run_stderr()
        >>> print(output, end="")
        /etc
        >>> print(error, end="")
        >>> cmd = ShellCommand("grep foobar doesnt-exist")
        >>> cmd.run_stderr()                                    # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        CalledProcessError: Command 'grep foobar doesnt-exist' returned non-zero exit status 2
        """
        status, unused, unused = self.run_status_stderr()
        if status != 0:
            raise CalledProcessError(self.exit_code, self.command_list, self.output,
                                     self.error_output)
        return self.output, self.error_output

    def run_status(self):
        """
        Run a command over an ssh channel, return exitcode and stdout.

        >>> status, output = ShellCommand("ls -d /etc").run_status()
        >>> status
        0
        >>> print(output, end="")
        /etc
        >>> status, output = ShellCommand("grep foobar doesnt-exist").run_status()
        >>> status
        2
        >>> print(output, end="")
        """
        return self.run_status_stderr()[0:2]

    def run(self):
        """
        Run a command over an ssh channel, return stdout.
        Raise CalledProcessError on failure.

        >>> cmd = ShellCommand("ls -d /etc", False)
        >>> print(cmd.run(), end="")
        /etc
        >>> cmd = ShellCommand("grep foobar doesnt-exist", False)
        >>> cmd.run()                                   # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        CalledProcessError: Command 'grep foobar doesnt-exist' returned non-zero exit status 2
        """
        return self.run_stderr()[0]


if __name__ == "__main__":
    import time
    import gc

    cmd = SSHCommand("ls -d /etc", "localhost", debug=True)
    print(cmd.run())
    gc.collect()

    print(SSHCommand("ls -d /etc", "localhost", debug=True).run())
    gc.collect()

    print("Going to sleep for 2")
    time.sleep(2)
    gc.collect()

    print("Waking up")
    print(SSHCommand("ls -d /etc", "localhost", debug=True).run())
    gc.collect()
    print("Exiting")
