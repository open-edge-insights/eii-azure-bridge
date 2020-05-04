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

The following sections will cover the configuration/usage of the EIS Azure
Bridge, the deployment of EIS on the Azure IoT Edge Runtime, as well as the
usage of the tools and scripts included in this code base for development.

> **NOTE:** The following sections assume an understanding of the configuration
> for EIS. It is recommended that you read the main README and User Guide for
> EIS prior to using this service.

## Pre-Requisites / Setup

To use and develop with the EIS Azure Bridge there are a few steps which must
be taken to configure your environment. Primarily, you need to configure your
Azure cloud account to have the proper instansiated services and you need to
setup your development system.

> **NOTE:** When you deploy with Azure IoT Hub you will also need to configure
> the Azure IoT Edge Runtime and EIS on your target device.

### <a name="az-cloud-setup"></a>Azure Cloud Setup

Prior to using the EIS Azure Bridge there are a few cloud services in Azure
which must be initialized.

Primarily, you need an Azure Containter Registry instance, an Azure IoT Hub,
as well as an Azure IoT Device. To create these instances, follow the guides
provided by Microsoft below:

> **NOTE:** In the quickstart guides below it is recommended that you create an
> Azure Resource Group. This is a good practice as it makes for easy clean up
> of your Azure cloud environment.

