# 1. Table of Contents
- [1. Table of Contents](#1-table-of-contents)
- [2. Description](#2-description)
  - [2.1. Host-MRM Interaction Model](#21-host-mrm-interaction-model)
  - [2.2. Scanning Modes](#22-scanning-modes)
    - [2.2.1 Finite Scanning Mode](#221-finite-scanning-mode)
    - [2.2.2 Continuous Scanning Mode](#222-continuous-scanning-mode)
  - [2.3. Notes/Cautions](#23-notescautions)
- [3. Directory Tree](#3-directory-tree)
  - [3.1. Files of Note](#31-files-of-note)
- [4. Prerequisites](#4-prerequisites)
  - [4.1. Python/Modules](#41-pythonmodules)
    - [4.1.1. conda](#411-conda)
    - [4.1.2. pip](#412-pip)
  - [4.2. Networking](#42-networking)
- [5. Usage and Behavior](#5-usage-and-behavior)
  - [5.1 Basic Usage](#51-basic-usage)
    - [5.1.1 Continuous Scan Usage](#511-continuous-scan-usage)
  - [5.2 control.py](#52-controlpy)
    - [5.2.1 Arguments](#521-arguments)
  - [5.3 emulator_test_driver.py](#53-emulator_test_driverpy)
  - [5.4. Input/Parameter Files](#54-inputparameter-files)
    - [5.4.1. settings.yml](#541-settingsyml)
- [6. Scan Data](#6-scan-data)
  - [6.1. Saved Files](#61-saved-files)
  - [6.2. Unpacking Saved Files](#62-unpacking-saved-files)
  - [6.3. Displaying an RTI Plot](#63-displaying-an-rti-plot)
- [7. Logging](#7-logging)
- [8. Credits](#8-credits)
 
# 2. Description
This software implements command and control (C2) of and receipt of data from the Time Domain PulsON 440 Monostatic Radar Module (MRM). More specifically, this software deployed to and executed from a Host computer, hereafter referred to as a/the Host, connected to the MRM will allow a user to query, configure, command, and receive all MRM functionality. In order to do so, the following constructs are leveraged.
- The [Application Programming Interface (API)](https://github.com/bwsiuassar/documentation/blob/master/PulsON%20440/320-0298E-MRM-API-Specification.pdf) between a Host and a MRM.
- The UDP-based communication between a Host and a MRM.

Assuming that MRM has been properly connected to the Host, this software allows users to exercise a subset of the [API](https://github.com/bwsiuassar/documentation/blob/master/PulsON%20440/320-0298E-MRM-API-Specification.pdf) functionality required to
- Query the MRM for various status indicators,
- Set the MRM configuration, 
- Command the MRM to collect scan data for relay to the Host, and
- Various other MRM behaviors like reboot.

## 2.1. Host-MRM Interaction Model
The interaction between Host software and a MRM is nearly identical to that of a [client-server](https://en.wikipedia.org/wiki/Client%E2%80%93server_model) wherein the Host software is a client making requests of the MRM as a server. One important distinction is that unlike typical, modern client-server applications (e.g., websites) where many clients may interact with a server, this application typically limits itself to one client making it [peer-to-peer](https://en.wikipedia.org/wiki/Peer-to-peer) in terms of interaction. For most developers, this distinction is not important but worth noting for those whose target applications involve either multiple Host software instances and/or multiple MRMs.

The basic interaction pattern is a request-confirm or send-receive one whereby the Host software makes requests of the MRM to which the MRM responds appropriately. This is reflected in the [API](https://github.com/bwsiuassar/documentation/blob/master/PulsON%20440/320-0298E-MRM-API-Specification.pdf)) where the majority of messages come in pairs in which one message originates from the Host software (request) and its paired message originates from the MRM (confirm).

## 2.2. Scanning Modes
The MRM is capable of two (2) modes or types of scanning, finite and continuous. As their names imply, the finite mode collects a finite number of scans until completion while the continuous mode continuously collects until commanded to stop. Both leverage the same basic messages of the [API](https://github.com/bwsiuassar/documentation/blob/master/PulsON%20440/320-0298E-MRM-API-Specification.pdf) but different in the sequence of events. The following subsections provide additional detail but assume that the perquisite events of connecting to the MRM and setting the desired configuration have already been accomplished. In both modes, [scan data](#6-scan-data) is saved to disk in a custom [format](#61-saved-files).

### 2.2.1 Finite Scanning Mode
The basic sequence of events in this mode are:
1. Host software commands the MRM to collect a finite number of scans.
2. The MRM collects the specified number of scans without interruption.
3. As the MRM collects scans, it transmits to the Host the received scans.
4. The MRM completes the specified number of scans including their transmission to the Host.
5. The MRM is ready to receive new commands.

### 2.2.2 Continuous Scanning Mode
The basic sequence of events in this mode are:
1. Host software commands the MRM to collect a continuous or infinite number of scans.
2. The MRM begins to collect scans.
3. As the MRM collects scans, it transmits to the Host the received scans.
4. The Host software commands the MRM to stop collecting scans.
5. The MRM completes the current scan it is collecting and transmits it to the Host.
6. The MRM is ready to receive new commands.

## 2.3. Notes/Cautions
- **Limited API Implementation**
  
  Only a minimum of the [API](https://github.com/bwsiuassar/documentation/blob/master/PulsON%20440/320-0298E-MRM-API-Specification.pdf) is implemented in the emulator as much of it is not relevant or realistic in the emulator's expected use cases. Refer to [formats.py](formats.py) for the implemented subset.

- **Synchronous Interaction/Model**
  
  The request-confirm model inherently promotes a [synchronous](https://www.youtube.com/watch?v=N5Ky-mz6n-8) event sequence and this software reflects as much. However, in spite of substantial use and validation of this software, there are no guarantees of the MRM following such a model in all cases including when errors may occur. Therefore, it is recommended that developers implement appropriate checks to avoid unknown behavior.

- **YAML Usage/Familiarity**
  
  This codebase uses [YAML](https://yaml.org/) for all configuration and parameterization needs. It is recommended that users have at least a basic familiarity with YAML in order to understand and utilize these aspects of the codebase.

- **Simultaneous Compatibility with MRM and Emulator**

A best effort is made to maintain simultaneous compatibility with the MRM and its [emulator](https://github.com/bwsiuassar/emulator). Due to differences in the MRM and the emulator, this codebase contains some functionality that only applies to one of these and not the other.

[**Go to Top**](#1-table-of-contents)

# 3. Directory Tree
```console
.
├── __init__.py
├── conda_environment.yml
├── constants.py
├── control.py
├── display_rti.py
├── emulator_test_driver.py
├── formats.py
├── log_config.yml
├── pip_requirements.txt
├── pulson440.py
├── settings.yml
├── README.md
└── unpack.py
```

## 3.1. Files of Note
- Configuration
  - [log_config.yml](log_config.yml) - Default/template logger configuration.
  - [settings.yml](settings.yml) - Default/template settings.
- Source
  - [constants.py](constants.py) - MRM constants including default values.
  - [formats.py](formats.py) - MRM message formats.
  - [pulson440.py](pulson440.py) - MRM C2 class; core functionality of this codebase.
  - [unpack.py](unpack.py) - MRM scan data unpacking.
- Scripts
  - [control.py](control.py) - Host executed MRM C2 script for scan data collection.
  - [emulator_test_driver.py](emulator_test_driver.py) - Host executed emulator C2 script for driving/testing the emulator.
  - [display_rti.py](display_rti.py) - Standalone module for displaying an RTI plot of unpacked data

[**Go to Top**](#1-table-of-contents)

# 4. Prerequisites
## 4.1. Python/Modules
The following lists the required Python modules to run the emulator.

| Required Module                       | Minimum Tested Version |
| :------------------------------------ | :--------------------- |
| [Python](https://www.python.org/)     | 3.8.5                  |
| [matplotlib](https://matplotlib.org/) | 3.3.2                  |
| [NumPy](https://numpy.org/)           | 1.19.2                 |
| [PyYAML](https://pyyaml.org/)         | 5.3.1                  |
| [SciPy](https://www.scipy.org/)       | 1.5.2                  |

Provided in this software package are configuration files that will allow you to meet these requirements using either the [conda](https://docs.conda.io/en/latest/) or [pip](https://pip.pypa.io/en/stable/) package managers. Listed below are the steps to meet and use the requirements for each package manager. Please use only one of these options to avoid creating package/environment conflicts

### 4.1.1. [conda](https://docs.conda.io/en/latest/)
In addition to installing requested modules and necessary dependencies, conda can install these items in a [virtual environment](https://realpython.com/python-virtual-environments-a-primer/) that is useful for minimizing the complexity of your development and execution environment. The following steps do exactly this.
  1. [Create 'pulson440' environment from environment file](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file) - `conda env create -f conda_environment.yml`
  2. [Activate 'pulson440' environment]((https://docs.conda.io/en/latest/)) - `conda activate emulator`

### 4.1.2. [pip](https://pip.pypa.io/en/stable/)
  1. [Install from requirements file](https://pip.pypa.io/en/stable/user_guide/#requirements-files) - `pip install -r pip_requirements.txt`

## 4.2. Networking
The basic communication interface between a Host and MRM is assumed to be a network protocol, more specifically, a physical ethernet connection that establishes a common [Local Area Network (LAN)](https://en.wikipedia.org/wiki/Local_area_network). Consequently, a Host and MRM are uniquely identified and addressed using a [standard IP and port scheme](https://www.geeksforgeeks.org/difference-between-ip-address-and-port-number/). It is important for users to not only know the IP and port pairing of the MRM of interest but also to ensure that any Host software's IP and port usage deconflicts with said MRM values.

The MRM comes preconfigured w/ a static IP that varies depending on time of manufacturer but the following IP and port pairings have been observed:

| IP            | Port  |
| :------------ | :-----|
| 192.168.1.151 | 21210 |

Here are some potentially useful resources to a) validate networking and b) understand UDP socket-based communication.
- Official Python resources
  - [socket](https://docs.python.org/3/library/socket.html) module
  - [Socket HOWTO](https://docs.python.org/3/library/socket.html)
  - [UDP communication](https://wiki.python.org/moin/UdpCommunication)
- Tutorials/Examples
  - [UDP client/server template](https://pymotw.com/2/socket/udp.html)
  - [Socket programming](https://realpython.com/python-sockets/) (uses TCP as opposed to UDP; concepts/structures still apply to UDP)

[**Go to Top**](#1-table-of-contents)

# 5. Usage and Behavior
The usage and behavior of the Host software implemented by this codebase is only one way to realize the overall goal(s) of MRM C2 and scan data reception. Other developers may choose alternative approaches such as invoking the Host software via the command line as this codebase does. The rest of this section will explain how this specific codebase does so and important aspects of configuring and executing various behaviors.

## 5.1 Basic Usage
The Host software is designed to be used in conjunction with either a MRM or [emulator](https://github.com/bwsiuassar/emulator) which will respond to Host behavior. The following is the basic, ordered sequence of broad event categories that are expected to occur.
1. Invocation and readiness of MRM or emulator.
2. Command line invocation of the Host software through either:
    - [control.py](control.py) or with appropriate [arguments](#521-arguments), e.g., `python control.py`, or
    - [emulator_test_driver.py](emulator_test_driver.py), e.g., `python emulator_test_driver.py`.
3. C2 and data exchange between emulator and Host.
4. Completion of Host software behavior.

### 5.1.1 Continuous Scan Usage
As described earlier, the [continuous scanning mode](#222-continuous-scanning-mode) of the MRM (or emulator) is only stopped after the Host software commands it to stop. In this codebase, this is accomplished via a file to which any non-zero value written to initiates a sequence of events to stop the continuous scanning. By default, this file is named 'control_radar' and is initially populated with a zero (0). To be clear, here is the [continuous scanning mode event sequence](#222-continuous-scanning-mode) updated with this specific implementation:
1. On initialization, the Host software creates the 'control_radar' file and populates it with a zero (0).
2. Host software commands the MRM to collect a continuous or infinite number of scans.
3. The MRM begins to collect scans.
4. As the MRM collects scans, it transmits to the Host the received scans.
5. User enters a non-zero value into 'control_radar'.
6. The Host software commands the MRM to stop collecting scans.
7. The MRM completes the current scan it is collecting and transmits it to the Host.
8. The Host software resets 'control_radar' with a zero (0) entry.
9. The MRM is ready to receive new commands.

## 5.2 [control.py](control.py)
[control.py](control.py) is designed to command an actual MRM to collect scans. While it should work with the [emulator](https://github.com/bwsiuassar/emulator), this configuration has not been tested.

### 5.2.1 Arguments
`scan_data_filename`
- **Description/Purpose:** Path and name of file to save radar scans to.
- **Type**: string
- **Default:** Depends on scanning/collection mode.

`--host_ip`
- **Description/Purpose:** User defined host IP address.
- **Type**: str
- **Choices/Requirements:** 
  - Users are responsible for picking/ensuring availability of specified address.

`--host_port`
- **Description/Purpose:** User defined host port.
- **Type**: int
- **Choices/Requirements:** 
  - Users are responsible for picking/ensuring availability of specified port.

`--radar_ip`
- **Description/Purpose:** MRM defined IP address.
- **Type**: str
- **Choices/Requirements:** 
  - This value is defined by the MRM itself; users should provide this value.

`--radar_port`
- **Description/Purpose:** MRM defined port.
- **Type**: int
- **Choices/Requirements:** 
  - This value is defined by the MRM itself; users should provide this value.

`--quick`
- **Description/Purpose:** Perform quick-look mode.
- **Type**: flag
- **Choices/Requirements:** 
  - Mutually exclusive with `--collect` argument.
  - In this mode, default `scan_data_filename` is 'quick_look.prd'.

`--collect`
- **Description/Purpose:** Perform collection mode.
- **Type**: flag
- **Choices/Requirements:** 
  - Mutually exclusive with `--quick` argument.
  - In this mode, default `scan_data_filename` is 'collect_N.prd' where 'N' is replaced by an integer to deconflict with any existing files.

`--num_scans`
- **Description/Purpose:** Number of scans to collect with `--collect` mode.
- **Type**: int
- **Choices/Requirements:** 
  - Defaults to continuous scanning.
- **Default:** 65535

`--interval`
- **Description/Purpose:** Interval (us) between consecutive scans with `--collect` mode.
- **Type**: int
- **Default:** 0

`--settings_file`
- **Description/Purpose:** Path and name of to radar settings file.
- **Type**: string
- **Default:** 'settings.yml'

`--return_data`
- **Description/Purpose:** Return collected data.
- **Type**: flag
- **Choices/Requirements:** 
  - Only useful if calling in other code.

## 5.3 [emulator_test_driver.py](emulator_test_driver.py)
[emulator_test_driver.py](emulator_test_driver.py) is designed to command the [emulator](https://github.com/bwsiuassar/emulator). Its primary purpose is to serve as an example/template for how to utilize this codebase in conjunction with the emulator. There is no particular meaning to the sequence of events implemented which are briefly described next.
1. Host software initialized.
2. Establish and confirm connection to emulator.
3. Get existing emulator configuration, set desired configuration, and finally get (presumably) new configuration.
4. Command a finite set of 4 scans and [saves collected scan data](#61-saved-files) to 'finite_scans.prd'.
5. Command a continuous collection mode and [saves collected scan data](#61-saved-files) to 'continuous_scans.prd'.
6. Wait for user to command emulator to stop scanning with a non-zero value posted to ['control_radar'](#511-continuous-scan-usage).
7. Request a emulator reboot and wait for completion.
8. Get emulator configuration.
9. Disconnect from radar.
10. [Unpack](#62-unpacking-saved-files) collected data.

## 5.4. Input/Parameter Files
In the interest of simplifying the use of this codebase and the C2 of a MRM, only a limited subset of parameters are exposed to users. Specifically, the [settings.yml](settings.yml) file captures these parameters. Any settings not exposed to users via said settings file, [command line calls](#52-controlpy), or [scripts](#53-emulator_test_driverpy) requires further explanation not provided here.

### 5.4.1. [settings.yml](settings.yml)
[settings.yml](settings.yml) specifies three (3) main settings categories:
1. MRM collection/scan settings
2. MRM configuration
3. Host software timeouts

Included in this codebase is an example/template of [settings.yml](settings.yml) which is shown below. Explanations of each available setting is included in the comments of this file.
```yaml
# Collection settings
dT_0: 0 # Path delay through the antennas (ns)
range_start: 10 # One way range at which to start the scan (m)
range_stop: 60 # One way range at which to stop the scan (m)
tx_gain_ind: 63 # Transmit gain index from 0 (lowest) - 63 (highest)
pii: 11 # Pulse integration index from 6 (lowest) - 15 (highest)

# Less used settings
code_channel: 0 # Code channel from 0 - 10; used to deconflict multiple radars
node_id: 1 # Node ID from 1 to (2^32 - 1); avoid 0 and 2^32
persist_flag: 0 # Configuration persistence flag; 0 to not persist, 1 to persist
quick_look_num_scans: 200 # Number of scans to perform in quick-look

# Timing settings
comm_check_timeout: 1 # Time (s) allowed to successfully request radar communications check
reboot_request_timeout: 1 # Time (s) allowed to successfully request reboot
get_health_timeout: 1 # Time (s) allowed to successfully get radar health
set_config_timeout: 1 # Time (s) allowed to successfully set radar configuration
get_config_timeout: 1 # Time (s) allowed to successfully get radar configuration
scan_request_timeout: 1 # Time (s) allowed to successfully send scan request
read_scan_data_timeout: 2 # Time (s) allowed between consecutive packets
read_residual_timeout: 5 # Time (s) allowed to read residual streaming data before dropping scans
```

[**Go to Top**](#1-table-of-contents)

# 6. Scan Data
Scan data generated by the MRM is serialized in the format described by "MRM_SCAN_INFO" message in section 3.21 of the [API](https://github.com/bwsiuassar/documentation/blob/master/PulsON%20440/320-0298E-MRM-API-Specification.pdf). The scan data is transmitted as a series of these messages to the Host who is then responsible for deserializing it and any subsequent handling. In the case of this codebase, the Host software deserializes the received scan data and saves it to disk in a format that is more easily accessed by Python based code. The subsequent subsections detail both the [saved file format](#61-saved-files) and also the available method to [unpack or read said save file](#62-unpacking-saved-files).

## 6.1. Saved Files
Saved scan data files contain two (2) main components included in the following order:
1. The MRM configuration under which the scan data was collected.
    - Retrieved from the MRM via the "MRM_GET_CONFIG_REQUEST" and "MRM_GET_CONFIG_CONFIRM" detailed in sections 3.3 and 3.4 of the [API](https://github.com/bwsiuassar/documentation/blob/master/PulsON%20440/320-0298E-MRM-API-Specification.pdf), respectively.
    - "MRM_GET_CONFIG_CONFIRM" message specifies the contents and format of the MRM configuration and is included in saved scan data files without modification.
2. All received "MRM_SCAN_INFO" messages as defined in section 3.21 of the [API](https://github.com/bwsiuassar/documentation/blob/master/PulsON%20440/320-0298E-MRM-API-Specification.pdf) without modification.
    - Included in order received by Host software from MRM. 

This in effect means saved scan data files generated by this codebase are a "MRM_GET_CONFIG_CONFIRM" message followed by whatever number of "MRM_SCAN_INFO" messages generated by the MRM for this particular scan request. 

These components are saved or serialized to file as binary which means that they must be read or deserialized in order to retrieve the human-interpretable values contained within, e.g., the actual numeric scan data. Within the context of this codebase, this process is described next.

## 6.2. Unpacking Saved Files
Unpacking or reading saved scan data files is simply a matter of deserializing the binary sequence written by the Host software. This codebase implements this functionality in [unpack.py](unpack.py). We refer users to the help documentation of the module for usage and options including various visualizations of the scan data.

## 6.3 Displaying an RTI Plot
Users can either choose to use the -v flag to visualize an RTI when unpacking or use the [display_rti.py](display_rti.py) script to display a more deatiled RTI on already unpacked pickle files. This is a standalone script.

[**Go to Top**](#1-table-of-contents)

# 7. Logging
This codebase's logging is implemented using the standard Python [logging](https://docs.python.org/3/howto/logging.html) functionality. Configuration of the logger is done via [log_config.yml](log_config.yml) which specifies a dictionary that follows a specific [schema](https://docs.python.org/3/library/logging.config.html#logging-config-dictschema). In its default configuration, logs are output both to console via `ext://sys.stdout` and to the file "pulson440.log". 

[**Go to Top**](#1-table-of-contents)

# 8. Credits
Credit for this codebase goes to the following persons (in alphabetical order):
- Ramamurthy Bhagavatula
- Michael Riedl

[**Go to Top**](#1-table-of-contents)
