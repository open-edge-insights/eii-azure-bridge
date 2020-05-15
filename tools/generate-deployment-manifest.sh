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

##
## Simple script to build the Azure module containers
##

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

eis_config="../build/provision/config/eis_config.json"
if [ ! -f "$eis_config" ] ; then
    log_fatal "EIS config \"${eis_config}\" does not exist, please provision EIS"
fi

log_info "Populating .env file with EIS .env variables"
python3 ./tools/populate_dotenv.py
check_error "Failed to populate .env with EIS variables"

source ./.env

log_info "Generating deployment template"
if [ "$DEV_MODE" == "true" ] ; then
    python3 ./tools/generate_deployment_template.py --dev-mode $@
    check_error "Failed to generate template"
else
    python3 ./tools/generate_deployment_template.py $@
    check_error "Failed to generate template"
fi


# Generate an Azure Blob Storage account key if the service has been specified
if [[ $@ =~ (^| )AzureBlobStorageonIoTEdge($| ) ]] ; then
    log_info "Generating Azure Blob Storage account key"
    python3 ./tools/generate_azure_blob_storage_key.py
    check_error "Failed to generate Azure Blob Storage account key"
fi

log_info "Populating EIS ETCD pre-load into manifest template"
python3 ./tools/serialize_eis_config.py $1.template.json $eis_config
check_error "Failed to populate EIS configuration into manifest template"

log_info "Generating Azure deployment manifest"
iotedgedev genconfig -f $1.template.json
check_error "Failed to generate Azure deployment manifest"

log_info "Done. Manifest at ./config/$1.amd64.json."
