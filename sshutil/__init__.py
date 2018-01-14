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

g_cache = None


def EnableGlobalCaching(timeout=1, max_channels=8):
    """Enable caching of ssh connections for all API calls

    Args:
        timeout - the length of time to keep an unused connection open.
        max_channel - the maximum number of channels to multiplex on a single ssh socket.
    """
    global g_cache
    from .cache import SSHConnectionCache
    g_cache = SSHConnectionCache("SSH global connection cache", timeout, max_channels)


def DisableGlobalCaching():
    """Disable caching of ssh connections for all API calls"""
    global g_cache
    from .cache import SSHNoConnectionCache
    g_cache.flush()
    g_cache = SSHNoConnectionCache("SSH uncached connections")


EnableGlobalCaching()
