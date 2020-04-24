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
"""EIS Azure Bridge digital twin configuration listener and utilities.
"""
import json
import logging
import traceback as tb
from dictdiffer import diff, patch, swap, revert
from util.msgbusutil import MsgBusUtil
from util.util import Util


async def config_listener(bs):
    """Listener for changes in the EIS Azure Bridge Azure IoT Edge runtime
    module digital twin changes.

    :param eab.bridge_state.BridgeState bs: Bridge state instance
    """
    log = logging.getLogger(__name__)

    while True:
        try:
            log.debug('Waiting to receive updated twin patch')
            data = await bs.module_client.receive_twin_desired_properties_patch()
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


def get_msgbus_config(config_client, dev_mode):
    """Helper method to construct the EIS Message Bus configuration dictionary.

    :param config_client: EIS Config Manager client
    :param bool dev_mode: Flag for whether or not execution is in dev mode
    :return: Message bus configuration
    :rtype: dict
    """
    topics = MsgBusUtil.get_topics_from_env('sub')

    # Currently only IPC communication is supported, this will change in the
    # future
    msgbus_config = {'type': 'zmq_ipc'}

    for topic in topics:
        publisher, topic = topic.split('/')
        cfg = MsgBusUtil.get_messagebus_config(
                topic, 'sub', publisher, config_client, dev_mode)
        assert cfg['type'] == 'zmq_ipc', 'Only IPC communication is supported'
        if topic in cfg:
            msgbus_config[topic] = cfg[topic]

        # Assuming they all have the same socket directory for now, since the
        # bridge will only have one message bus context for now
        if 'socket_dir' not in msgbus_config:
            msgbus_config['socket_dir'] = cfg['socket_dir']

    return msgbus_config
