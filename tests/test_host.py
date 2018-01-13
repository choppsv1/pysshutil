# -*- coding: utf-8 -*-#
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
from sshutil.host import Host
from sshutil.cmd import CalledProcessError


def setup_module (unused):
    from sshutil.cache import setup_travis
    setup_travis()


def test_local_ok ():
    local = Host()

    # -----------------
    # run_status_stderr
    # -----------------

    status, output, stderr = local.run_status_stderr("echo testing")
    assert status == 0
    assert output == "testing\n"
    assert stderr == ""
    status, output, stderr = local.run_status_stderr("echo testing >&2")
    assert status == 0
    assert output == ""
    assert stderr == "testing\n"
    status, output, stderr = local.run_status_stderr("echo testing; exit 2")
    assert status == 2
    assert output == "testing\n"
    assert stderr == ""
    status, output, stderr = local.run_status_stderr("echo testing >&2; exit 3")
    assert status == 3
    assert output == ""
    assert stderr == "testing\n"

    # ----------
    # run_status
    # ----------

    status, output = local.run_status("echo testing")
    assert status == 0
    assert output == "testing\n"
    status, output = local.run_status("echo testing >&2")
    assert status == 0
    assert output == ""
    status, output = local.run_status("echo testing; exit 2")
    assert status == 2
    assert output == "testing\n"
    status, output = local.run_status("echo testing >&2; exit 3")
    assert status == 3
    assert output == ""

    # ----------
    # run_stderr
    # ----------

    output, stderr = local.run_stderr("echo testing")
    assert output == "testing\n"
    assert stderr == ""
    output, stderr = local.run_stderr("echo testing >&2")
    assert output == ""
    assert stderr == "testing\n"
    try:
        output, stderr = local.run_stderr("echo testing; exit 2")
    except CalledProcessError as error:
        assert error.args[0] == 2
        # cmd [1] is based on the implementation ... not what we sent
        assert error.args[2] == "testing\n"
        assert len(error.args) == 3
    else:
        assert False


    # ---
    # run
    # ---

    output = local.run("echo testing")
    assert output == "testing\n"
    output = local.run("echo testing >&2")
    assert output == ""
    try:
        output = local.run("echo testing; exit 2")
    except CalledProcessError as error:
        assert error.args[0] == 2
        # cmd [1] is based on the implementation ... not what we sent
        assert error.args[2] == "testing\n"
        assert len(error.args) == 3
    else:
        assert False

__author__ = 'Christian Hopps'
__date__ = 'January 13 2018'
__version__ = '1.0'
__docformat__ = "restructuredtext en"
