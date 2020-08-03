# EIS Azure Bridge

> **NOTE:** The source code for this project must be placed under the `IEdgeInsights`
> directory in the source code for EIS for the various scripts and commands in
> this README to work.

The EIS Azure Bridge serves as a connector between EIS and the Microsoft
Azure IoT Edge Runtime ecosystem. It does this by allowing the following
forms of bridging:

* Publishing of incoming data from EIS onto the Azure IoT Edge Runtime bus
* Storage of incoming images from the EIS video analytics pipeline into a
    local instance of the Azure Blob Storage service
* Translation of configuration for EIS from the Azure IoT Hub digital twin
    for the bridge into ETCD via the EIS Configuration Manager APIs

This code base is structured as an Azure IoT Edge Runtime module. It includes:

* Deployment templates for deploying the EIS video analytics pipeline with the
    bridge on top of the Azure IoT Edge Runtime
* The EIS Azure Bridge module
* A simple subscriber on top of the Azure IoT Edge Runtime for showcasing the
    end-to-end transmission of data
* Various utilities and helper scripts for deploying and developing on the
    EIS Azure Bridge

The following sections will cover the configuration/usage of the EIS Azure
Bridge, the deployment of EIS on the Azure IoT Edge Runtime, as well as the
usage of the tools and scripts included in this code base for development.

> **NOTE:** The following sections assume an understanding of the configuration
> for EIS. It is recommended that you read the main README and User Guide for
> EIS prior to using this service.

## Pre-Requisites / Setup

To use and develop with the EIS Azure Bridge there are a few steps which must
be taken to configure your environment. The setup must be done to configure
your Azure Cloud account, your development system, and also the node which
you are going to deploy the EIS Azure Bridge on.

