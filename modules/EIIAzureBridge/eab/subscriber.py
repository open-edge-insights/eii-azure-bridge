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
"""EII Azure Bridge EMB subscriber async functions.
"""
import json
import asyncio
import logging
import traceback as tb

# Azure Imports
from azure.iot.device import Message
from azure.core.exceptions import ResourceExistsError


async def subscriber_recv(loop, subscriber):
    """Receive a message from a subscriber on the EII Message Bus.

    :param loop: asyncio loop
    :param subscriber: EII Message Bus Subscriber
    """
    recv = loop.run_in_executor(None, subscriber.recv)
    msg = await recv
    return msg


async def upload_frame(bs, container_name, meta_data, blob):
    """Upload a frame into Azure Blob Storage
    """
    loop = asyncio.get_event_loop()
    log = logging.getLogger(container_name)
    ext = 'raw'

    if 'encoding_type' in meta_data:
        ext = meta_data['encoding_type']

    blob_name = f'{meta_data["img_handle"]}.{ext}'

    log.debug(f'Creating blob client for {blob_name}')
    blob_client = \
        bs.bsc.get_blob_client(container=container_name, blob=blob_name)

    log.info(f'Uploading blob {blob_name}')
    # TODO: Add thread pool for these uploads (WE'RE GOING FOR SPEED!)
    upload = loop.run_in_executor(None, blob_client.upload_blob, blob)
    await upload


async def upload_frame_done(fut):
    """Upload frame done callback

    :param asyncio.Future fut: Future for uploading the frame
    """
    ex = fut.exception()
    if ex is not None:
        log = logging.getLogger(__name__)
        log.error(f'Failed to upload frame to Azure Blob Storage: {ex}')


async def emb_subscriber_listener(bs, subscriber, output_name, container_name):
    """EII Message Bus asyncio subscriber listener.

    This will resend the meta-data received from EII onto the MSFT IoT Edge
    Runtime bus using the given output name. The output name must be a
    specified output route for the module when deployed via the IoT Edge
    Runtime.

    :param subscriber: EII Message Bus subscriber
    :param container_name: Name of the Azure Blob container
    :param output_name: Output stream name
    """
    # Get asyncio loop handle
    loop = asyncio.get_event_loop()
    log = logging.getLogger(output_name)
    save_blobs = False

    log.info(f'{output_name} subscriber starting...')

    if bs.bsc is not None and container_name is not None:
        log.debug(
            f'Creating blob storage container: {container_name}')
        save_blobs = True
        try:
            container_client = bs.bsc.get_container_client(container_name)
            container_client.create_container()
        except ResourceExistsError:
            # Pass this error, its okay if it already exists
            pass

    try:
        # Loop forever receiving messages
        while True:
            log.debug('Waiting for message from the EII Message Bus')
            msg = await subscriber_recv(loop, subscriber)

            meta = msg.get_meta_data()
            blob = msg.get_blob()

            if meta is None and blob is not None:
                # This listener can only handle messages which contain
                # meta-data that is to be passed on to the MSFT IoT Edge
                # Runtime bus
                log.error('Received a message without meta-data')
                break

            log.debug(f'Received: {meta}')

            if save_blobs and blob is not None:
                try:
                    fut = asyncio.ensure_future(
                        upload_frame(bs, container_name, meta, blob),
                        loop=loop)
                    fut.add_done_callback(upload_frame_done)
                except Exception:
                    log.error(f'Failed to upload blob: {tb.format_exc()}')

            if blob is not None:
                # Free the blob early (might be a lot of memory)
                del blob

            # Package the meta-data into a message object and send it
            log.debug('Re-sending message over the IoT Edge runtime bus')
            output_msg = Message(json.dumps(meta))
            await bs.module_client.send_message_to_output(
                    output_msg, output_name)
    except asyncio.CancelledError:
        log.info('Subscriber routine cancelled')
    except Exception:
        log.error(f'Unexpected error in listener: {tb.format_exc()}')
