#!/bin/bash

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

RED='\033[0;31m'
YELLOW="\033[1;33m"
GREEN="\033[0;32m"
NC='\033[0m' # No Color

function log_warn() {
    echo -e "${YELLOW}WARN: $1 ${NC}"
}

function log_info() {
    echo -e "${GREEN}INFO: $1 ${NC}"
}

function log_error() {
    echo -e "${RED}ERROR: $1 ${NC}"
}

function log_fatal() {
    echo -e "${RED}FATAL: $1 ${NC}"
    exit -1
}

function check_error() {
    if [ $? -ne 0 ] ; then
        log_fatal "$1"
    fi
}

reqs_file="dev-requirements.txt"
if [ ! -f "$reqs_file" ] ; then
    reqs_file="./tools/$reqs_file"
fi

log_info "Installing Python dependencies"
pip3 install -r $reqs_file
check_error "Failed to install Python dependencies"

CURL=`which curl`
if [ "$CURL" == "" ] ; then
    log_info "Installing curl"
    apt install curl
    check_error "Failed to install curl"
fi

log_info "Installing azure-cli"
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
check_error "Failed to install azure-cli"

log_info "Attempting to login to Azure"
az login
check_error "Failed to login to Azure"

log_info "Installing azure-iot extension"
az extension add --name azure-iot
check_error "Failed to install azure-iot Azure CLI extension"

log_info "Installing azure-cli-iot-ext extension"
az extension add --name azure-cli-iot-ext
check_error "Failed to install azure-cli-iot-ext Azure CLI extension"
