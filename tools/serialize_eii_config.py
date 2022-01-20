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
"""Python script to serialize the EII ETCD pre-load JSON file into the Azure
IoT Edge deployment manifest template.
"""
import os
import json
import argparse
import sys


# Parse command line arguments
ap = argparse.ArgumentParser()
ap.add_argument('manifest', help='Azure manifest template')
ap.add_argument('config', help='EII pre-load configuration path')
args = ap.parse_args()

# Verify the input files exist
if not os.path.exists(args.config):
    raise AssertionError('{} does not exist'.format(args.config))
if not os.path.exists(args.manifest):
    raise AssertionError('{} does not exist'.format(args.manifest))

print('[INFO] Populating EII configuration into Azure manifest')

def is_safe_path(basedir, path, follow_symlinks=True):
    # resolves symbolic links
    if follow_symlinks:
        matchpath = os.path.realpath(path)
    else:
        matchpath = os.path.abspath(path)
    return basedir == os.path.commonpath((basedir, matchpath))

# Load JSON files
with open(args.config, 'r') as f:
   config = json.load(f)

with open(args.manifest, 'r') as f:
    manifest = json.load(f)

# Serialize and populate the manifest
config_str = json.dumps(config)
eii_azure_bridge = manifest['modulesContent']['AzureBridge']
eii_azure_bridge['properties.desired']['eii_config'] = config_str

if is_safe_path(os.getcwd(), args.manifest):
    with open(args.manifest, 'w') as f:
        json.dump(manifest, f, indent=4)

print('[INFO] Azure manifest populated')
