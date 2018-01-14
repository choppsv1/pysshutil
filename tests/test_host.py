# -*- coding: utf-8 eval: (yapf-mode 1) -*-
#
# January 13 2018, Christian Hopps <chopps@gmail.com>
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
from sshutil.host import Host
from testfunc import _run_variations


def setup_module(module):
    del module  # unused
    from sshutil.cache import _setup_travis
    _setup_travis()


proxy = "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null localhost /bin/nc %h %p"


@pytest.mark.parametrize(
    "cache",
    [SSHConnectionCache("SSH Session cache"),
     SSHNoConnectionCache("SSH Session no cache"), None])
@pytest.mark.parametrize("proxycmd", [None, proxy])
@pytest.mark.parametrize("debug", [False, True])
def test_local_ok(cache, proxycmd, debug):
    _run_variations(Host(debug=debug, cache=cache, proxycmd=proxycmd))
