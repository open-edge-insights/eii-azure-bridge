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
"""Unit tests for utility functions in the eab.config module.
"""
import os
import unittest
from dictdiffer import diff
from eab.config import *


class MockConfigManagerClient:
    """Mock object for the configuration manager.

    .. note:: This only mocks the APIs of the configuration manager ETCD client
        which the configuration utilities in the EII Azure Bridge uses.
    """
    def __init__(self, mock_config):
        """Constructor.

        :param dict mock_config: Mock configuration to pull values from
        """
        self.mock_config = mock_config

    def GetConfig(self, key):
        """Mocked :code:`GetConfig()` method.
        """
        return self.mock_config[key]


class TestConfigUtils(unittest.TestCase):
    """Unit tests for configuration utility functions.
    """
    def test_find_root_changes(self):
        """Test the :code:`eab.config.find_root_changes()` utility function.

        .. note:: The find_root_changes() method does not report all nested
            changes. Meaning, if a key is removed from a nested dict, then the
            top most level key will be in the changed_keys return value. You
            will not get the removed key from the nested key in the list of
            removed keys. The method tested here only reports removed top
            level keys, and the top level key of an item which has been
            changed.
        """
        # Defining data to use when testing
        base = {
            'test': 'test',
            'list': ['test', 123],
            'dict': {
                'nested_test': 'test',
                'nested_list': ['test', 123],
                'nested_dict': {
                    'nested_nested_test': 'test',
                }
            },
            'dict2': {
                'nested_test': 'test',
                'nested_list': ['test', 123],
                'nested_dict': {
                    'nested_nested_test': 'test',
                }
            }
        }

        # Test removed top level key and top level list item
        changed = {
            'list': [123],
            'dict': {
                'nested_test': 'test',
                'nested_list': ['test', 123],
                'nested_dict': {
                    'nested_nested_test': 'test',
                }
            },
            'dict2': {
                'nested_test': 'test',
                'nested_list': ['test', 123],
                'nested_dict': {
                    'nested_nested_test': 'test',
                }
            }
        }
        changed_keys, removed_keys = find_root_changes(base, changed)
        self.assertEqual(changed_keys, ['list'])
        self.assertEqual(removed_keys, ['test'])

        # Test modified nested list
        changed = {
            'test': 'test',
            'list': ['test', 123],
            'dict': {
                'nested_list': ['test', 123],
                'nested_dict': {
                    'nested_nested_test': 'test',
                }
            },
            'dict2': {
                'nested_test': 'test',
                'nested_list': ['test', 123],
                'nested_dict': {
                    'nested_nested_test': 'test',
                }
            }
        }
        changed_keys, removed_keys = find_root_changes(base, changed)
        self.assertEqual(changed_keys, ['dict'])
        self.assertEqual(removed_keys, [])

        # Test modified nested list and removed high level
        changed = {
            'test': 'test',
            'list': ['test', 123],
            'dict': {
                'nested_dict': {
                    'nested_nested_test': 'test',
                }
            }
        }
        changed_keys, removed_keys = find_root_changes(base, changed)
        self.assertEqual(changed_keys, ['dict'])
        self.assertEqual(removed_keys, ['dict2'])

    def test_get_msgbus_config(self):
        """Test the :code:`eab.config.get_msgbus_config()` method.
        """
        app_name = 'EIIAzureBridge'

        # Set environmental variables for retrieving TCP and IPC configurations
        # This simulates connections to both VI and VA
        os.environ['SubTopics'] = ('VideoIngestion/camera1_stream,'
                                   'VideoAnalytics/camera1_stream_results')
        os.environ['camera1_stream_cfg'] = 'zmq_ipc,/EII/sockets'
        os.environ['camera1_stream_results_cfg'] = 'zmq_tcp,127.0.0.1:65013'

        # Define mock production EII config
        prod_config = {
            '/Publickeys/VideoAnalytics': 'TEST-VA-CLIENT-KEY',
            f'/Publickeys/{app_name}': 'TEST-APP-CLIENT-KEY',
            f'/{app_name}/private_key': 'TEST-APP-CLIENT-SECRET'
        }

        # Define mock dev mode EII config
        # This is empty, because the util should not try to retrieve anything
        # from the config manager in this case
        dev_config = {}

        # Expected message bus configurations to receive

        # NOTE: IPC config should be the same for prod and dev mode
        expected_ipc_config = {
            'type': 'zmq_ipc',
            'socket_dir': '/EII/sockets'
        }

        expected_prod_tcp_config = {
            'type': 'zmq_tcp',
            'camera1_stream_results': {
                'host': '127.0.0.1',
                'port': 65013,
                'server_public_key': prod_config['/Publickeys/VideoAnalytics'],
                'client_public_key': prod_config[f'/Publickeys/{app_name}'],
                'client_secret_key': prod_config[f'/{app_name}/private_key']
            }
        }

        expected_dev_tcp_config = {
            'type': 'zmq_tcp',
            'camera1_stream_results': {
                'host': '127.0.0.1',
                'port': 65013
            }
        }

        # Create mock config manager clients
        prod_config_client = MockConfigManagerClient(prod_config)
        dev_config_client = MockConfigManagerClient(dev_config)

        # Do prod mode test
        ipc_msgbus_config, tcp_msgbus_config = get_msgbus_config(
                app_name, prod_config_client, False)

        result = list(diff(ipc_msgbus_config, expected_ipc_config))
        self.assertEqual(result, [])

        result = list(diff(tcp_msgbus_config, expected_prod_tcp_config))
        self.assertEqual(result, [])

        # Do dev mode test
        ipc_msgbus_config, tcp_msgbus_config = get_msgbus_config(
                app_name, dev_config_client, True)

        result = list(diff(ipc_msgbus_config, expected_ipc_config))
        self.assertEqual(result, [])

        result = list(diff(tcp_msgbus_config, expected_dev_tcp_config))
        self.assertEqual(result, [])
