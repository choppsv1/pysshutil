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
import getpass
import logging
import os
import socket
import threading
import traceback
import paramiko as ssh

__author__ = 'Christian Hopps'
__version__ = '1.0'
__docformat__ = "restructuredtext en"

MAXSSHBUF = 16 * 1024
MAXCHANNELS = 8

logger = logging.getLogger(__name__)

# Used by travis-ci testing
private_key = None


def shell_escape_single_quote (command):
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


class SSHConnection (object):
    """A connection to an SSH server"""
    ssh_sockets = {}
    ssh_socket_keys = {}
    ssh_socket_timeout = {}
    ssh_sockets_lock = threading.Lock()

    def __init__ (self, host, port=22, username=None, password=None, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        self.host_key = None
        self.chan = None
        self.ssh = None

        if not username:
            username = getpass.getuser()

        self.username = username
        self.password = password
        self.ssh = self.get_ssh_socket(host, port, username, password, debug)

        # Open a session.
        try:
            if self.debug:
                logger.debug("Opening SSH channel on socket (%s:%s)", self.host, str(self.port))
            self.chan = self.ssh.open_session()
        except:
            self.close()
            raise

    def __del__ (self):
        # Make sure we get rid of the cached reference to the open ssh socket
        self.close()

    def close (self):
        if hasattr(self, "chan") and self.chan:
            if self.debug:
                logger.debug("Closing SSH channel on socket (%s:%s)", self.host, str(self.port))
            self.chan.close()
            self.chan = None
        if hasattr(self, "ssh") and self.ssh:
            tmp = self.ssh
            self.ssh = None
            self.release_ssh_socket(tmp, self.debug)

    def is_active (self):
        return self.chan and self.ssh and self.ssh.is_active()

    @classmethod
    def get_ssh_socket (cls, host, port, username, password, debug):
        # Return an open ssh socket if we have one.
        key = "{}:{}:{}".format(host, port, username)
        with cls.ssh_sockets_lock:
            if key in cls.ssh_sockets:
                for entry in cls.ssh_sockets[key]:
                    if entry[2] < MAXCHANNELS:
                        sshsock = entry[1]
                        entry[2] += 1
                        if debug:
                            logger.debug("Incremented SSH socket use to %s", str(entry[2]))

                        # Cancel any timeout for closing, only really need to do this on count == 1.
                        cls.cancel_close_socket_expire(sshsock, debug)

                        return sshsock
                # This means there are no entries with free channels

            attempt = 0

            try:
                error = None
                for addrinfo in socket.getaddrinfo(host,
                                                   port,
                                                   socket.AF_UNSPEC,
                                                   socket.SOCK_STREAM):
                    af, socktype, proto, unused_name, sa = addrinfo
                    try:
                        ossock = socket.socket(af, socktype, proto)
                        ossock.connect(sa)
                        if attempt:
                            logger.debug("Succeeded after %s attempts to : %s", str(attempt), str(addrinfo))
                        break
                    except socket.error as ex:
                        ossock = None
                        logger.debug("Got socket error connecting to: %s: %s", str(addrinfo), str(ex))
                        attempt += 1
                        error = ex
                        continue
                else:
                    if error is not None:
                        logger.debug("Got error connecting to: %s: %s (no addr)", str(addrinfo), str(error))
                        raise error                             # pylint: disable=E0702
                    raise Exception("Couldn't connect to any resolution for {}:{}".format(host, port))
            except Exception as ex:
                logger.error("Got unexpected socket error connecting to: %s:%s: %s",
                             str(host),
                             str(port),
                             str(ex))
                raise

            try:
                if debug:
                    logger.debug("Opening SSH socket to %s:%s", str(host), str(port))

                sshsock = ssh.Transport(ossock)
                # self.ssh.set_missing_host_key_policy(ssh.AutoAddPolicy())

                # XXX this takes an event so we could yield here to wait for event.
                event = None
                sshsock.start_client(event)

                # XXX save this if we actually need it.
                sshsock.get_remote_server_key()

                # try:
                #     sshsock.auth_none(username)
                # except (ssh.AuthenticationException, ssh.BadAuthenticationType):
                #     pass

                if not sshsock.is_authenticated() and password is not None:
                    try:
                        sshsock.auth_password(username, password, event, False)
                    except (ssh.AuthenticationException, ssh.BadAuthenticationType):
                        pass

                if not sshsock.is_authenticated():
                    ssh_keys = ssh.Agent().get_keys()
                    if private_key:
                        # Used by travis-ci
                        ssh_keys += ( private_key, )
                    lastkey = len(ssh_keys) - 1
                    for idx, ssh_key in enumerate(ssh_keys):
                        if sshsock.is_authenticated():
                            break
                        try:
                            sshsock.auth_publickey(username, ssh_key, event)
                        except ssh.AuthenticationException:
                            if idx == lastkey:
                                raise
                            # Try next key
                assert sshsock.is_authenticated()

                # nextauth (rval from above) would be a secondary authentication e.g., google authenticator.

                # XXX using the below instead of the breakout above fails threaded.
                # sshsock.connect(hostkey=None,
                #                 username=self.username,
                #                 password=self.password)

                if key not in cls.ssh_sockets:
                    cls.ssh_sockets[key] = []
                # Add this socket to the list of sockets for this key
                cls.ssh_sockets[key].append([ossock, sshsock, 1])
                cls.ssh_socket_keys[sshsock] = key
                return sshsock
            except ssh.AuthenticationException as error:
                ossock.close()
                logger.error("Authentication failed: %s", str(error))
                raise

    @classmethod
    def cancel_close_socket_expire (cls, ssh_socket, debug):
        """Must enter locked"""
        if not ssh_socket:
            return
        if ssh_socket not in cls.ssh_socket_timeout:
            return
        if debug:
            logger.debug("Canceling timer to release ssh socket: %s", str(ssh_socket))
        timer = cls.ssh_socket_timeout[ssh_socket]
        del cls.ssh_socket_timeout[ssh_socket]
        timer.cancel()

    @classmethod
    def _close_socket_expire (cls, ssh_socket, debug):
        if not ssh_socket:
            return

        with cls.ssh_sockets_lock:
            # If we aren't present anymore must have been canceled
            if ssh_socket not in cls.ssh_socket_timeout:
                return

            if debug:
                logger.debug("Timer expired, releasing ssh socket: %s", str(ssh_socket))

            # Remove any timeout
            del cls.ssh_socket_timeout[ssh_socket]
            cls._close_socket(ssh_socket, debug)

    @classmethod
    def release_ssh_socket (cls, ssh_socket, debug):
        if not ssh_socket:
            return

        with cls.ssh_sockets_lock:
            key = cls.ssh_socket_keys[ssh_socket]

            assert key in cls.ssh_sockets
            entry = None
            for entry in cls.ssh_sockets[key]:
                if entry[1] == ssh_socket:
                    break
            else:
                raise KeyError("Can't find {} in list of entries".format(key))

            entry[2] -= 1
            if entry[2]:
                if debug:
                    logger.debug("Decremented SSH socket use to %s", str(entry[2]))
                return

            # We are all done with this socket
            # Setup a timer to actually close the socket.
            if ssh_socket not in cls.ssh_socket_timeout:
                if debug:
                    logger.debug("Setting up timer to release ssh socket: %s", str(ssh_socket))
                cls.ssh_socket_timeout[ssh_socket] = threading.Timer(1, cls._close_socket_expire, [ssh_socket, debug])
                cls.ssh_socket_timeout[ssh_socket].start()

    @classmethod
    def _close_socket (cls, ssh_socket, debug):
        entry = None
        try:
            key = cls.ssh_socket_keys[ssh_socket]
            for entry in cls.ssh_sockets[key]:
                if entry[1] == ssh_socket:
                    break
            else:
                assert False

            if debug:
                logger.debug("Closing SSH socket to %s", str(key))
            if entry[1]:
                entry[1].close()
                entry[1] = None

            if entry[0]:
                entry[0].close()
                entry[0] = None
        except Exception as error:
            logger.info("%s: Unexpected exception: %s: %s", str(cls), str(error), traceback.format_exc())
            logger.error("%s: Unexpected error closing socket:  %s", str(cls), str(error))
        finally:
            del cls.ssh_socket_keys[ssh_socket]
            if entry:
                cls.ssh_sockets[key].remove(entry)


class SSHClientSession (SSHConnection):
    """A client session to a host using a subsystem"""

    #---------------------------+
    # Overriding parent methods
    #---------------------------+

    def __init__ (self, host, port, subsystem, username=None, password=None, debug=False):
        super(SSHClientSession, self).__init__(host, port, username, password, debug)
        try:
            self.chan.invoke_subsystem(subsystem)
        except:
            self.close()
            raise

    #-------------+
    # New methods
    #-------------+

    def send (self, chunk):
        assert self.chan is not None
        self.chan.send(chunk)

    def sendall (self, chunk):
        assert self.chan is not None
        self.chan.sendall(chunk)

    def recv (self, size=MAXSSHBUF):
        assert self.chan is not None
        return self.chan.recv(size)


def setup_travis ():
    import sys
    global private_key                                      # pylint: disable=W0603

    logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
    print("Setup called.")
    if 'USER' in os.environ:
        if os.environ['USER'] != "travis":
            return
    else:
        if getpass.getuser() != "travis":
            return

    print("Executing under Travis-CI")
    ssh_dir = "{}/.ssh".format(os.environ['HOME'])
    priv_filename = os.path.join(ssh_dir, "id_rsa")
    if os.path.exists(priv_filename):
        logger.error("Found private keyfile")
        print("Found private keyfile")
        return
    else:
        logger.error("Creating ssh dir " + ssh_dir)
        print("Creating ssh dir " + ssh_dir)
        os.system("mkdir -p {}".format(ssh_dir))
        priv = ssh.RSAKey.generate(bits=1024)
        private_key = priv

        logger.error("Generating private keyfile " + priv_filename)
        print("Generating private keyfile " + priv_filename)
        priv.write_private_key_file(filename=priv_filename)

        pub = ssh.RSAKey(filename=priv_filename)
        auth_filename = os.path.join(ssh_dir, "authorized_keys")
        logger.error("Adding keys to authorized_keys file " + auth_filename)
        print("Adding keys to authorized_keys file " + auth_filename)
        with open(auth_filename, "a") as authfile:
            authfile.write("{} {}\n".format(pub.get_name(), pub.get_base64()))
        logger.error("Done generating keys")
        print("Done generating keys")

