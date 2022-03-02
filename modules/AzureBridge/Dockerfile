# Copyright (c) 2020 Intel Corporation.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

ARG EII_VERSION
ARG DOCKER_REGISTRY
ARG ARTIFACTS="/artifacts"
ARG EII_UID
ARG EII_USER_NAME
ARG UBUNTU_IMAGE_VERSION
FROM ia_eiibase:$EII_VERSION as base
FROM ia_common:$EII_VERSION as common

FROM base as builder
LABEL description="Azure Bridge image"

ARG ARTIFACTS
WORKDIR /app

# Uninstalling python packages installed at /usr/lib/python3/dist-packages
# in ia_eiibase image as some of them were considered while
# installing the app's requirements.txt below
RUN pip3 freeze | xargs pip3 uninstall -y

COPY requirements.txt .
RUN pip3 install --user -r requirements.txt


ARG CMAKE_INSTALL_PREFIX

# Install libzmq
RUN rm -rf deps && \
    mkdir -p deps && \
    cd deps && \
    wget -q --show-progress https://github.com/zeromq/libzmq/releases/download/v4.3.4/zeromq-4.3.4.tar.gz -O zeromq.tar.gz && \
    tar xf zeromq.tar.gz && \
    cd zeromq-4.3.4 && \
    ./configure --prefix=${CMAKE_INSTALL_PREFIX} && \
    make install

# Install cjson
RUN rm -rf deps && \
    mkdir -p deps && \
    cd deps && \
    wget -q --show-progress https://github.com/DaveGamble/cJSON/archive/v1.7.12.tar.gz -O cjson.tar.gz && \
    tar xf cjson.tar.gz && \
    cd cJSON-1.7.12 && \
    mkdir build && cd build && \
    cmake -DCMAKE_INSTALL_INCLUDEDIR=${CMAKE_INSTALL_PREFIX}/include -DCMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX} .. && \
    make install

COPY --from=common ${CMAKE_INSTALL_PREFIX}/lib ${CMAKE_INSTALL_PREFIX}/lib
COPY --from=common ${CMAKE_INSTALL_PREFIX}/include ${CMAKE_INSTALL_PREFIX}/include

COPY . .

FROM ubuntu:$UBUNTU_IMAGE_VERSION as runtime

# Setting python env
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-distutils python3-minimal python3-setuptools  && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

ARG EII_UID
ARG EII_USER_NAME
RUN adduser --quiet --disabled-password ${EII_USER_NAME}
ARG ARTIFACTS
ARG CMAKE_INSTALL_PREFIX
ENV PYTHONPATH $PYTHONPATH:/app/.local/lib/python3.8/site-packages:/app:/app/.local/lib/python3.8/dist-packages
COPY --from=builder ${CMAKE_INSTALL_PREFIX}/lib ${CMAKE_INSTALL_PREFIX}/lib
COPY --from=builder ${CMAKE_INSTALL_PREFIX}/include ${CMAKE_INSTALL_PREFIX}/include
COPY --from=builder /root/.local/lib .local/lib
COPY --from=builder /app .

COPY --from=common /eii/common/util/*.py util/
COPY --from=common /root/.local/lib .local/lib

RUN chown -R ${EII_UID} .local/lib/python3.8

ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:${CMAKE_INSTALL_PREFIX}/lib
ENV PATH $PATH:/app/.local/bin

HEALTHCHECK NONE

CMD ["python3", "-u", "main.py"]
