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
"""Helper script to populate the .env file from the docker_setup/.env file.
"""
import os
import re


# List of variables which need to be populated from the parent .env file
VARS = [
    'EII_VERSION',
    'DEV_MODE',
    "SOCKET_DIR",
    'PROFILING_MODE',
    'EII_USER_NAME',
    'EII_UID',
    'ETCD_HOST',
    'ETCD_PREFIX',
    'ETCDROOT_PASSWORD',
    'ETCD_DATA_DIR',
    'ETCD_CLIENT_PORT',
    'ETCD_PEER_PORT',
    'SOCKET_DIR',
    'EII_INSTALL_PATH',
    'DOCKER_REGISTRY',
    'HOST_IP'
]

# Paths to .env files
parent_env_fn = os.path.join('..', 'build', '.env')
this_env_fn = '.env'

# Verify required files exist
assert os.path.exists(parent_env_fn), f'Cannot find {parent_env_fn} file'
assert os.path.exists(this_env_fn), f'Cannot find {this_env_fn}'

# Read .env files
with open(parent_env_fn, 'r') as f:
    parent_env = list(f.readlines())

with open(this_env_fn, 'r') as f:
    this_env = f.read()

# Parse needed values from the parent_env file
for var in VARS:
    try:
        for line in parent_env:
            # Make sure the line starts with to make sure we don't accidentally
            # match with a comment in the ../build/.env file
            if line.startswith(var):
                # Get value of the var
                res = re.findall(f'(?:{var}=)(.+|)', line)
                if len(res) > 0:
                    value = res[0]
    except IndexError as e:
        # A value wasn't set, so set it to nothing
        value = ''

    # Check if the variable already exists in the .env
    if re.findall(f'{var}=(.+|)', this_env):
        # Place the value in this_env
        this_env = re.sub(
                f'{var}=(.+|)',
                f'{var}={value}',
                this_env)
    else:
        this_env += f'\n{var}={value}'

    if var == 'DOCKER_REGISTRY':
        # Need to populate special variable for the Azure Container Registry
        # which omits the "/" in the DOCKER_REGISTRY variable
        # Check if the variable already exists in the .env
        if re.findall(f'AZ_CONTAINER_REGISTRY=.+', this_env):
            # Place the value in this_env
            this_env = re.sub(
                    f'AZ_CONTAINER_REGISTRY=.+',
                    f'AZ_CONTAINER_REGISTRY={value[:-1]}',
                    this_env)
        else:
            this_env += f'\nAZ_CONTAINER_REGISTRY={value[:-1]}'


# Write the new .env file contents for the Azure Bridge
with open(this_env_fn, 'w') as f:
    f.write(this_env)
