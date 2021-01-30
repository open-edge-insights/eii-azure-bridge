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
"""Simple helper script to generate an Azure IoT Hub deployment manifest.
"""
import json
import os
import argparse


# Templates location
TEMPLATES_DIR = os.path.join('config', 'templates')
assert os.path.exists(TEMPLATES_DIR), f'Cannot find {TEMPLATES_DIR}'

# List of supported services to add (automatically) to the deployment
# manifest
SUPPORTED_SERVICES = [
    'EIIAzureBridge', 'ia_video_ingestion', 'SimpleSubscriber',
    'AzureBlobStorageonIoTEdge', 'ia_video_analytics'
]

# Parse command line arguments
ap = argparse.ArgumentParser()
ap.add_argument('deployment_name', help='Name of the deployment')
ap.add_argument('services', choices=SUPPORTED_SERVICES, nargs='+',
                help='Services to use in the deployment')
ap.add_argument('-d', '--dev-mode', default=False, action='store_true',
                help='Whether or not services running in dev mode')
args = ap.parse_args()


print('[INFO] Loading base manifest')
with open(os.path.join(TEMPLATES_DIR, 'base.template.json'), 'r') as f:
    base_manifest = json.load(f)


for service in args.services:
    print(f'[INFO] Populating template for {service}')
    fn = os.path.join(TEMPLATES_DIR, f'{service}.template.json')
    with open(fn, 'r') as f:
        template = json.load(f)

    # Add some custom properties based on the selected services
    if service == 'EIIAzureBridge':
        if args.dev_mode:
            # Remove certificate mounts if in dev-mode
            settings = template[service]['settings']
            del settings['createOptions']['HostConfig']['Mounts']
        if 'AzureBlobStorageonIoTEdge' in args.services:
            template[service]['env'] = {
                'AZURE_STORAGE_CONNECTION_STRING': {
                    "value": (
                        'DefaultEndpointsProtocol=https;'
                        'AccountName=$AZ_BLOB_STORAGE_ACCOUNT_NAME;'
                        'AccountKey=$AZ_BLOB_STORAGE_ACCOUNT_KEY;'
                        'BlobEndpoint=http://AzureBlobStorageonIoTEdge:11002/'
                        '$AZ_BLOB_STORAGE_ACCOUNT_NAME')
                },
                'AZ_BLOB_STORAGE_ACCOUNT_KEY': {
                    'value': '$AZ_BLOB_STORAGE_ACCOUNT_KEY'
                }
            }

    if args.dev_mode:
        try:
            # Remove certificate mounts if in dev-mode
            settings = template[service]['settings']
            del settings['createOptions']['HostConfig']['Mounts']
        except KeyError:
            # Passing this KeyError, because it means that there are no mounts
            # to remove for the service in order to run it in dev mode
            pass

    if 'routes' in template:
        r = template['routes']
        modules_content = base_manifest['modulesContent']
        modules_content['$edgeHub']['properties.desired']['routes'].update(r)

    # Populate the template info into the deployment manifest
    edge_agent = base_manifest['modulesContent']['$edgeAgent']
    edge_agent['properties.desired']['modules'][service] = template[service]
    if 'properties.desired' in template:
        props = template['properties.desired']
        base_manifest['modulesContent'][service] = {
            'properties.desired': props
        }

output_fn = f'{args.deployment_name}.template.json'
print(f'[INFO] Saving deployment manifest template to {output_fn}')
with open(output_fn, 'w') as f:
    json.dump(base_manifest, f, indent=4)
print('[INFO] Done.')
