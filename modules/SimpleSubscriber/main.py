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
"""Simple subscriber on MSFT Azure Edge Runtime.
"""
import json
import asyncio
import logging
from azure.iot.device.aio import IoTHubModuleClient


async def main():
    """Main method for asyncio.
    """
    # Configuring logging
    log = logging.getLogger('SimpleSuscriber')
    log.setLevel(logging.INFO)

    # Create console logger
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Create logging formatter
    fmt = logging.Formatter(
            '[%(asctime)s] %(name)s::%(levelname)s: %(message)s')

    # Apply all logging pieces
    ch.setFormatter(fmt)
    log.addHandler(ch)

    try:
        # The client object is used to interact with your Azure IoT hub.
        log.info('Initializing IoT Hub module client')
        module_client = IoTHubModuleClient.create_from_edge_environment()
        await module_client.connect()

        log.info('Running')
        while True:
            msg = await module_client.receive_message_on_input('input1')
            meta_data = json.loads(msg.data)
            log.info(f'Received: {json.dumps(meta_data, indent=4)}')
    except Exception as e:
        log.error(f'Error receiving messages: {e}')
    finally:
        await module_client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
