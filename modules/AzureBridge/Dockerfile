ARG EIS_VERSION
ARG AZ_CONTAINER_REGISTRY
FROM $AZ_CONTAINER_REGISTRY/ia_eisbase:$EIS_VERSION as ia_eisbase

ARG HOST_TIME_ZONE=""

WORKDIR ${PY_WORK_DIR}

# Setting timezone inside the container
ARG DEBIAN_FRONTEND=noninteractive
RUN echo "$HOST_TIME_ZONE" >/etc/timezone
RUN cat /etc/timezone
RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/${HOST_TIME_ZONE} /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

COPY requirements.txt ./
RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python3.6 get-pip.py

COPY requirements.txt .
RUN pip3 install -r requirements.txt

ARG EIS_UID
ARG EIS_USER_NAME
RUN useradd -r -u ${EIS_UID} -G video ${EIS_USER_NAME}

FROM $AZ_CONTAINER_REGISTRY/ia_common:$EIS_VERSION as common

FROM ia_eisbase

COPY --from=common ${GO_WORK_DIR}/common/libs ${PY_WORK_DIR}/libs
COPY --from=common ${GO_WORK_DIR}/common/util ${PY_WORK_DIR}/util
COPY --from=common ${GO_WORK_DIR}/common/cmake ${PY_WORK_DIR}/common/cmake
COPY --from=common /usr/local/lib /usr/local/lib
COPY --from=common /usr/local/lib/python3.6/dist-packages/ /usr/local/lib/python3.6/dist-packages

COPY . .

CMD ["python3.6", "-u", "main.py"]
