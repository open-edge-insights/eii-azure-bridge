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
from azure.iot.device.aio import IoTHubModuleClient


async def main():
    """Main method for asyncio.
    """
    # The client object is used to interact with your Azure IoT hub.
    print('[INFO] Initializing IoT Hub module client')
    module_client = IoTHubModuleClient.create_from_edge_environment()
    await module_client.connect()

    try:
        print('[INFO] Running')
        while True:
            msg = await module_client.receive_message_on_input('input1')
            meta_data = json.loads(msg.data)
            print(f'[INFO] Received: {json.dumps(meta_data, indent=4)}')
    except Exception as e:
        print(f'[ERROR] {e}')
    finally:
        await module_client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
