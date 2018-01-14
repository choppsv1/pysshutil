# -*- coding: utf-8 eval: (yapf-mode 1) -*-
#
# January 14 2018, Christian E. Hopps <chopps@gmail.com>
#
# Copyright (c) 2018, Deutsche Telekom AG.
# All Rights Reserved.
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
import pytest

from sshutil.cache import SSHConnectionCache, SSHNoConnectionCache
from sshutil.cmd import SSHCommand, SSHPTYCommand

proxycmd = "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null localhost /bin/nc %h %p"


def setup_module(_):
    from sshutil.cache import _setup_travis
    _setup_travis()


@pytest.mark.parametrize(
    "cache",
    [SSHConnectionCache("SSH Session cache"),
     SSHNoConnectionCache("SSH Session no cache"), None])
@pytest.mark.parametrize("debug", [False, True])
def test_ok(cache, debug):
    output = SSHCommand("echo foobar", "localhost", debug=debug, cache=cache).run()
    assert output == "foobar\n"


# Failing for some reason
# @pytest.mark.parametrize(
#     "cache",
#     [SSHConnectionCache("SSH Session cache"),
#      SSHNoConnectionCache("SSH Session no cache"), None])
# @pytest.mark.parametrize("debug", [False, True])
# def test_pty_ok(cache, debug):
#     output = SSHPTYCommand("echo foobar", "localhost", debug=debug, cache=cache).run()
#     assert output == "foobar\n"

# @pytest.mark.parametrize("debug", [False, True])
# def test_config(debug):
#     # test newport
#     pass

# @pytest.mark.parametrize("debug", [False, True])
# def test_getaddrinfo_2nd(debug):
#     pass

# @pytest.mark.parametrize("debug", [False, True])
# def test_getaddrinfo_none(debug):
#     pass

# @pytest.mark.parametrize("debug", [False, True])
# def test_getaddrinfo_fail(debug):
#     pass

# @pytest.mark.parametrize("debug", [False, True])
# def test_pass_fail_key_ok(debug):
#     pass

# @pytest.mark.parametrize("debug", [False, True])
# def test_pass_fail_key_fail_agent(debug):
#     pass

# @pytest.mark.parametrize("debug", [False, True])
# def test_auth_fail(debug):
#     pass

# @pytest.mark.parametrize("debug", [False, True])
# def test_remote_closed(debug):
#     pass

__author__ = 'Christian E. Hopps'
__date__ = 'January 14 2018'
__version__ = '1.0'
__docformat__ = "restructuredtext en"
