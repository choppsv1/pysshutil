..
.. January 15 2018, Christian Hopps <chopps@gmail.com>
..

=====
Usage
=====

To use sshutil in a project::

  import sshutil

To run a command over SSH::

  from sshutil.cmd import SSHCommand

  cmd = SSHCommand("hostname", "red.example.com")
  assert "red" == output.cmd.run()

To read and write to a command over SSH::

  from sshutil.conn import SSHCommandSession

  session = SSHCommandSession("cat", "red.example.com")

  s = "testing\n"
  session.sendall(s)

  rs = session.recv(len(s))
  assert rs == s


To run many commands on a host::

  from sshutil.host import Host

  host = Host("red.example.com")
  assert "red" == host.run("hostname")
  assert "red.example.com" == host.run("hostname -f")

To globally disable ssh connection caching::

  import sshutil

  sshutil.DisableGlobalCaching()