* [Create Azure Container Registry](https://docs.microsoft.com/en-us/azure/container-registry/container-registry-get-started-portal)
* [Create Azure IoT Hub](https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-create-through-portal)
* [Register an Azure IoT Device](https://docs.microsoft.com/en-us/azure/iot-edge/how-to-register-device)
* [Create AzureML Workspace](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-manage-workspace)
* [Push Model to AzureML Workspace](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-deploy-existing-model)
    > **NOTE:** If you already have an existing model in AzureML, do not worry about doing this step
    > If you need a model to push, a good resource can be found [here](https://notebooks.azure.com/azureml/projects/azureml-getting-started/html/how-to-use-azureml/deployment/onnx/onnx-modelzoo-aml-deploy-resnet50.ipynb)

For the AzureML Workspace, you also need to setup the workspace to be able
authenticate connections using Service Principal Authentication. To set this
up, follow the instructions provided [here](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-setup-authentication#set-up-service-principal-authentication).

In this setup process, you will execute a command to similar to the following:

```sh
$ az ad sp create-for-rbac --sdk-auth --name ml-auth
```

After executing this command you will see a JSON blob printed to your console
window. Save the `clientId`, `clientSecret`, `subscriptionId`, and `tenantId`
for configuring the sample ONNX EIS UDF later.

All of the tutorials provided above provide options for creating these instances
via Visual Studio Code, the Azure Portal, or the Azure CLI. If you wish to use
the Azure CLI, it is recommended that you follow the Development System Setup
instructions below.

**IMPORTANT:**

In the tutorials above you will receive credentials/connection strings for your
Azure Container Registry, Azure IoT Hub, and Azure IoT Device. Save these for
later, as they will be important for setting up your development and single node
deployment showcased in this README.

### <a name="dev-sys-setup"></a>Development System Setup

The development system will be used for the following actions:

* Building and pushing the EIS containers to your Azure Container Registry
* Building and pushing the EIS Azure Bridge containers
* Creating your Azure IoT Hub deployment manifest
* Deploying your manifest to a single node

The instructions that follow should be followed in order to run the EIS Azure
Bridge locally or on a single-node deployment.

First, setup your system for building EIS. To do this, follow the instructions
detailed in the main EIS README and the EIS User Guide.

Once this is completed, install the required components to using the Azure CLI
and development tools. The script, `./tools/install-dev-tools.sh` automates this
process. To run this script, execute the following command:

```sh
$ sudo -H -E -u ${USER} ./tools/install-dev-tools.sh
```

> **NOTE:** The `-u ${USER}` flag above allows the Azure CLI to launch your
> browser (if it can) so you can login to your Azure account.

While running this script you will be prompted to sign-in to your Azure
account so you can run commands from the Azure CLI that interact with your
Azure instance.

This script will install the following:

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
services which can be pushed to an ACR. Not all EIS services are supported by and
validated with the EIS Azure Bridge.

### <a name="single-node-setup"></a>Single-Node Azure IoT Edge Setup

To setup a Linux system with the Azure IoT Edge Runtime follow the instructions
provided at [this link](https://docs.microsoft.com/en-us/azure/iot-edge/how-to-install-iot-edge-linux).

## <a name="eis-build-push"></a>Build and Push EIS Containers

After setting up your development system, build and push the EIS containers
to your Azure Contianer Registry.

If you are going to use the Sample ONNX EIS UDF, then you must copy the UDF
source code into the EIS `IEdgeInsights/common/udfs/python/` directory. Do this
with the following command:

```sh
$ cp -r sample_onnx/ ../common/udfs/python
```
> **NOTE:** The command above assume you have the EIS Azure Bridge source code
> as a subdirectory of the EIS source code.

Additionally, you will need to add some Python packages to be installed when
the Video Ingestion container gets built. Modify the `IEdgeInsights/VideoIngestion/vi_requirements.txt`
file to look like the following:

```
numpy==1.18.0
onnxruntime==1.2.0
azureml-sdk==1.4.0
```

Once you have completed these steps, follow the instructions provided in the EIS
READMEs and User Guide to build and push the EIS containers to a container
registry.

**IMPORTANT NOTE**

When initially building the EIS containers do not set the `DOCKER_REGISTRY`
variable in the `docker_setup/.env` file. Build the containers, and then set
the registry URL. After that, build the EIS containers again (this will not
re-build any binaries, it will just re-tag the container images), and then
run the `docker-compose push` command.

## Build and Push EIS Azure Bridge Containers

To build the EIS Azure Bridge containers (i.e. the `SimpleSubscriber` and `EISAzureBridge`
Azure IoT Edge modules) first you must set the `AZ_CONTAINER_REGISTRY` value in the
`.env` file. The value of this should be the URL to your Azure Container Registry.
You should have gotton the URL when creating your Azure Container Registry.

Next, to build the containers, execute the followoing command:

```sh
$ ./tools/build-azure-modules.sh
```

Once the modules have been built, push them to your Azure Container Registry
with the following command:

```sh
$ ./tools/push-azure-modules.sh
```

> **NOTE:** The comannd above will only succeed if you have logged into your
> Azure Container Registry using the command specified in the
> [Development System Setup](#dev-sys-setup) section.

## Running Locally on Development System

To run the EIS Azure Bridge in the Azure IoT Edge Runtime simulator provided
through the `iotedgehubdev` tool, follow the instructions below:

> **NOTE:** It is assumed that you have ran the `./tools/install-dev-tools.sh`
> script prior to following these steps.

1. Provision EIS on your development system
    > **NOTE:** Execute the following command from the
    > `<EIS root source code>/docker_setup/provision/`directory.

    Before running the following command, make sure to modify the `docker_setup/.env`
    file according to the EIS configuration you want to use.

    Also, set the `ETCD_HOST` variable in the `docker_setup/.env` file in EIS
    to the IP address of your development system.

    ```sh
    $ sudo -H -E ./provision_eis.sh ../docker-compose.yml
    ```

    At this point, you don't need to worry about modifying the EIS `docker-compose.yml`
    since the EIS Azure Bridge will replace all of the configuration in ETCD
    when it starts up.

2. Populate the Azure Container Registry variables in the `.env` file. This
    should include populating the `AZ_CONTAINER_REGISTRY`, `AZ_CONTAINER_REGISTRY_USERNAME`,
    and `AZ_CONTAINER_REGISTRY_PASSWORD` variables. All of these values should
    have been obtained when creating your Azure Container Registry.

    > **NOTE:** The `AZ_CONTAINER_REGISTRY` variable will be a value that looks
    > like `*.azurecr.io`.

3. Populate the AzureML variables in the `.env` file. This should include
    populating the `AML_TENANT_ID`, `AML_PRINCIPAL_ID`, and `AML_PRINCIPAL_PASS`
    environmental variables. The values of these will be the values saved when
    you created the Service Principal Authentication for your AzureML workspace
    in the [Azure Cloud Setup](#az-cloud-setup) section. The table below
    provides the necessary mappings.

    | Environmental Variable |  Mapped Value  |
    | :--------------------: | :------------: |
    | `AML_TENANT_ID`        | `tenantId`     |
    | `AML_PRINCIPAL_ID`     | `clientId`     |
    | `AML_PRINCIPAL_PASS`   | `clientSecret` |

4. Configure sample ONNX EIS UDF. Open the `config/eis_config.json` file. Under
    the `udfs` key, modify the following (key, value) pairs:

    |           Key         |                                      Value                                |
    | --------------------- | ------------------------------------------------------------------------- |
    | `aml_ws`              | AzureML workspace name                                                    |
    | `aml_subscription_id` | `subscriptionId` saved from creating the Service Principal Authentication |
    | `model_name`          | Name of the model in your AzureML workspace                               |

5. **(OPTIONAL)** If you wish to store the images from the EIS video ingestion
    service in a local Azure Blob Storage instance, then you must fill in the
    `AZ_BLOB_STORAGE_ACCOUNT_NAME` variable in the `.env` file.

    The account name must be a lowercase string with no spaces or odd characters.
    This script will populate the values in the `.env` file including the account
    key.

6. Generate an Azure IoT Hub deployment manifest

    ```sh
    $ ./tools/generate-deployment-manifest.sh example EISAzureBridge SimpleSubscriber ia_video_ingestion
    ```

    > **NOTE:** If you are using Azure Blob Storage, include `AzureBlobStorageonIoTEdge`
    > in the argument list above.

    > **NOTE:** When you run the command above, it will pull some values from your
    > EIS `docker_setup/.env` file. Make sure to see the EIS README for what to
    > set in that file.

    The above command will generate two files: `./example.template.json` and
    `config/example.amd64.json`. The first is a deployment template, and the second
    is the fully populated/generated configuration for Azure IoT Hub. In executing
    the script above, you should have a manifest which includes the EIS Azure Bridge,
    Simple Subscriber, as well as the EIS video ingestion service.

    If you have chosen to use the Azure Blob Storage service, then you will
    be prompted to provide an Azure Blob Storage account name. This is not
    tied to a cloud instance, but will be how the EIS Azure Bridge logs into
    the local instance of Azure Blob Storage deployed on your edge device.

7. Setup the `iotedgehubdev` simulator with the following command:

    ```sh
    $ sudo iotedgehubdev setup -c "<edge-device-connection-string>"
    ```

    > **NOTE:** This setup is only required the first time you run the EIS Azure
    > Bridge in a simulator.

8. Run the simulator using the command below:

    ```sh
    $ ./tools/run-simulator.sh ./example.template.json
    ```

After executing the steps above, run the following command to see the output
from the Simple Subscriber:

```sh
$ docker logs -f SimpleSubscriber
```

This service should be outputting classification meta-data from EIS, which it
received over the Azure IoT Edge Runtime.

## Single-Node Azure IoT Edge Deployment

> **NOTE:** Outside of the Azure ecosystem, EIS can be deployed and communicate
> across nodes. In the Azure IoT Edge ecosystem this is not possible with EIS.
> All EIS services must be running on the same edge node. However, you can
> deploy EIS on multiple nodes, but intercommunication between the nodes will
> not work.

In the Azure IoT ecosystem you can deploy to single-nodes and you can do bulk
deployments. This section will cover how to deploy the EIS Azure Bridge and
associated EIS services to a single Linux edge node. For more details on deploying
modules at scale with the Azure IoT Edge Runtime, see
[this guide](https://docs.microsoft.com/en-us/azure/iot-edge/how-to-deploy-monitor)

Note that this section will give a high-level overview of how to deploy the
modules with the Azure CLI. For more information on developing and deploying
Azure modules, see [this guide](https://docs.microsoft.com/en-us/azure/iot-edge/tutorial-develop-for-linux).

In order to deploy to a single Azure IoT Edge node you must have already
configured your Azure cloud instance (see instructions in the [Azure Cloud Setup](#az-cloud-setup)
section). Additionally, you need to have already built and pushed the EIS services
(follow the instructions in the [Build and Push EIS Containers](#eis-build-push) section).

Once you have completed these two steps you must then install the Azure IoT
Edge Runtime on your target deployment system. To do that, follow the instructions
provided by Microsoft in [this guide](https://docs.microsoft.com/en-us/azure/iot-edge/how-to-install-iot-edge-linux).

Next, you must provision EIS on your target deployment system. Follow the instructions
provided in the EIS READMEs/User Guide for completing this process.

Once you have your target edge system setup and provisioned, you need to
create your Azure IoT Hub deployment manifest and set the modules for the
Azure IoT Edge Device. The EIS Azure Bridge provides some convenience scripts
to ease this process. To complete this steps, follow the instructions below.

> **NOTE:** These steps should be done from your development system setup in
> the [Development System Setup](#dev-sys-setup) section.

1. Configure the `.env` file in this repository. You must set the following
    values in the `.env` file

    |             Setting             |                                  Description                                 |
    | :-----------------------------: | ---------------------------------------------------------------------------- |
    | `EIS_CERTIFICATES`              | The directory with the EIS certificates on your edge system                  |
    | `AZ_CONTAINER_REGISTRY`         | URL for the container registry (obtained during creation)                    |
    | `AZ_CONTAINER_REGISTY_USERNAME` | User name for the container registry login (obtained during creation)        |
    | `AZ_CONTAINER_REGISTY_PASSWORD` | Password for the container registry login (obtained during creation)         |
    | `AZ_BLOB_STORAGE_ACCOUNT_NAME`  | **(OPTIONAL)** User name for the local Azure Blob Storage instance           |
    | `AML_TENANT_ID`                 | The `tenantId` saved in the Azure Cloud setup                                |
    | `AML_PRINCIPAL_ID`              | The `clientId` saved in the Azure Cloud setup                                |
    | `AML_PRINCIPAL_PASS`            | The `clientSecret` saved in the Azure Cloud setup                            |


    The `.env` file in this folder will pull from your `IEdgeInsights/docker_setup/.env`
    file when generating your deployment manifest later in these steps. Make sure
    that you have configured that file according to the EIS configuration you
    have on your target system.

    Especially, make sure to set the `ETCD_HOST` to the IP address of your
    target machine. This is a current limitation of the EIS Azure Bridge.

    > **NOTE:** If you have chosen to use the Azure Blob Storage service, then you will
    > be prompted to provide an Azure Blob Storage account name. This is not
    > tied to a cloud instance, but will be how the EIS Azure Bridge logs into
    > the local instance of Azure Blob Storage deployed on your edge device.

    > **NOTE:** There are other values in this `.env` file, they are mostly common
    > EIS environment variables. See the EIS documentation for more details.

2. Configure EIS pre-load configuration. This configuration is at `config/eis_config.json`.
    Modify this file according to how you want EIS to run. By default, EIS is
    configured to run the sample ONNX EIS UDF. To configure this UDF modify the
    following (key, value) pairs under the `udfs` key:

    |           Key         |                                      Value                                |
    | --------------------- | ------------------------------------------------------------------------- |
    | `aml_ws`              | AzureML workspace name                                                    |
    | `aml_subscription_id` | `subscriptionId` saved from creating the Service Principal Authentication |
    | `model_name`          | Name of the model in your AzureML workspace                               |

3. Generate your Azure IoT Hub deployment manifest

    ```sh
    $ ./tools/generate-deployment-manifest.sh example EISAzureBridge SimpleSubscriber ia_video_ingestion
    ```

    > **NOTE:** If you are using Azure Blob Storage, include `AzureBlobStorageonIoTEdge`
    > in the argument list above.

    > **NOTE:** When you run the command above, it will pull some values from your
    > EIS `docker_setup/.env` file. Make sure to see the EIS README for what to
    > set in that file.

    The above command will generate two files: `./example.template.json` and
    `config/example.amd64.json`. The first is a deployment template, and the second
    is the fully populated/generated configuration for Azure IoT Hub. In executing
    the script above, you should have a manifest which includes the EIS Azure Bridge,
    Simple Subscriber, as well as the EIS video ingestion service.

4. Set the modules on your Azure IoT Edge Device using the Azure CLI command
    shown below:

    ```sh
    $ az iot edge set-modules -n <azure-iot-hub-name> -d <azure-iot-edge-device-name> -k config/<deployment-manifest>
    ```

Provided all of the setups above ran correctly, your edge node should now be running
your Azure IoT Edge modules, the EIS Azure Bridge, and the EIS Video Ingestion
service.

**IMPORTANT:**

When deployment with Azure IoT Edge Runtime there are many security considerations
to be taken into account. Please see the following Microsoft resources regarding
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
