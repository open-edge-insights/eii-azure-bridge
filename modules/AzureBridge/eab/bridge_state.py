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
"""Azure Bridge state singleton.
"""
import os
import json
import asyncio
import logging
import time
import etcd3
from distutils.util import strtobool
from jsonschema import validate
from eab.subscriber import emb_subscriber_listener
from eab.config import *

# Azure Imports
from azure.iot.device.aio import IoTHubModuleClient
from azure.storage.blob import BlobServiceClient

# EII Imports
import eii.msgbus as emb
import cfgmgr.config_manager as cfg
from util.log import configure_logging
from util.util import Util


class BridgeState:
    """Singleton containing the state of the Azure Bridge.

    .. note:: This object assumes it can find a file called,
        "config_schema.json", in the directory the application is executing
        from.
    """
    # Private singleton instance
    _instance = None

    @staticmethod
    def get_instance():
        """Get instance of the BridgeState singleton.

        :return: BridgeState instance
        :rtype: BridgeState
        """
        if BridgeState._instance is None:
            # Initialize first instance of the bridge state
            BridgeState()
        return BridgeState._instance

    def __init__(self):
        """Constructor.

        .. warning:: This should *NEVER* be called directly by the application.
        """
        # Verify initial state
        assert os.path.exists('config_schema.json'), 'Missing config schema'
        assert BridgeState._instance is None, 'BridgeState already initialized'
        BridgeState._instance = self

        # Configure initial logging
        self.log = configure_logging('INFO', __name__, False)

        self.log.info('Reading configuration JSON schema')
        with open('config_schema.json', 'r') as f:
            self.schema = json.load(f)

        # Assign initial state values
        self.loop = asyncio.get_event_loop()
        self.ipc_msgbus_ctxs = {}
        self.tcp_msgbus_ctxs = {}
        self.config_listener = None
        self.subscriber_listeners = None
        self.subscribers = []
        self.config = None  # Saved digital twin

        # Setup Azure Blob connection
        conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if conn_str is not None:
            self.log.info('Azure blob storage ENABLED in Azure bridge')
            self.bsc = BlobServiceClient.from_connection_string(conn_str)
        else:
            self.log.warn('Azure blob storage DISABLED')
            self.bsc = None

        self.log.info('Initializing Azure module client')
        self.module_client = IoTHubModuleClient.create_from_edge_environment()
        self.loop.run_until_complete(self.module_client.connect())

        self.log.info('Getting initial digital twin')
        twin = self.loop.run_until_complete(self.module_client.get_twin())
        self.log.debug('Received initial digital twin')

        self.log.info('Initializing EII config manager')

        try:
            self.config_mgr = cfg.ConfigMgr()
            self.dev_mode = self.config_mgr.is_dev_mode()
            self.app_name = self.config_mgr.get_app_name()
        except Exception as ex:
            self.log.error(f'Exception: {ex}')
            raise ex

        self.log.debug('Finished initializing config manager')

        # Configure the Azure bridge state with its initial state
        self.configure(twin['desired'])

        # Setup twin listener
        self.config_listener = asyncio.gather(config_listener(self))

    def configure(self, config):
        """Configure the Azure Bridge using the given Azure digital
        twin for the module.

        .. warning:: This will clear out any previous state that existed (i.e.
            all subscribers will be stopped)

        :param dict config: Azure IoT Hub digital twin for the Azure Bridge
        """
        self.log.info('Configuring the Azure Bridge')

        # Verify the configuration
        self.log.debug('Validating JSON schema of new configuration')
        validate(instance=config, schema=self.schema)

        # Reset message bus state if needed
        if self.ipc_msgbus_ctxs or self.tcp_msgbus_ctxs:
            # Stop all subscribers
            self.log.debug('Stopping previous subscribers')

            # Clean up the message bus contexts and subscribers
            self._cleanup_msgbus_ctxs()

        # Configure logging
        if 'log_level' in config:
            log_level = config['log_level'].upper()
        else:
            log_level = 'INFO'

        self.log = configure_logging(log_level, __name__, False)

        self.log.info('Getting EII Message Bus configuration')
        ipc_msgbus_config, tcp_msgbus_config = get_msgbus_config(
                self.app_name, self.config_mgr, self.dev_mode)

        self.log.debug(f'Topic msgbus config dict: \nIPC: '
                       f'{ipc_msgbus_config}, \nTCP:{tcp_msgbus_config}')

        # Initialize message bus context
        self.log.info('Initializing EII Message Bus')
        if ipc_msgbus_config:
            for topic, msgbus_config in ipc_msgbus_config.items():
                ipc_msgbus_ctx = emb.MsgbusContext(msgbus_config)
                self.ipc_msgbus_ctxs[topic] = ipc_msgbus_ctx
        if tcp_msgbus_config:
            for topic, msgbus_config in tcp_msgbus_config.items():
                tcp_msgbus_ctx = emb.MsgbusContext(msgbus_config)
                self.tcp_msgbus_ctxs[topic] = tcp_msgbus_ctx

        # Initialize subscribers
        listener_coroutines = []

        try:
            for (in_topic, topic_conf) in config['topics'].items():
                self.log.info(f'Creating subscriber {in_topic}')
                self.log.debug(f'{in_topic} config: {topic_conf}')
                assert 'az_output_topic' in topic_conf, \
                       'Missing az_output_topic'

                if self.bsc is not None and \
                        'az_blob_container_name' in topic_conf:
                    cn = topic_conf['az_blob_container_name']
                else:
                    cn = None

                msgbus_ctx = None
                if in_topic in self.ipc_msgbus_ctxs:
                    msgbus_ctx = self.ipc_msgbus_ctxs[in_topic]
                elif in_topic in self.tcp_msgbus_ctxs:
                    msgbus_ctx = self.tcp_msgbus_ctxs[in_topic]
                else:
                    raise RuntimeError(
                            f'Cannot find {in_topic} msgbus context')

                # Initialize the subcsriber
                subscriber = msgbus_ctx.new_subscriber(in_topic)

                self.subscribers.append(subscriber)
                listener_coroutines.append(emb_subscriber_listener(
                    self, subscriber, topic_conf['az_output_topic'], cn))
        except Exception:
            # Clean up the message bus contexts
            self._cleanup_msgbus_ctxs()

            # Re-raise whatever exception just occurred
            raise

        # Schedule task for C2D Listener
        self.subscriber_listeners = asyncio.gather(*listener_coroutines)

        # Configure EII
        self.log.info('Getting ETCD configuration')

        # NOTE: THIS IS A HACK, AND NEEDS TO BE FIXED IN THE FUTURE
        hostname = 'localhost'

        # This change will be moved to an argument to the function in 2.3
        # This is done now for backward compatibility
        etcd_host = os.getenv('ETCD_HOST')
        if etcd_host is not None and etcd_host != '':
            hostname = etcd_host

        port = os.getenv('ETCD_CLIENT_PORT', '2379')
        if not Util.check_port_availability(hostname, port):
            raise RuntimeError(f'etcd service port: {port} is not up!')

        try:
            if self.dev_mode:
                etcd = etcd3.client(host=hostname, port=port)
            else:
                etcd = etcd3.client(host=hostname, port=port,
                                    ca_cert='/run/secrets/ca_etcd',
                                    cert_key='/run/secrets/etcd_root_key',
                                    cert_cert='/run/secrets/etcd_root_cert')
        except Exception as e:
            self.log.error(f'Exception raised when creating etcd'
                           f'client instance with error: {e}')
            raise e
        resp = etcd.get_all()
        eii_config = {}
        for value, meta in resp:
            try:
                value = json.loads(value.decode('utf-8'))
                key = meta.key.decode('utf-8')
                eii_config[key] = value
            except Exception as e:
                # NOTE: Errors may happen if security is enabled, because the
                # first part is the request's key
                self.log.error(f'{e}')

        self.log.debug('Finding changes in EII configuration')
        new_eii_config = json.loads(config['eii_config'])
        changed_keys, removed_keys = find_root_changes(
                eii_config, new_eii_config)

        self.log.debug(f'Changed service configs: {changed_keys}')
        self.log.debug(f'Removed service configs: {removed_keys}')

        self.log.info('Applying EII configuration')

        self.log.debug('Applying changes to the changed configs')
        for key in changed_keys:
            self.log.debug(f'Pushing config for {key}')
            etcd.put(
                    key, json.dumps(new_eii_config[key], indent=4))
            self.log.debug(f'Successfully pushed config for {key}')

        self.log.debug('Deleting removed service configs')
        for key in removed_keys:
            # NOTE: THIS IS A HACK, AND NEEDS TO BE FIXED IN THE FUTURE
            self.log.debug(f'Removing config for {key}')
            etcd.delete(key)
            self.log.debug(f'Successfully removed config for {key}')

        self.log.info('EII configuration update applied')

        # Save configuration for future comparisons
        self.config = config

    def stop(self):
        """Fully stop the bridge including the configuration listener and all
        subscribers.

        .. note: This is meant to be done at the close of the application
        """
        self.log.info('Stopping the Azure Bridge')

        if self.config_listener is not None:
            self.log.debug('Stopping the config listener')
            self.config_listener.cancel()

        # Clean up the message bus contexts
        self._cleanup_msgbus_ctxs()

        self.log.debug('Disconnecting from Azure IoT Hub client')
        self.loop.run_until_complete(self.module_client.disconnect())

    def _cleanup_msgbus_ctxs(self):
        """Helper function to clean up the message bus contexts stored within
        the bridge state.
        """
        # If the subscriber listeners are running in the asyncio loop stop them
        if self.subscriber_listeners is not None:
            self.log.debug('Stopping all EII subscriber listeners')
            self.subscriber_listeners.cancel()

        # Close existing subscribers
        self.log.debug('Closing all EII subscribers')
        for sub in self.subscribers:
            sub.close()

        # Loop over the IPC and TCP message bus contexts and force their
        # their deletion so any internal state can be cleanup immediately
        if self.ipc_msgbus_ctxs:
            self.log.debug('Cleaning up IPC msgbus context')
            for topic, msgbus_ctx in self.ipc_msgbus_ctxs.items():
                del msgbus_ctx
            self.ipc_msgbus_ctxs = {}

        if self.tcp_msgbus_ctxs:
            self.log.debug('Cleaning up TCP msgbus context')
            for topic, msgbus_ctx in self.tcp_msgbus_ctxs.items():
                del msgbus_ctx
            self.tcp_msgbus_ctxs = {}
