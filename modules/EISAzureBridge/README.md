EIS Azure Bridge Module
=======================

This directory contains the source code for the EIS Azure Bridge EIS service
which bridges communication from the EIS Message bus and the Azure IoT Edge
Runtime. For more information on this service, see the top level README. The
purpose of this README is to cover some specifics related to the code itself,
and not the usage of the module in EIS. Refer to the EIS and EIS Azure Bridge
READMEs for more information.

## Running Unit Tests

The EIS Azure Bridge contains unit tests for various utility functions in the
service. It does not contain unit tests for every single method, because most
of it is not unit test-able, meaning, you must have a fully up and running Azure
IoT Edge Runtime in order to run the code succesfully. Testing the bridge in
this way can be accomplished via using the Azure IoT Edge Runtime simulator
documented in the root directory of the EIS Azure Bridge service.

To run the unit tests for the EIS Azure Bridge, first install the EIS Azure
Bridge python dependencies:

```sh
$ sudo -H -E pip3 install -r requirements.txt
```

Next, setup your `PYTHONPATH` to contian the necessary EIS Python libraries for
the test:

> **NOTE:** This can be skipped if you have installed the EIS libraries on your
> system already. This step assumes none of the EIS libraries for Python, Go,
> or C have been installed on your system.

```sh
$ export PYTHONPATH=${PYTHONPATH}:../../../common:../../../common/libs/ConfigManager/python
```

Next, run the unit tests with the following Python command:

```sh
$ python3 -m unittest discover
```

If everything runs successfully, you should see the following output:

```
..
----------------------------------------------------------------------
Ran 2 tests in 0.001s

OK
```
