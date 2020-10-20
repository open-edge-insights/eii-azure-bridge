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

if [[ $# -eq 1 ]] ; then
    deployment=$1
    pat='(.+)(:?\.template\.json)'
    [[ $deployment =~ $pat ]]
    deployment_name="${BASH_REMATCH[1]}"
else
    deployment="deployment.template.json"
    deployment_name="deployment"
fi

log_info "Loading environmental variables"
source ./.env
check_error "Failed to source environment"

# Creating some required directories by EIS

eis_config="../build/provision/config/eis_config.json"
if [ ! -f "$eis_config" ] ; then
    log_fatal "EIS config \"${eis_config}\" does not exist, please provision EIS"
fi

log_info "Populating .env file with EIS .env variables"
python3 ./tools/populate_dotenv.py
check_error "Failed to populate .env with EIS variables"

log_info "Generating deployment manifest from \"$deployment\" template"
iotedgedev genconfig -f $deployment
check_error "Failed to generate deployment manifest"

log_info "Populating EIS configuration into Azure manifest"
python3 ./tools/serialize_eis_config.py ./$deployment $eis_config
check_error "Failed to populate EIS configuration into Azure manifest"

log_info "Running simulator"
sudo -H -E -u $USER iotedgehubdev start -d ${PWD}/config/$deployment_name.amd64.json -v
check_error "Failed to run simulator"
