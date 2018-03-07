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
import getpass
import logging
import socket
import paramiko as ssh
import sshutil.cache

from . import g_cache

__author__ = 'Christian Hopps'
__version__ = '1.0'
__date__ = 'January 14 2016'
__docformat__ = "restructuredtext en"

MAXSSHBUF = 16 * 1024
logger = logging.getLogger(__name__)


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


class SSHConnection(object):
    """A connection to an SSH server"""

    def __init__(self,
                 host,
                 port=22,
                 username=None,
                 password=None,
                 debug=False,
                 cache=None,
                 proxycmd=None):
        if cache is None:
            cache = g_cache

        self.host = str(host)
        self.port = int(port)
        self.debug = debug
        self.cache = cache
        self.host_key = None

        if not username:
            username = getpass.getuser()

        self.username = username

        self.ssh = cache.get_ssh_socket(host, port, username, password, debug, proxycmd)

        # Open a session.
        try:
            if self.debug:
                logger.debug("Opening SSH channel on socket (%s:%s)", self.host, str(self.port))
            self.chan = self.ssh.open_session()
        except:
            self.close()
            raise

    def __del__(self):
        # Make sure we get rid of the cached reference to the open ssh socket
        self.close()

    def close(self):
        if hasattr(self, "chan") and self.chan:
            if self.debug:
                logger.debug("Closing SSH channel on socket (%s:%s)", self.host, str(self.port))
            self.chan.close()
            self.chan = None
        if hasattr(self, "ssh") and self.ssh:
            tmp = self.ssh
            self.ssh = None
            self.cache.release_ssh_socket(tmp, self.debug)

    def is_active(self):
        return self.chan and self.ssh and self.ssh.is_active()


class SSHSession(SSHConnection):
    def send(self, chunk):
        assert self.chan is not None
        return self.chan.send(chunk)

    def sendall(self, chunk):
        assert self.chan is not None
        self.chan.sendall(chunk)

    def recv(self, size=MAXSSHBUF):
        assert self.chan is not None
        return self.chan.recv(size)

    def recv_ready(self):
        assert self.chan is not None
        return self.chan.recv_ready()

    def recv_stderr(self, size=MAXSSHBUF):
        assert self.chan is not None
        return self.chan.recv_stderr(size)

    def recv_stderr_ready(self):
        assert self.chan is not None
        return self.chan.recv_stderr_ready()


class SSHClientSession(SSHSession):
    """A client session to a host using a subsystem."""

    def __init__(self,
                 host,
                 port,
                 subsystem,
                 username=None,
                 password=None,
                 debug=False,
                 cache=None,
                 proxycmd=None):
        """Opens a client session to a host using a given subsystem.

        :param host: The host to execute the command on.
        :param port: The ssh port to use.
        :param subsystem: The subsystem to open over the SSH channel.
        :param username: The username to authenticate with if `None` getpass.get_user() is used.
        :param password: The password or public key to authenticate with.
                         If `None` given will also try using an SSH agent.
        :type password: str or ssh.PKey
        :param debug: True to enable debug level logging.
        :param cache: A connection cache to use.
        :type cache: SSHConnectionCache
        :param proxycmd: Proxy command to use when making the ssh connection.
        """
        super(SSHClientSession, self).__init__(host, port, username, password, debug, cache,
                                               proxycmd)
        try:
            self.chan.invoke_subsystem(subsystem)
        except:
            self.close()
            raise


class SSHCommandSession(SSHSession):
    """A client session to a host using a command i.e., like a remote pipe

    Objects of this class are useful for long running commands. For run-to-completion commands
    SSHCommand should be used.
    """

    def __init__(self,
                 host,
                 port,
                 command,
                 username=None,
                 password=None,
                 debug=False,
                 cache=None,
                 proxycmd=None):
        """Open a client session to a host using a command i.e., like a remote pipe

        :param host: The host to execute the command on.
        :param port: The ssh port to use.
        :param command: The shell command to execute.
        :param username: The username to authenticate with if `None` getpass.get_user() is used.
        :param password: The password or public key to authenticate with.
                         If `None` given will also try using an SSH agent.
        :type password: str or ssh.PKey
        :param debug: True to enable debug level logging.
        :param cache: A connection cache to use.
        :type cache: SSHConnectionCache
        :param proxycmd: Proxy command to use when making the ssh connection.
        """
        super(SSHCommandSession, self).__init__(host, port, username, password, debug, cache,
                                                proxycmd)
        try:
            self.chan.exec_command(command)
        except:
            self.close()
            raise

    def recv_exit_status(self):
        return self.chan.recv_exit_status()