The following sections cover the setup for the first two environments listed.
Setting up your system for a single-node deployment will be covered in the
[Single-Node Azure IoT Edge Deployment](#single-node-dep) section below.

> **NOTE:** When you deploy with Azure IoT Hub you will also need to configure
> the Azure IoT Edge Runtime and EIS on your target device.

### <a name="az-cloud-setup"></a>Azure Cloud Setup

Prior to using the EIS Azure Bridge there are a few cloud services in Azure
which must be initialized.

Primarily, you need an Azure Containter Registry instance, an Azure IoT Hub,
as well as an Azure IoT Device. Additionally, if you wish to use the sample ONNX
UDF in EIS to download a ML/DL model from AzureML, then you must follow a few
steps to get this configured as well. For these steps, see the [Setting up AzureML](#setting-up-azureml)
section below.

To create these instances, follow the guides provided by Microsoft below:

> **NOTE:** In the quickstart guides below it is recommended that you create an
> Azure Resource Group. This is a good practice as it makes for easy clean up
> of your Azure cloud environment.

* [Create Azure Container Registry](https://docs.microsoft.com/en-us/azure/container-registry/container-registry-get-started-portal)
* [Create Azure IoT Hub](https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-create-through-portal)
* [Register an Azure IoT Device](https://docs.microsoft.com/en-us/azure/iot-edge/how-to-register-device)

> **IMPORTANT:**
> In the tutorials above you will receive credentials/connection strings for your
> Azure Container Registry, Azure IoT Hub, and Azure IoT Device. Save these for
> later, as they will be important for setting up your development and single node
> deployment showcased in this README.

All of the tutorials provided above provide options for creating these instances
via Visual Studio Code, the Azure Portal, or the Azure CLI. If you wish to use
the Azure CLI, it is recommended that you follow the Development System Setup
instructions below.

#### Setting up AzureML

To use the sample EIS ONNX UDF, you must do the following:

1. Create an AzureML Workspace (see [these](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-manage-workspace)
    instructions provided by Microsoft)
2. Configure Service Principle Authentication on your AzureML workspace by following
    instructions provided [here](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-setup-authentication#set-up-service-principal-authentication)

**IMPORTANT**

During the setup process provided for step 2 above, you will run a command similar
to the following:

```sh
$ az ad sp create-for-rbac --sdk-auth --name ml-auth
```

After executing this command you will see a JSON blob printed to your console
window. Save the `clientId`, `clientSecret`, `subscriptionId`, and `tenantId`
for configuring the sample ONNX EIS UDF later.

##### Pushing a Model to AzureML

If you already have an ONNX model you wish to push to your AzureML Workspace, then
follow [these instructions](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-deploy-existing-model)
to push your model.

If you do not have a model, and want an easy model to use, follow
[this](https://notebooks.azure.com/azureml/projects/azureml-getting-started/html/how-to-use-azureml/deployment/onnx/onnx-modelzoo-aml-deploy-resnet50.ipynb)
notebook provided my Microsoft to train a simple model to push to your AzureML Workspace.

Also, you can find pre-trained models in the [ONNX Model Zoo](https://github.com/onnx/models).

### <a name="dev-sys-setup"></a>Development System Setup

The development system will be used for the following actions:

* Building and pushing the EIS containers (including the bridge) to your Azure Container Registry
* Creating your Azure IoT Hub deployment manifest
* Deploying your manifest to a single node

For testing purposes, your development system can serve to do the actions detailed
above, as well as being the device you use for your single-node deployment. This
should not be done in a production environment, but it can be helpful when
familiarizing yourself with the EIS Azure Bridge.

First, setup your system for building EIS. To do this, follow the instructions
detailed in the main EIS README and the EIS User Guide. At the end, you should
have installed Docker, Docker Compose, and other EIS Python dependencies for
the EIS Builder script in the `../build/` directory.

Once this is completed, install the required components to user the Azure CLI
and development tools. The script `./tools/install-dev-tools.sh` automates this
process. To run this script, execute the following command:

```sh
$ sudo -H -E -u ${USER} ./tools/install-dev-tools.sh
```

> **NOTE:** The `-u ${USER}` flag above allows the Azure CLI to launch your
> browser (if it can) so you can login to your Azure account.

> **NOTE:** Occasionally, pip's local cache can get corrupted. If this happens,
> pip may `SEGFAULT`. In the case that this happens, delete the `~/.local` directory
> on your system and re-run the script mentioned above. You may consider creating
> a backup of this directory just in case.

While running this script you will be prompted to sign-in to your Azure
account so you can run commands from the Azure CLI that interact with your
Azure instance.

This script will install the following tools:

* Azure CLI
* Azure CLI IoT Edge/Hub Extensions
* Azure `iotedgehubdev` development tool
* Azure `iotedgedev` development tool

Next, login to your Azure Container Registry with the following command:

```sh
$ az acr login --name <ACR Name>
```

> **NOTE:** Fill in `<ACR Name>` with the name of your Azure Container Registry

**IMPORTANT NOTE:**

Please see the list of supported services at the end of this README for the
services which can be pushed to an ACR instance. Not all EIS services are
supported by and validated to work with the EIS Azure Bridge.

## <a name="eis-build-push"></a>Build and Push EIS Containers

> **NOTE:** By following the steps below, the EIS Azure Bridge and Simple
> Subscriber Azure IoT Modules will be pushed to your ACR instance as well.

After setting up your development system, build and push the EIS containers
to your Azure Contianer Registry instance. Note that the EIS Azure Bridge only
supports a few of the EIS services currently. Before building and pushing your
EIS containers, be sure to look at the [Supported EIS Services](#supported-eis-services)
section below, so as to not build/push uneeded containers to your registry.

To do this go to the `../build/` directory in the EIS source code, modify the
`DOCKER_REGISTRY` variable in the `../build/.env` file to point to your Azure
Container Registry.

Next, execute the following commands:

```sh
$ python3 eis_builder.py -f video-streaming-azure.yml
$ docker-compose build
$ docker-compose push
```

For more detailed instructions on this process, see the EIS README and User Guide.

## <a name="single-node-dep"></a>Single-Node Azure IoT Edge Deployment

> **NOTE:** Outside of the Azure ecosystem, EIS can be deployed and communicate
> across nodes. In the Azure IoT Edge ecosystem this is not possible with EIS.
> All EIS services must be running on the same edge node. However, you can
> deploy EIS on multiple nodes, but intercommunication between the nodes will
> not work.

> **IMPORTANT NOTE:**
> If you are using TCP communication between VI or VA and the EIS Azure Bridge,
> modify the `Clients` environmental variable in your `docker-compose.yml` file use
> while provisioning EIS to include `EISAzureBridge` so that the connection can be
> encrypted/authenticated.

In the Azure IoT ecosystem you can deploy to single-nodes and you can do bulk
deployments. This section will cover how to deploy the EIS Azure Bridge and
associated EIS services to a single Linux edge node. For more details on deploying
modules at scale with the Azure IoT Edge Runtime, see
[this guide](https://docs.microsoft.com/en-us/azure/iot-edge/how-to-deploy-monitor)

Note that this section will give a high-level overview of how to deploy the
modules with the Azure CLI. For more information on developing and deploying
Azure modules, see [this guide](https://docs.microsoft.com/en-us/azure/iot-edge/tutorial-develop-for-linux).

The deloyment of the Azure IoT Edge and the EIS modules can be broken down into
the following steps:

1. Provisioning
2. Configuring EIS
3. Configuring Azure IoT Deployment Manifest
4. Deployment

Prior to deploying a single Azure IoT Edge node you must have already
configured your Azure cloud instance (see instructions in the [Azure Cloud Setup](#az-cloud-setup)
section). Additionally, you need to have already built and pushed the EIS services to your
Azure Container Registry (follow the instructions in the [Build and Push EIS Containers](#eis-build-push)
section).

Provided you have met these two prerequisites, follow the steps below to do a
single node deployment with the EIS Azure Bridge on the Azure IoT Edge Runtime.

### Step 1 - Provisioning

The provisioning must take place on the node you wish to deploy your Azure IoT
Edge modules onto.

> **NOTE:** This may be your development system, which was setup earlier. Keep in
> mind, however, that having your system setup as a development system and a
> targeted node for a single-node deployment should never be done in production.

First, you must then install the Azure IoT Edge Runtime on your target deployment
system. To do that, follow the instructions provided by Microsoft in
[this guide](https://docs.microsoft.com/en-us/azure/iot-edge/how-to-install-iot-edge-linux).

Next, you must provision EIS on your target deployment system. Follow the instructions
provided in the EIS READMEs/User Guide for completing this process.

While provisioning EIS on your system, note that you only need to setup the
Video Ingesiton and/or the Video Analytics containers. All other services are
not supported by the EIS Azure Bridge currently.

Be sure to note down which directory you generate your certificates into, this
will be important later. Unless, you are running EIS in dev mode, in that case
you will have no certificates generated.

**IMPORTANT NOTE:**

If you previously installed EIS outside of Azure on your system, then make sure
that all of the EIS containers have been stopped. You can do this by going to
the `build/` directory in the EIS source code and running the following command:

```sh
$ docker-compose down
```

This will stop and remove all of the previously running EIS containers, allowing
the EIS Azure Bridge to run successfully.

#### Expected Result

When you have completed these steps, you should have the Azure IoT Edge Runtime
installed (which includes Docker), and you should have the `ia_etcd` EIS container
running on your system.

To confirm this, run the `docker ps` command. Your output should look similar to
the following:

```sh
$ docker ps
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
75121173d4d8        ia_etcd:2.3         "./start_etcd.sh"   11 days ago         Up 2 seconds                            ia_etcd
```

### Step 2 - Configuring EIS

This step should be done from your development system, and not the edge node you
are deploying EIS onto. The configuration you will do during this setup will
allow your system to deploy EIS to your edge node. As noted earlier, for development
and testing purposes this could be the same system as your targeted edge device,
but this is not recommended in a production environment.

To configure EIS, modify the `build/provision/config/eis_config.json` file. This
should have been generated when the `build/eis_builder.py` script was executed
when building/pushing the EIS containers to your ACR instance. If it does not
exist, run this script based on the instructions provided in the EIS README.

Next, configure the `build/.env` file. You must make sure to modify the following
values in the `.env` file:

* `DOCKER_REGISTRY` - This should have been set when building/pushing the EIS
    containers to your ACR instance. Make sure it is set to the URL for your
    ACR instance.
* `HOST_IP` - This must be the IP address of the edge node you are deploying
    your containers to
* `ETCD_HOST` - This should be set to the same value as your `HOST_IP` address
* `DEV_MODE` - Set this to the same value you used when provisioning your edge node
    in the previous step

Next, in the `EISAzureBridge/` source directory, modify the `.env` file. Make
sure to set the following values:

* `EIS_CERTIFICATES`              - The directory with the EIS certificates on your edge system
* `AZ_CONTAINER_REGISTY_USERNAME` - User name for the container registry login (obtained during creation)
* `AZ_CONTAINER_REGISTY_PASSWORD` - Password for the container registry login (obtained during creation)
    * **IMPORTANT NOTE:** Make sure to surround the password in single quotes, i.e. `'`, because bash
        may escape certain characters when the file is read, leading to incorrect configuration
* `AZ_BLOB_STORAGE_ACCOUNT_NAME`  - **(OPTIONAL)** User name for the local Azure Blob Storage instance

**IMPORTANT NOTE #1:**

It is important to note that for the `AZ_CONTAINER_REGISTY_PASSWORD` variable you
must wrap the password in single quotes, i.e. `'`. Otherwise, there may be
characters that get escaped in a weird way when the values are populated into
your deployment manifest leading to configuration errors.

**IMPORTANT NOTE #2:**

If you wish to use the sample EIS ONNX UDF, now is the time to configure the UDF
to run. See the [Sample EIS ONNX UDF](#sample-eis-onnx-udf) configuration section
below for how to configure the UDF.

#### Expected Result

Once the following step has been completed, then you should have correctly configured
`.env` files to deploying EIS via Azure. If some of the values were incorrect, then
you will encounter issues in the proceeding steps.

### Step 3 - Configuring Azure IoT Deployment Manifest

Once you have your target edge system provisioned and EIS configured, you need to
create your Azure IoT Hub deployment manifest. The EIS Azure Bridge provides some
convenience scripts to ease this process.

> **NOTE:** These steps should be done from your development system setup in
> the [Development System Setup](#dev-sys-setup) section. Note, that for testing
> and development purposes, these could be the same system.

To generate your deployment manifest template, execute the following command:

```sh
$ ./tools/generate-deployment-manifest.sh example EISAzureBridge SimpleSubscriber ia_video_ingestion ia_video_analytics
```

> **NOTE:** If you are using Azure Blob Storage, include `AzureBlobStorageonIoTEdge`
> in the argument list above.

> **NOTE:** When you run the command above, it will pull some values from your
> EIS `build/.env` file. If the `build/.env` file is configured incorrectly,
> you may run into issues.

The above command will generate two files: `./example.template.json` and
`config/example.amd64.json`. The first is a deployment template, and the second
is the fully populated/generated configuration for Azure IoT Hub. In executing
the script above, you should have a manifest which includes the EIS Azure Bridge,
Simple Subscriber, as well as the EIS video ingestion service.

The list of services given to the bash script can be changed if you wish to
run different services.

You may want/need to modify your `./example.template.json` file after running
this command. This could be because you wish to change the topics that VI/VA use
or because you want to configure the EIS Azure Bridge in some different way. If you
modify this file, you must regenerate the `./config/example.amd64.json` file.
To do this, execute the following command:

```sh
$ iotedgedev genconfig -f example.template.json
```

If you wish to modify your `eis_config.json` file after generating your template,
you can re-add this to the EIS Azure Bridge digital twin by running the following
command:

```sh
$ python3 serialize_eis_config.py example.template.json ../build/provision/config/eis_config.json
```

**IMPORTANT NOTE:**

If you wish to have the EISAzureBridge subscribe and bridge data over an IPC
socket coming from either Video Ingestion or Video Analytics, then you must
change the user which the container operates under. By default, the EISAzureBridge
container is configured to run as the `eisuser` created during the installation of
EIS on your edge system. Both Video Ingestion and Video Analytics operate as root
in order to access various accelerators on your system. This results in the
IPC sockets for the communication with these modules being created as root. To
have the EISAzureBridge subscribe it must also run as root. To change this, do
the following steps:

1. Open your deployment manifest template
2. Under the following JSON key path: `modulesContent/modules/EISAzureBridge/settings/createOptions`
    delete the `User` key

This will cause the container to be launched as `root` by default allowing you to
subscribe to IPC sockets created as root.

#### Expected Result

If all of the commands above ran correctly, then you will have a valid `*.template.json`
file and a valid `config/*.amd64.json` file.

If, for some reason, these commands fail, revisit Step 2 and make sure all of your
environmental variables are set correctly. And if that does not resolve your issue,
verify that your development system is setup correctly by revisiting the
[Development System Setup](#dev-sys-setup) section.

### Step 4 - Deployment

Now that you have generated your deployment manifest, deploy the modules to your
Azure IoT Edge Device using the Azure CLI command shown below:

```sh
$ az iot edge set-modules -n <azure-iot-hub-name> -d <azure-iot-edge-device-name> -k config/<deployment-manifest>
```

If this command run successfully, then you will see a large JSON string print out
on the console with information on the deployment which it just initiated. If it
failed, then the Azure CLI will output information on the potential reason for the
failure.

#### Expected Results

Provided all of the setups above ran correctly, your edge node should now be running
your Azure IoT Edge modules, the EIS Azure Bridge, and the EIS services you
selected.

It is possible that for the EIS Azure Bridge (and any Python Azure IoT Edge modules)
you will see that the service crashes the first couple of times it attempts to come
up on your edge system with an exception similar to the following:

```
Traceback (most recent call last):
    File "/usr/local/lib/python3.7/site-packages/azure/iot/device/common/mqtt_transport.py", line 340, in connect
        host=self._hostname, port=8883, keepalive=DEFAULT_KEEPALIVE
    File "/usr/local/lib/python3.7/site-packages/paho/mqtt/client.py", line 937, in connect
        return self.reconnect()
    File "/usr/local/lib/python3.7/site-packages/paho/mqtt/client.py", line 1071, in reconnect
        sock = self._create_socket_connection()
    File "/usr/local/lib/python3.7/site-packages/paho/mqtt/client.py", line 3522, in _create_socket_connection
        return socket.create_connection(addr, source_address=source, timeout=self._keepalive)
    File "/usr/local/lib/python3.7/socket.py", line 728, in create_connection
        raise err
    File "/usr/local/lib/python3.7/socket.py", line 716, in create_connection
        sock.connect(sa)
    ConnectionRefusedError: [Errno 111] Connection refused
```

This occurs because the container is starting before the `edgeHub` container for
the Azure IoT Edge Runtime has come up, and so it it unable to connect. Once the
`edgeHub` container is fully launched, then this should go away and the containers
should launch correctly.

If everything is running smoothly, you should see messages being printed in the
Simple Subscriber service using the following command:

```sh
$ docker logs -f SimpleSubscriber
```

For more debugging info, see the following section.

### Helpful Debugging Commands

If you are encountering issues, the following commands can help with debugging:

* **Azure IoT Edge Runtime Daemon Logs:** `journalctl -u iotedge -f`
* **Container Logs:** `docker logs -f <CONTAINER-NAME>`

### Final Notes

When deploying with Azure IoT Edge Runtime there are many security considerations
to be taken into account. Please consult the following Microsoft resources regarding
the security in your deployments.

* [Securing Azure IoT Edge](https://docs.microsoft.com/en-us/azure/iot-edge/security)
* [IoT Edge Security Manager](https://docs.microsoft.com/en-us/azure/iot-edge/iot-edge-security-manager)
* [IoT Edge Certificates](https://docs.microsoft.com/en-us/azure/iot-edge/iot-edge-certs)
* [Securing the Intelligent Edge blob post](https://azure.microsoft.com/en-us/blog/securing-the-intelligent-edge/)

## Configuration

The configuration of the EIS Azure Bridge is a mix of the configuration for the
EIS services, the EIS Azure Bridge module, and configuration for the other
Azure IoT Edge Modules (i.e. the Simple Subscriber, and the Azure Blob Storage
modules). All of this configuration is wrapped up into your deployment manifest
for Azure IoT Hub.

The following sections cover the configuration of the aforementioned servies
and then the generation of your Azure Deployment manifest.

### EIS Azure Bridge

The EIS Azure Bridge spans EIS and Azure IoT Edge Runtime environments, as such
its configuration is a mix of EIS configuration and Azure IoT Edge module configuration
properties. The configuration of the bridge is split between environmental
variables specified in your Azure IoT Hub deployment manifest and the module's
digital twin. Additionally, the digital twin for the EIS Azure Bridge module
contains the entire configuration for the EIS services running in your edge
environment.

The configuration of the EIS Message Bus is done in a method similar to that of
the EIS services, such as Video Analytics service. To specify the topics which
the bridge should subscribe to you must set the `SubTopics` environmental variable
as follows:

```
SubTopics=VideoIngestion/camera1_stream,<PUBLISHING-SERVICE>/<TOPIC>,...
```

In the example above, you can see that `SubTopics` is a list of comma seperated
values, where each value is the publishing services seperated by a `/` and then
the topic to subscribe to.

In addition to this environmental variable, for every client/topic combination in
the list you must specify the configuration for the topic. This is done by
setting an environmental variable as follows:

```
<TOPIC>_cfg=zmq_ipc,${SOCKET_DIR}
```

This means that if your topic is `camera1_stream`, then the environmental variable
will be set as follows:

```
camera1_stream_cfg=zmq_ipc,${SOCKET_DIR}
```

Since the EIS Azure Bridge only supports IPC communication over the EIS Message
Bus currently, the value of the environmental variable will always be:
`zmq_ipc,${SOCKET_DIR}` for now.

> **NOTE:** In the future, the EIS Azure Bridge will support TCP communication
> using the ZeroMQ protocol in the EIS Message Bus. This confguration is subject
> to change when this feature is added.

Below is an example digital twin for the EIS Azure Bridge:

```json
{
    "log_level": "DEBUG",
    "topics": {
        "camera1_stream": {
            "az_output_topic": "camera1_stream"
        }
    },
    "eis_config": "{\"/VideoIngestion/config\": {\"encoding\": {\"type\": \"jpeg\", \"level\": 96}, \"ingestor\": {\"type\": \"opencv\", \"pipeline\": \"./test_videos/pcb_d2000.avi\", \"loop_video\": \"true\", \"queue_size\": 10, \"poll_interval\": 0.2}, \"max_jobs\": 20, \"max_workers\": 4, \"udfs\": [{\"name\": \"pcb.pcb_filter\", \"type\": \"python\", \"scale_ratio\": 4, \"training_mode\": \"false\", \"n_total_px\": 300000, \"n_left_px\": 1000, \"n_right_px\": 1000}, {\"name\": \"pcb.pcb_classifier\", \"type\": \"python\", \"ref_img\": \"common/udfs/python/pcb/ref/ref.png\", \"ref_config_roi\": \"common/udfs/python/pcb/ref/roi_2.json\", \"model_xml\": \"common/udfs/python/pcb/ref/model_2.xml\", \"model_bin\": \"common/udfs/python/pcb/ref/model_2.bin\", \"device\": \"CPU\"}]}, \"/GlobalEnv/\": {\"PY_LOG_LEVEL\": \"INFO\", \"GO_LOG_LEVEL\": \"INFO\", \"C_LOG_LEVEL\": \"INFO\", \"GO_VERBOSE\": \"0\", \"ETCD_KEEPER_PORT\": \"7070\"}}"
}
```

> See the `modules/EISAzureBridge/config_schema.json` for the full JSON schema
> for the digital twin of the EIS Azure Bridge module.

Each key in the configuration above is described in the table below.

|       Key       |                                              Description                                       |
| :-------------: | ---------------------------------------------------------------------------------------------- |
| `log_level`     | This is the logging level for the EIS Azure Bridge module, must be INFO, DEBUG, WARN, or ERROR |
| `topics`        | Configuration for the topics to map from the EIS Message Bus into the Azure IoT Edge Runtime   |
| `eis_config`    | Entire serialized configuration for EIS; this configuration will be placed in ETCD             |

You will notice that the `eis_config` is a serialized JSON string. This is due
to a limitation with the Azure IoT Edge Runtime. Currently, module digital twins
do not support arrays; however, the EIS configuration requires array support. To
workaround this limitation, the EIS configuration must be a serialized JSON
string in the digital twin for the EIS Azure Bridge module.

The `topics` value is a JSON object, where each key is a topic from the EIS Message
Bus which will be re-published onto the Azure IoT Edge Runtime. The value for
the topic key will be an additional JSON object, where there is one required
key, `az_output_topic`, which is the topic on Azure IoT Edge Runtime to use and
then an optional key, `az_blob_container_name`. This key specifies the Azure Blob
Storage container to store the images from the EIS video analytics pipeline in.
If this (key, value) pair is not specified, then the images will not be saved.

> **IMPORTANT NOTE:** "Container" in the Azure Blob Storage context is not
> referencing a Docker container, but rather a storage structure within the
> Azure Blob Storage instance running on your edge device. For more information
> on the data structure of Azure Blob Storage, see
> [this link](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-blobs-introduction#blob-storage-resources)

### Sample EIS ONNX UDF

EIS provides a sample UDF which utilizes the ONNX RT to execute your machine learning /
deep learning model. It also supports connecting to an AzureML Workspace to download
the model and then run it. The source code for this UDF is in `common/video/udfs/python/sample_onnx/`.

To use this UDF with EIS, you need to modify your `build/provision/config/eis_config.json`
configuration file to run the UDF in either your Video Ingesiton or Video Analytics
instance. Then, you need to modify the environmental variables in the `EISAzureBridge/.env`
file to provide the connection information to enable the UDF to download your
model from AzureML. Make sure to follow the instructions provided in the
[Setting up AzureML](#setting-up-azureml) section above to configure your
workspace correctly so that the UDF can download your model.

The sample ONNX UDF requires that the following configuration values be set for
the UDF in your `eis_config.json` file:

|           Key         |                                      Value                                |
| --------------------- | ------------------------------------------------------------------------- |
| `aml_ws`              | AzureML workspace name                                                    |
| `aml_subscription_id` | `subscriptionId` saved from creating the Service Principal Authentication |
| `model_name`          | Name of the model in your AzureML workspace                               |
| `download_mode`       | Whether or not to attempt to download the model                           |

> **NOTE:** If `download_mode` is `false`, then it expects the `model_name` to
> where the `*.onnx` model file is in the container.

This should be added into the `udfs` list for your Video Ingestion or Video Analytics
instance you wish to have run the UDF. The configuration should look similar to
the following:

```javascript
{
    // ... omited rest of EIS configuration ...

    "udfs": [
        {
            "name": "sample_onnx.onnx_udf",
            "type": "python",
            "aml_ws": "example-azureml-workspace",
            "aml_subscription_id": "subscription-id",
            "model_name": "example-model-name",
            "download_model": true
        }
    ]

    // ... omited rest of EIS configuration ...
}
```

The following environmental variables must be set in the `EISAzureBridge/.env` file
in order to have the sample ONNX UDF download your model from an AzureML Workspace:

|             Setting             |                      Description                  |
| :-----------------------------: | ------------------------------------------------- |
| `AML_TENANT_ID`                 | The `tenantId` saved in the Azure Cloud setup     |
| `AML_PRINCIPAL_ID`              | The `clientId` saved in the Azure Cloud setup     |
| `AML_PRINCIPAL_PASS`            | The `clientSecret` saved in the Azure Cloud setup |

It is important to note that for the `AML_PRINCIPAL_PASS` variable you must wrap the password
in single quotes, i.e. `'`. Otherwise, there may be characters that get escaped in
a weird way when the values are populated into your deployment manifest leading
to configuration errors.

The `tenantId`, `clientId`, `clientSecret`, and `subscriptionId` should all have
been obtained when following the instructions in the [Setting up AzureML](#setting-up-azureml)
section.

**IMPORTANT NOTE:**

If your system is behind a proxy, you may run into an issue where the download of
your ONNX model from AzureML times out. This may happen even if the proxy is set
globally for Docker on your system. To fix this, update your deployment manifest
template so that the Video Ingestion and/or Video Analytics containers have
the `http_proxy` and `https_proxy` values set. The manifest should look something
like the following:

```javascript
{
    // ... omitted ...

    "modules": {
        "ia_video_ingestion": {
            // ... omitted ...

            "settings": {
                "createOptions": {
                    "Env": [
                        // ... omitted ...

                        "http_proxy=<YOUR PROXY>",
                        "https_proxy=<YOUR PROXY>",

                        // ... omitted ...
                    ]
                }
            }

            // ... omitted ...
        }
    }

    // ... omitted ...
}
```

### Simple Subscriber

The Simple Subscriber module provided with the EIS Azure Bridge is a very simple
service which only receives messages over the Azure IoT Edge Runtime and prints
them to stdout. As such, there is no digital twin required for this module. The
only configuration required is that a route be established in the Azure IoT Edge
Runtime from the EIS Azure Bridge module to the Simple Subscriber module. This
routewill look something like the following in your deployment manifest:

```javascript
{
    "$schema-template": "2.0.0",
    "modulesContent": {
        // ... omitted for brevity ...

        "$edgeHub": {
            "properties.desired": {
                "schemaVersion": "1.0",
                "routes": {
                    "BridgeToSimpleSubscriber": "FROM /messages/modules/EISAzureBridge/outputs/camera1_stream INTO BrokeredEndpoint(\"/modules/SimpleSubscriber/inputs/input1\")"
                },
                "storeAndForwardConfiguration": {
                    "timeToLiveSecs": 7200
                }
            }
        }

        // ... omitted for brevity ...
    }
}
```

For more information on establishing routes in the Azure IoT Edge Runtime,
see [this documentation](https://docs.microsoft.com/en-us/azure/iot-edge/module-composition#declare-routes).

### EIS ETCD Pre-Load

The configuration for EIS is given to the EIS Azure Bridge via the `eis_config`
key in the module's digital twin. As specified in the EIS Azure Bridge configuration
section, this must be a serialized string. For the scripts included with the
EIS Azure Bridge for generating your deployment manifest the ETCD pre-load
configuration is stored at `config/eis_config.json`. See the EIS documentation
for more information on populating this file with your desired EIS configuration.
The helper scripts will automatically serialize this JSON file and add it to your
deployment manifest.

### Azure Blob Storage

For more information on configuring your Azure Blob Storage instance at the
edge, see the documentation for the service [here](https://docs.microsoft.com/en-us/azure/iot-edge/how-to-store-data-blob).

Also see [this guide](https://docs.microsoft.com/en-us/azure/iot-edge/how-to-deploy-blob)
as well.

### Azure Deployment Manifest

For more information on creating / modifying Azure IoT Hub deployment manifests,
see [this guide](https://docs.microsoft.com/en-us/azure/iot-edge/module-composition).

## Azure IoT Edge Simulator

Microsoft provides a simluator for the Azure IoT Edge Runtime. During the
setup of your development system (covered in the [Development System Setup](#dev-sys-setup)
section), the simulator is automatically installed on your system.

Additionally, the EIS Azure Bridge provides the `./tools/run-simulator.sh` script
to easily use the simulator with the bridge.

To do this, follow steps 1 - 3 in the [Single-Node Azure IoT Edge Deployment](#single-node-dep)
section above. Then, instead of step 4, run the following command to setup
the simulator:

```sh
$ sudo iotedgehubdev setup -c "<edge-device-connection-string>"
```

Next, start the simulator with your deployment manifest template using the
following command:

```sh
$ ./tools/run-simulator.sh ./example.template.json
```

If everything is running smoothly, you should see messages being printed in the
Simple Subscriber service using the following command:

```sh
$ docker logs -f SimpleSubscriber
```

**IMPORTANT NOTE:**

You *cannot* run both the Azure IoT Edge Runtime and the simulator simultaneously
on the same system. If you are using the same system, first stop the Azure IoT Edge
Runtime daemon with the following command:

```sh
$ sudo systemctl stop iotedge
```

Then, run the simulator as specified above.

## Supported EIS Services

Below is a list of services supported by the EIS Azure Bridge:

* Video Ingestion
* Video Analytics

## Additional Resources

For more resources on Azure IoT Hub and Azure IoT Edge, see the following
references:

* [Azure IoT Hub](https://docs.microsoft.com/en-us/azure/iot-hub/)
* [Azure IoT Edge](https://docs.microsoft.com/en-us/azure/iot-edge/)
* [How to Deploy AzureML Models](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-deploy-and-where)
* [AzureML Tutorial: Train your first ML Model](https://docs.microsoft.com/en-us/azure/machine-learning/tutorial-1st-experiment-sdk-train)
