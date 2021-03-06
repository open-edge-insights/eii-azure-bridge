# Contents

- [Contents](#contents)
  - [Azure Bridge Module](#azure-bridge-module)
  - [Running Unit Tests](#running-unit-tests)

## Azure Bridge Module

This directory contains the source code for the Azure Bridge OEI service which bridges communication from the Message bus and the Azure IoT Edge Runtime. For more information on this service, see the top level README. The purpose of this README is to cover some specifics related to the code itself, and not the usage of the module in OEI. Refer to the OEI and Azure Bridge READMEs for more information.

>**Note:** In this document, you will find labels of 'Edge Insights for Industrial (EII)' for filenames, paths, code snippets, and so on. Consider the references of EII as Open Edge Insights (OEI). This is due to the product name change of EII as OEI.

## Running Unit Tests

The Azure Bridge contains unit tests for various utility functions in the service. It does not contain unit tests for every single method, because most of it is not unit test-able, meaning, you must have a fully up and running Azure IoT Edge Runtime in order to run the code succesfully. Testing the bridge in this way can be accomplished via using the Azure IoT Edge Runtime simulator documented in the root directory of the Azure Bridge service.

To run the unit tests for the Azure Bridge, first install the Azure Bridge python dependencies:

>**Note:** It is highly recommended that you use a python virtual environment to install the python packages, so that the system python installation doesn't get altered. Details on setting up and using python virtual environment can be found [here](https://www.geeksforgeeks.org/python-virtual-environment/)

 ```sh
 sudo -H -E pip3 install -r requirements.txt
 ```

Next, set up your `PYTHONPATH` to contian the necessary OEI Python libraries for the test:

> **NOTE:** This can be skipped if you have installed the OEI libraries on your system already. This step assumes none of the OEI libraries for Python, Go, or C have been installed on your system.

```sh
export PYTHONPATH=${PYTHONPATH}:../../../common:../../../common/libs/ConfigManager/python
```

Next, run the unit tests with the following Python command:

```sh
python3 -m unittest discover
```

If everything runs successfully, you should see the following output:

```sh
..
----------------------------------------------------------------------
Ran 2 tests in 0.001s

OK
```
