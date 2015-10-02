# -*- coding: utf-8 -*-#
#
# Copyright (c) 2015 by Christian E. Hopps.
# All rights reserved.
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
import os
import paramiko as ssh
from sshutil.cmd import ShellCommand, SSHCommand

__author__ = 'Christian Hopps'
__date__ = 'September 26 2015'
__docformat__ = "restructuredtext en"


def setup_module (unused):
    from sshutil.conn import _setup_module
    _setup_module(None)


def test_ssh_command ():
    cmd = SSHCommand("ls -d /etc", "localhost", debug=True)
    print(cmd.run())