class SSHSimpleCallHomeClient(object):
    """An example call home client."""

    def __init__(self, bind_addr, subsystem, username=None, password=None, debug=False):
        """An example client session to a server using a given subsystem where the server connects to us.

        :param bind_addr: The address to listen on on.
        :param subsystem: The subsystem to open over the SSH channel.
        :param username: The username to authenticate with if `None` getpass.get_user() is used.
        :param password: The password or public key to authenticate with.
                         If `None` given will also try using an SSH agent.
        :type password: str or ssh.PKey
        :param debug: True to enable debug level logging.
        """
        self.username = username
        self.password = password
        self.listensock = None
        self.subsystem = subsystem
        self.peeraddr = None
        self.ossock = None
        self.sshsock = None
        self.chan = None
        self.debug = debug

        # Open a listening socket and accept a connection.
        proto = socket.AF_INET6 if ":" in bind_addr[0] else socket.AF_INET
        self.listensock = socket.socket(proto, socket.SOCK_STREAM)
        self.listensock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listensock.bind(bind_addr)
        self.listenaddr = self.listensock.getsockname()
        self.listensock.listen(1)

    def accept_call_home(self, host_keys):
        """Accept a connection from the listen socket.

        :param subsystem: The subsystem to invoke on the connection request.
        :param host_keys: A dict of hostname whose value are a list of keys.
        :returns: None
        :raises:  SSHException
        """
        (self.ossock, self.peeraddr) = self.listensock.accept()

        def validate_keys(sshsock, key):
            # self is really the client not this policy object??? a bug said this, but code seems different
            peeraddr = sshsock.sock.getpeername()
            hostname = peeraddr[0]
            if hostname not in host_keys:
                raise ssh.SSHException('No hostkey found for server {}'.format(hostname))
            if key not in host_keys[hostname]:
                if host_keys[hostname]:
                    raise ssh.BadHostKeyException(hostname, key, host_keys[hostname][0])
                raise ssh.SSHException('No hostkey matched for server {}'.format(hostname))
            return True

        # Initialize/authenticate the ssh connection.
        self.sshsock = ssh.Transport(self.ossock)
        sshutil.cache.start_ssh(self.sshsock, self.username, self.password, validate_keys,
                                self.debug)

        # Open the channel.
        try:
            self.chan = self.sshsock.open_session()
            self.chan.invoke_subsystem(self.subsystem)
        except:
            self.close()
            raise

    #
    # XXX this duplicates SSHSession+parents, come up with a better way, maybe mixin
    #
    def __del__(self):
        # Make sure we get rid of the cached reference to the open ssh socket
        if hasattr(self, "chan"):
            self.close()

    def send(self, chunk):
        assert self.chan is not None
        return self.chan.send(chunk)

    def sendall(self, chunk):
        assert self.chan is not None
        self.chan.sendall(chunk)

    def recv(self, size=MAXSSHBUF):
        assert self.chan is not None
        return self.chan.recv(size)

    def recv_ready(self):
        assert self.chan is not None
        return self.chan.recv_ready()

    def recv_stderr(self, size=MAXSSHBUF):
        assert self.chan is not None
        return self.chan.recv_stderr(size)

    def recv_stderr_ready(self):
        assert self.chan is not None
        return self.chan.recv_stderr_ready()

    def close(self):
        socks = [self.chan, self.sshsock, self.ossock, self.listensock]
        self.chan = None
        self.sshsock = None
        self.ossock = None
        self.listensock = None
        for sock in socks:
            if self.debug:
                logger.debug("Closing %s", str(sock))
            sock.close()

    def is_active(self):
        return self.chan and self.sshsock and self.sshsock.is_active()
