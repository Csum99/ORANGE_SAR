# 1. Table of Contents
- [1. Table of Contents](#1-table-of-contents)
- [2. Description](#2-description)
  - [2.1 SAR Backprojection](#21-sar-backprojection)
  - [2.2. SAR Data Simulation](#22-sar-data-simulation)
  - [2.5. Notes/Cautions](#25-notescautions)
- [3. Directory Tree](#3-directory-tree)
  - [3.1. Files of Note](#31-files-of-note)
- [4. Prerequisites](#4-prerequisites)
  - [4.1. Python/Modules](#41-pythonmodules)
    - [4.1.1. conda](#411-conda)
    - [4.1.2. pip](#412-pip)
- [5. Usage and Behavior](#5-usage-and-behavior)
  - [5.1. backprojection.py](#51-backprojectionpy)
    - [5.1.1. Arguments](#511-arguments)
  - [5.2. simulate_sar_data.py](#52-simulate_sar_datapy)
    - [5.2.1. Arguments](#521-arguments)
    - [5.2.2. Simulation Parameters Format](#522-simulation-parameters-format)
      - [5.2.2.1. Point Scatterers](#5221-point-scatterers)
      - [5.2.2.2. Image](#5222-image)
  - [5.3 Data Format](#53-data-format)
- [6. Examples](#6-examples)
- [7. Credits](#7-credits)

# 2. Description
This codebase provides two (2) main pieces of functionality:
1. Synthetic Aperture Radar (SAR) image formation via a backprojection approach.
2. Simulation of SAR data compatible with available backprojection method so as to generate corresponding SAR imagery.

This README provides a very basic explanation of the theory and design of these functionalities and focuses on explaining how to use these both independently and together. For a more detailed understanding of said theory and design, we refer users to the lecture material of the Beaver Works Summer Institute (BWSI) Unmanned Aerial System-SAR (UAS-SAR) course or any one of many available radar and SAR texts easily found online.

## 2.1 SAR Backprojection
Backprojection is a method for generating SAR imagery from received radar signals under fairly minimal assumptions and constraints. It is this reduced set of assumptions and constraints that makes it well suited for the BWSI UAS-SAR course. [backprojection.py](backprojection.py) implements this functionality in a number of ways that trade image quality and image formation speed.

Furthermore, we include some additional constraints in order to further simplify the concepts that must be understood. These constraints are as follow:
- Radar signals to be processed into SAR imagery are real-valued and amplitude-only which does limit the maximum SAR image "quality" that can be achieved.

## 2.2. SAR Data Simulation
A series of SAR data simulation options are available through the methods implemented in [simulate_sar_data.py](simulate_sar_data.py). Given the sheer complexity of simulating a "true" electromagnetic phenomena like radar in general or SAR more specifically, these simulations are extremely simple. In order to realize this, many simplifications and assumptions are made including the following ones:
- All effects of realistic scattering factors (e.g., incidence angle, material reflectivity, polarization, etc.) of any discrete scatterer are collectively modeled as a single RCS value.
- No medium of propagation (equivalently atmospheric) effects are modeled, i.e., world is simulated as a vacuum.
- Ground plane or earth is flat, i.e., no curvature.

With these simplifications in place, the following design choices are also made:
- Received SAR signal data is modeled as a sinc function (whose width is determined by the specified bandwidth) on a simple, single frequency carrier wave.
- Generated SAR images are limited to spanning the ground place.
- The X-Y-Z coordinate system is right-handed with the X-Y plane defining the ground planes and the positive Z-axis specifying the altitude of any point in question.

With these assumptions and basic approach, the following basic simulation options are available to users:
- Simulation of one or more specified point (isotropic) scatterer(s).
- Simulation of an grayscale (single-channel) image such that its individual pixels are each treated as discrete point scatterers whose RCS is proportional to their pixel value.

## 2.5. Notes/Cautions
- **YAML Usage/Familiarity**
  
  This codebase uses [YAML](https://yaml.org/) for all configuration and parameterization needs. It is recommended that users have at least a basic familiarity with YAML in order to understand and utilize these aspects of the codebase.

[**Go to Top**](#1-table-of-contents)

# 3. Directory Tree
```console
.
├── images
│   ├── BobShinBeaver.jpg
│   ├── monalisa.jpg
│   ├── probe.jpg
│   └── scream.jpg
├── params
│   ├── bobshinbeaver.yml
│   ├── example.yml
│   ├── lisa_kelley.yml
│   ├── mit.yml
│   ├── monalisa.yml
│   ├── probe.yml
│   ├── starry.yml
│   └── time_delay.yml
├── testing
│   ├── monalisa.yml
│   └── starry.yml
├── __init__.py
├── backprojection.py
├── conda_environment.yml
├── constants.py
├── interactive_single_scan.py
├── package_results.py
├── pip_requirements.txt
├── README.md
├── simulate_sar_data.py
└── tests.py
```

## 3.1. Files of Note
- Source
  - [backprojection.py](backprojection.py) - SAR backprojection image formation implementation.
  - [simulate_sar_data.py](simulate_sar_data.py) - SAR data simulation implementation.

[**Go to Top**](#1-table-of-contents)

# 4. Prerequisites
## 4.1. Python/Modules
The following lists the required Python modules to utilize this codebase.

| Required Module                                      | Minimum Tested Version |
| :--------------------------------------------------- | :--------------------- |
| [Python](https://www.python.org/)                    | 3.8.5                  |
| [imageio](https://imageio.readthedocs.io/en/stable/) | 2.9.0                  |
| [matplotlib](https://matplotlib.org/)                | 3.3.2                  |
| [NumPy](https://numpy.org/)                          | 1.19.2                 |
| [PyYAML](https://pyyaml.org/)                        | 5.3.1                  |
| [scikit-image](https://scikit-image.org/)            | 0.17.2                 |
| [SciPy](https://www.scipy.org/)                      | 1.5.2                  |

Provided in this software package are configuration files that will allow you to meet these requirements using either the [conda](https://docs.conda.io/en/latest/) or [pip](https://pip.pypa.io/en/stable/) package managers. Listed below are the steps to meet and use the requirements for each package manager. Please use only one of these options to avoid creating package/environment conflicts

### 4.1.1. [conda](https://docs.conda.io/en/latest/)
In addition to installing requested modules and necessary dependencies, conda can install these items in a [virtual environment](https://realpython.com/python-virtual-environments-a-primer/) that is useful for minimizing the complexity of your development and execution environment. The following steps do exactly this.
  1. [Create 'backprojection' environment from environment file](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file) - `conda env create -f conda_environment.yml`
  2. [Activate 'backprojection' environment]((https://docs.conda.io/en/latest/)) - `conda activate backprojection`

### 4.1.2. [pip](https://pip.pypa.io/en/stable/)
  1. [Install from requirements file](https://pip.pypa.io/en/stable/user_guide/#requirements-files) - `pip install -r pip_requirements.txt`

[**Go to Top**](#1-table-of-contents)

# 5. Usage and Behavior

## 5.1. [backprojection.py](backprojection.py)

### 5.1.1. Arguments
`data_file`
- **Description/Purpose:** Path to file containing [pickled](https://docs.python.org/3/library/pickle.html) scan data.
- **Type**: str
- **Choices/Requirements:** 
  - Expected content is a with the keys 'scan_data', 'platform_pos', and 'range_bins'.

`x_min`
- **Description/Purpose:** Minimum of SAR image pixels' X-coordinates (m).
- **Type**: float

`x_max`
- **Description/Purpose:** Maximum of SAR image pixels' X-coordinates (m).
- **Type**: float

`x_res`
- **Description/Purpose:** SAR image pixels' resolution (m) along the X-axis.
- **Type**: float

`y_min`
- **Description/Purpose:** Minimum of SAR image pixels' Y-coordinates (m).
- **Type**: float

`y_max`
- **Description/Purpose:** Maximum of SAR image pixels' Y-coordinates (m).
- **Type**: float

`y_res`
- **Description/Purpose:** SAR image pixels' resolution (m) along the Y-axis.
- **Type**: float

`--sar_image_file`
- **Description/Purpose:** File to save generated SAR image to.
- **Type**: str
- **Choices/Requirements:** 
  - If not specified, generated SAR image is not saved.
- **Default:** None

`--method`
- **Description/Purpose:** Backprojection method/implementation to use.
- **Type**: str
- **Choices/Requirements:** 
  - Choices are 'shift', 'interp', and 'fourier'.
- **Default:** 'interp'

`--num_processes`
- **Description/Purpose:** Number of multiprocessing processes to use.
- **Type**: int
- **Default:**  1

`--z_offset`
- **Description/Purpose:** Constant Z-axis offset (m) of SAR image pixels' coordinates.
- **Type**: float
- **Default:**  0

`--center_freq`
- **Description/Purpose:** Center frequency (Hz) of radar.
- **Type**: float
- **Choices/Requirements:** 
  - Must be specified if using 'fourier' as `--method` argument.

`--no_visuals`
- **Description/Purpose:** Do not display generated SAR image.
- **Type**: flag

`--progress_bar`
- **Description/Purpose:** Show SAR image generation progress bar.
- **Type**: flag

## 5.2. [simulate_sar_data.py](simulate_sar_data.py)

### 5.2.1. Arguments

### 5.2.2. Simulation Parameters Format
A user specifies the parameters of the simulation in the [YAML](https://yaml.org/) file specified by the user with the `--sim_params_file` argument. Captured in these parameters are both parameters common to any available simulation mode and those specific to each of them. The mode specific parameters are described in subsequent subsections with the common ones described next.

`sim_type`
- **Description/Purpose:** Simulation type.
- **Type**: str
- **Choices/Requirements:** 
  - Choices are 'point', 'image', and 'image_misaligned'.

`center_freq`
- **Description/Purpose:** Radar signal center frequency (Hz).
- **Type**: int
- **Choices/Requirements:** 
  - If user is modeling PulsON 440 used in BWSI UAS-SAR course, recommended value is 4062500000 Hz (equivalently 4.0625 GHz).

`bandwidth`
- **Description/Purpose:** Radar signal bandwidth (Hz).
- **Type**: int
- **Choices/Requirements:** 
  - If user is modeling PulsON 440 used in BWSI UAS-SAR course, recommended value is 2437500000 Hz (equivalently 2.4375 GHz).

`scan_rate`
- **Description/Purpose:** Radar scanning or scan generation rate (Hz).
- **Type**: int

`duration`
- **Description/Purpose:** Total radar scanning duration or equivalently SAR data collection duration (s).
- **Type**: int

`range_min`
- **Description/Purpose:** Radar sampling minimum range (m).
- **Type**: int

`range_max`
- **Description/Purpose:** Radar sampling maximum range (m).
- **Type**: int

`platform_init_pos`
- **Description/Purpose:** Initial (X, Y, Z) platform position (m).
- **Type**: list

`platform_vel`
- **Description/Purpose:** Platform's (X, Y, Z) velocity (m/s).
- **Type**: list

`prop_loss`
- **Description/Purpose:** Specifies whether (True) or not (False) to include range propagation loss in simulation.
- **Type**: boolean

`add_noise`
- **Description/Purpose:** Specifies whether (True) or not (False) to add AWGN noise to simulated data.
- **Type**: boolean

`noise_magnitude`
- **Description/Purpose:** Specifies the variance of AWGN noise added if so `add_noise` is True.
- **Type**: float

For illustration, the following YAML snippet is provided. Note that this snippet alone is not sufficient to use any of the available simulation modes. The remainder of the necessary parameters are described in the next subsections.

```yaml
# Simulation type; options are ['point', 'image', 'image_misaligned']
sim_type: 'point'

# Radar/waveform parameters
center_freq: 4062500000 # (Hz)
bandwidth: 2437500000 # (Hz)
scan_rate: 25 # (Hz)
duration: 8 # (seconds)
range_min: 3 # (m)
range_max: 50 # (m)

# Platform motion parameters
platform_init_pos: [-20, -15, 5] # Relative to image center; [X, Y, Z] (meters)
platform_vel: [5, 0, 0] # [X, Y, Z] (meters/second)

# Propagation loss
prop_loss: False

# Noise parameters
add_noise: False
noise_magnitude: 4
```



#### 5.2.2.1. Point Scatterers
 each desired point scatterer in terms of its position and RCS.

#### 5.2.2.2. Image


## 5.3 Data Format
Both [backprojection.py](#51-backprojectionpy) and [simulate_sar_data.py](#52-simulate_sar_datapy) both respectively utilize and produce radar scan data and associated metadata of the same format. Please note that this data format was solely defined for this codebase has no meaningful basis or interdependence with other aspects of the BWSI UAS-SAR course (e.g., other codebases).

The three (3) main components of the radar scan data and associated metadata are described in the table below. All are either matrices (2-D arrays) or vectors (1-D arrays) whose dimensions map to specific meanings. These components are stored as key-value pairs in a standard [Python dictionary](https://docs.python.org/3/tutorial/datastructures.html#dictionaries) which is in turn serialized to file by the standard [Python pickle](https://docs.python.org/3/library/pickle.html) module.

| Component          | Description                                                                                                                                  | Dictionary Key | Dimensions                             |
| :------------------| :------------------------------------------------------------------------------------------------------------------------------------------- | :------------- | :------------------------------------- |
| Radar scan data    | Scan-by-scan (pulse-by-pulse) radar data from which to generate SAR image.                                                                   | 'scan_data'    | Number of scans x Number of range bins |
| Platform positions | Scan-by-scan (pulse-by-pulse) position or platform with which to generate SAR image.                                                         | 'platform_pos' | Number of scans x 3                    |
| Range bins         | Range bins or range values at which each corresponding sample of a radar scan is taken. Length is equal to number of columns in 'scan_data'. | 'range_bins'   | Number of range bins x 1               |

[**Go to Top**](#1-table-of-contents)

# 6. Examples

[**Go to Top**](#1-table-of-contents)

# 7. Credits
Credit for this codebase goes to the following persons (in alphabetical order):
- Ramamurthy Bhagavatula
- Winston Liu
- Mason Mitchell
- Brian Nowakowski
- Michael Riedl

[**Go to Top**](#1-table-of-contents)

