# Copyright (c) 2020 Intel Corporation.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM,OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
"""EII Azure Bridge digital twin configuration listener and utilities.
"""
import os
import json
import logging
import traceback as tb
from dictdiffer import diff, patch, swap, revert
from util.util import Util


async def config_listener(bs):
    """Listener for changes in the EII Azure Bridge Azure IoT Edge runtime
    module digital twin changes.

    :param eab.bridge_state.BridgeState bs: Bridge state instance
    """
    log = logging.getLogger(__name__)

    while True:
        try:
            log.debug('Waiting to receive updated twin patch')
            data = \
                await bs.module_client.receive_twin_desired_properties_patch()
            log.debug(f'Updated Twin: {json.dumps(data, indent=4)}')

            log.info('Received updated configuration, applying now...')
            bs.configure(data)
        except AssertionError as ex:
            log.error(f'Invalid twin: {ex}')
        except Exception as ex:
            log.error(f'Unexpected error: {ex},\n{tb.format_exc()}')


def find_root_changes(orig, new):
    """Discover all of the root keys which have underlying changes.

    :param dict orig: Original version of the dictionary
    :param dict new: New version of the dictionary
    :return: 2-tuple of two lists with (changed root keys, removed root keys)
    :rtype: tuple
    """
    # Take changes between the two dictionaries
    changes = diff(orig, new)
    changed_keys = []
    removed_keys = []

    # Find unique list of root keys which have underlying changes
    for change_type, key_info, mod in changes:
        if change_type == 'change' or change_type == 'add':
            if isinstance(key_info, (list, tuple,)):
                key = key_info[0]
            else:
                key = key_info
            if key == '':
                continue
            base_key = key.split('.')[0]
            if base_key not in changed_keys:
                changed_keys.append(base_key)
        else:
            if key_info != '':
                if isinstance(key_info, (list, tuple,)):
                    key = key_info[0]
                else:
                    key = key_info
                if key not in changed_keys:
                    changed_keys.append(key)
            else:
                for key, value in mod:
                    if key in orig and key not in removed_keys:
                        removed_keys.append(key)

    return (changed_keys, removed_keys,)


def get_msgbus_config(app_name, config_mgr, dev_mode):
    """Helper method to construct the EII Message Bus configuration dictionary.

    :param str app_name: EIIAzureBridge app name
    :param config_mgr: Config Manager Instance
    :param bool dev_mode: Flag for whether or not execution is in dev mode
    :return: Tuple of (IPC topic->msgbus config dict,
                       TCP topic->msgbus config dict)
    :rtype: tuple
    """
    num_of_subscribers = config_mgr.get_num_subscribers()

    ipc_msgbus_config = {}
    tcp_msgbus_config = {}

    for index in range(num_of_subscribers):
        # Fetching subscriber element based on index
        sub_ctx = config_mgr.get_subscriber_by_index(index)
        # Fetching msgbus config of subscriber
        msgbus_cfg = sub_ctx.get_msgbus_config()
        mode = msgbus_cfg['type']
        topics = sub_ctx.get_topics()
        for topic in topics:
            if mode == 'zmq_ipc':
                ipc_msgbus_config[topic] = msgbus_cfg
            elif mode == 'zmq_tcp':
                tcp_msgbus_config[topic] = msgbus_cfg
            else:
                raise RuntimeError(f'Unknown msgbus type: {mode}')
    return ipc_msgbus_config, tcp_msgbus_config
