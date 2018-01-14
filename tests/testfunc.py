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
from sshutil.cmd import CalledProcessError


def _run_variations(runnable):
    # -----------------
    # run_status_stderr
    # -----------------

    status, output, stderr = runnable.run_status_stderr("echo testing")
    assert status == 0
    assert output == "testing\n"
    assert stderr == ""
    status, output, stderr = runnable.run_status_stderr("echo testing >&2")
    assert status == 0
    assert output == ""
    assert stderr == "testing\n"
    status, output, stderr = runnable.run_status_stderr("echo testing; exit 2")
    assert status == 2
    assert output == "testing\n"
    assert stderr == ""
    status, output, stderr = runnable.run_status_stderr("echo testing >&2; exit 3")
    assert status == 3
    assert output == ""
    assert stderr == "testing\n"

    status, output, stderr = runnable.run_status_stderr("no-command-named-this")
    assert status == 127
    assert output == ""
    assert "command not found" in stderr

    # ----------
    # run_status
    # ----------

    status, output = runnable.run_status("echo testing")
    assert status == 0
    assert output == "testing\n"
    status, output = runnable.run_status("echo testing >&2")
    assert status == 0
    assert output == ""
    status, output = runnable.run_status("echo testing; exit 2")
    assert status == 2
    assert output == "testing\n"
    status, output = runnable.run_status("echo testing >&2; exit 3")
    assert status == 3
    assert output == ""

    # ----------
    # run_stderr
    # ----------

    output, stderr = runnable.run_stderr("echo testing")
    assert output == "testing\n"
    assert stderr == ""
    output, stderr = runnable.run_stderr("echo testing >&2")
    assert output == ""
    assert stderr == "testing\n"
    try:
        output, stderr = runnable.run_stderr("echo foo; exit 2")
    except CalledProcessError as error:
        assert error.args[0] == 2
        assert error.args[2] == "foo\n"
        assert error.args[3] == ""
        assert len(error.args) == 4
    else:
        assert False
    try:
        output, stderr = runnable.run_stderr("echo bar >&2; exit 2")
    except CalledProcessError as error:
        assert len(error.args) == 4
        assert error.args[0] == 2
        assert error.args[2] == ""
        assert error.args[3] == "bar\n"
    else:
        assert False
    try:
        output, stderr = runnable.run_stderr("echo foo; echo bar >&2; exit 2")
    except CalledProcessError as error:
        assert len(error.args) == 4
        assert error.args[0] == 2
        assert error.args[2] == "foo\n"
        assert error.args[3] == "bar\n"
    else:
        assert False

    # ---
    # run
    # ---

    output = runnable.run("echo testing")
    assert output == "testing\n"
    output = runnable.run("echo testing >&2")
    assert output == ""
    try:
        output = runnable.run("echo testing; exit 2")
    except CalledProcessError as error:
        assert error.args[0] == 2
        # cmd [1] is based on the implementation ... not what we sent
        assert error.args[2] == "testing\n"
        assert len(error.args) == 4
    else:
        assert False


def _init_variations(cl, debug, cache, proxycmd):
    # -----------------
    # run_status_stderr
    # -----------------

    status, output, stderr = cl(
        "echo testing", "localhost", debug=debug, cache=cache,
        proxycmd=proxycmd).run_status_stderr()
    assert status == 0
    assert output == "testing\n"
    assert stderr == ""
    status, output, stderr = cl(
        "echo testing >&2", "localhost", debug=debug, cache=cache,
        proxycmd=proxycmd).run_status_stderr()
    assert status == 0
    assert output == ""
    assert stderr == "testing\n"
    status, output, stderr = cl(
        "echo testing; exit 2", "localhost", debug=debug, cache=cache,
        proxycmd=proxycmd).run_status_stderr()
    assert status == 2
    assert output == "testing\n"
    assert stderr == ""
    status, output, stderr = cl(
        "echo testing >&2; exit 3", "localhost", debug=debug, cache=cache,
        proxycmd=proxycmd).run_status_stderr()
    assert status == 3
    assert output == ""
    assert stderr == "testing\n"

    status, output, stderr = cl(
        "no-command-named-this", "localhost", debug=debug, cache=cache,
        proxycmd=proxycmd).run_status_stderr()
    assert status == 127
    assert output == ""
    assert "command not found" in stderr

    # ----------
    # run_status
    # ----------

    status, output = cl(
        "echo testing", "localhost", debug=debug, cache=cache, proxycmd=proxycmd).run_status()
    assert status == 0
    assert output == "testing\n"
    status, output = cl(
        "echo testing >&2", "localhost", debug=debug, cache=cache, proxycmd=proxycmd).run_status()
    assert status == 0
    assert output == ""
    status, output = cl(
        "echo testing; exit 2", "localhost", debug=debug, cache=cache,
        proxycmd=proxycmd).run_status()
    assert status == 2
    assert output == "testing\n"
    status, output = cl(
        "echo testing >&2; exit 3", "localhost", debug=debug, cache=cache,
        proxycmd=proxycmd).run_status()
    assert status == 3
    assert output == ""

    # ----------
    # run_stderr
    # ----------

    output, stderr = cl(
        "echo testing", "localhost", debug=debug, cache=cache, proxycmd=proxycmd).run_stderr()
    assert output == "testing\n"
    assert stderr == ""
    output, stderr = cl(
        "echo testing >&2", "localhost", debug=debug, cache=cache, proxycmd=proxycmd).run_stderr()
    assert output == ""
    assert stderr == "testing\n"
    try:
        output, stderr = cl(
            "echo foo; exit 2", "localhost", debug=debug, cache=cache,
            proxycmd=proxycmd).run_stderr()
    except CalledProcessError as error:
        assert error.args[0] == 2
        assert error.args[2] == "foo\n"
        assert error.args[3] == ""
        assert len(error.args) == 4
    else:
        assert False
    try:
        output, stderr = cl(
            "echo bar >&2; exit 2", "localhost", debug=debug, cache=cache,
            proxycmd=proxycmd).run_stderr()
    except CalledProcessError as error:
        assert len(error.args) == 4
        assert error.args[0] == 2
        assert error.args[2] == ""
        assert error.args[3] == "bar\n"
    else:
        assert False
    try:
        output, stderr = cl(
            "echo foo; echo bar >&2; exit 2",
            "localhost",
            debug=debug,
            cache=cache,
            proxycmd=proxycmd).run_stderr()
    except CalledProcessError as error:
        assert len(error.args) == 4
        assert error.args[0] == 2
        assert error.args[2] == "foo\n"
        assert error.args[3] == "bar\n"
    else:
        assert False

    # ---
    # run
    # ---

    output = cl("echo testing", "localhost", debug=debug, cache=cache, proxycmd=proxycmd).run()
    assert output == "testing\n"
    output = cl("echo testing >&2", "localhost", debug=debug, cache=cache, proxycmd=proxycmd).run()
    assert output == ""
    try:
        output = cl(
            "echo testing; exit 2", "localhost", debug=debug, cache=cache, proxycmd=proxycmd).run()
    except CalledProcessError as error:
        assert error.args[0] == 2
        # cmd [1] is based on the implementation .. not what we sent
        assert error.args[2] == "testing\n"
        assert len(error.args) == 4
    else:
        assert False


__author__ = 'Christian E. Hopps'
__date__ = 'January 14 2018'
__version__ = '1.0'
__docformat__ = "restructuredtext en"
