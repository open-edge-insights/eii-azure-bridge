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
"""Helper script to generate Azure Blob Storage account key in the .env file.
"""
import re
import os
import base64


# Verify the .env file exists
if not os.path.exists('.env'):
    raise AssertionError('Cannot find the ".env" file')

print('[INFO] Generating random 64-byte base64 encoded account key')

# Generate a random 64-byte string
rand_str = os.urandom(64)

# Encode the random string as base64 and get it's UTF-8 representation
account_key = base64.b64encode(rand_str).decode('utf-8')

# Read the current contents of the .env file
with open('.env', 'r') as f:
    contents = f.read()

# Find and replace the current value of the AZ_BLOB_STORAGE_ACCOUNT_KEY
new_contents = re.sub(
        r'AZ_BLOB_STORAGE_ACCOUNT_KEY=(.+|)',
        f'AZ_BLOB_STORAGE_ACCOUNT_KEY=\'{account_key}\'',
        contents, flags=re.M)

# Save the new contents of the .env file
with open('.env', 'w') as f:
    f.write(new_contents)

print('[INFO] Done.')
