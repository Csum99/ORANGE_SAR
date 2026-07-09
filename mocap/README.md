# Motion Capture and Radar Data Calibration System

# 1. Table of Contents
- [1. Table of Contents](#1-table-of-contents)
- [2. Description](#2-description)
  - [2.1. Host-MRM-Mocap Interaction Model](#21-host-mrm-mocap-interaction-model)
  - [2.2. Calibration Modes](#22-calibration-modes)
    - [2.2.1 Stationary Radar Calibration Mode](#221-stationary-radar-calibration-mode)
    - [2.2.2 Automatic Radar Calibration Mode (Matched Filtering)](#222-automatic-radar-calibration-mode-matched-filtering)
    - [2.2.3 Manual Radar Calibration Mode](#223-manual-radar-calibration-mode)
  - [2.3. Notes/Cautions](#23-notescautions)
- [3. Directory Tree](#3-directory-tree)
  - [3.1. Files of Note](#31-files-of-note)
- [4. Prerequisites](#4-prerequisites)
  - [4.1. Python/Modules](#41-pythonmodules)
    - [4.1.1. conda](#411-conda)
    - [4.1.2. pip](#412-pip)
  - [4.2. Data Requirements](#42-data-requirements)
- [5. Usage and Behavior](#5-usage-and-behavior)
  - [5.1 Basic Usage](#51-basic-usage)
  - [5.2 calibration_stationary.py](#52-calibration_stationarypy)
    - [5.2.1 Arguments](#521-arguments)
  - [5.3 calibration_auto.py](#53-calibration_autopy)
    - [5.3.1 Arguments](#531-arguments)
  - [5.4 calibration_manual.py](#54-calibration_manualpy)
    - [5.4.1 Arguments](#541-arguments)
  - [5.5. Input/Parameter Files](#55-inputparameter-files)
- [6. Calibration Data](#6-calibration-data)
  - [6.1. Input Data Files](#61-input-data-files)
  - [6.2. Output Data Files](#62-output-data-files)
  - [6.3. Logging](#63-logging)
- [7. Interactive Features](#7-interactive-features)
- [8. Troubleshooting](#8-troubleshooting)
- [9. Credits](#9-credits)

[**Go to Top**](#1-table-of-contents)

# 2. Description

This software implements motion capture and radar data calibration for the Time Domain PulsON 440 Monostatic Radar Module (MRM) and OptiTrack motion capture system. The system provides tools to align motion capture data with radar scan data, enabling precise tracking and analysis of moving objects in radar imagery.

The calibration system addresses the fundamental challenge of synchronizing two different data streams:
- **Radar Data**: Scan data from the PulsON 440 radar
- **Motion Capture Data**: 3D position tracking data from reference objects and platform positions

## 2.1. Radar-Mocap Interaction Model

The interaction between the calibration system and the data sources follows a data processing model where:

1. **Data Loading**: The system loads pre-recorded radar and motion capture data from pickle files
2. **Data Processing**: Radar data is converted to dB scale and timestamps are normalized
3. **Alignment Analysis**: The system analyzes temporal relationships between the two data streams
4. **Parameter Adjustment**: Users can interactively or automatically adjust parameters for optimal alignment
5. **Verification**: The system generates verification plots and saves aligned data

This model assumes that both radar and motion capture data have been previously collected and saved in the appropriate pickle format.

## 2.2. Calibration Modes

The system supports three distinct calibration modes depending on the radar deployment scenario and user preference.

### 2.2.1 Stationary Radar Calibration Mode

The stationary radar calibration mode assumes that the radar is initially stationary for a baseline period. This mode is designed for scenarios where:

1. The radar starts in a fixed position
2. The radar begins moving after an initial stationary period
3. Motion capture data tracks both the radar platform and reference objects

**Processing Sequence:**
1. **Baseline Analysis**: Uses the first N scans to establish a baseline for radar movement detection
2. **Movement Detection**: Applies Mean Absolute Difference (MAD) analysis to identify when radar movement begins
3. **Platform Movement Detection**: Identifies sustained movement periods in motion capture data using velocity thresholds
4. **Data Alignment**: Resamples motion capture data to match radar timestamps

### 2.2.2 Automatic Radar Calibration Mode (Matched Filtering)

The automatic radar calibration mode (`calibration_auto.py`) handles scenarios where the radar is moving throughout the entire data collection period. This mode uses a matched filtering approach to automatically align the radar and motion capture data, requiring no manual adjustment.

**Processing Sequence:**
1. **Matched Filtering Alignment**: Uses a 2D template (built from mocap trajectory) and slides it over the radar data to find the best alignment automatically
2. **Reference Object Tracking**: Uses known reflector positions to verify alignment quality
3. **Movement Period Detection**: Identifies relevant movement periods for analysis
4. **Data Resampling**: Ensures motion capture data matches radar sampling rate

### 2.2.3 Manual Radar Calibration Mode

The manual radar calibration mode (`calibration_manual.py`) is for scenarios where the user wants to manually adjust the alignment and where the radar is moving throughout the entire data collection period. This mode provides interactive lag adjustment (keyboard controls) and visual feedback.

**Processing Sequence:**
1. **Manual Lag Adjustment**: User interactively adjusts the lag between radar and mocap data using keyboard controls and visual feedback
2. **Reference Object Tracking**: Uses known reflector positions to verify alignment quality
3. **Movement Period Detection**: Identifies relevant movement periods for analysis
4. **Data Resampling**: Ensures motion capture data matches radar sampling rate

## 2.3. Notes/Cautions

- **Data Quality Requirements**
  Both radar and motion capture data must be properly formatted and contain all required fields. Missing or corrupted data will cause the calibration to fail.
- **Interactive Parameter Adjustment**
  The system provides interactive parameter adjustment for optimal results in manual and stationary modes. Use `--skip-interactive` to disable.
- **Memory Requirements**
  Large datasets may require significant memory. The system loads entire datasets into memory for processing.
- **File Path Dependencies**
  The system expects specific file structures and will create output directories as needed. Ensure proper file permissions.
- **Matplotlib Backend Requirements**
  Interactive features require a matplotlib backend that supports GUI interactions. In headless environments, use the `--skip-interactive` flag.

[**Go to Top**](#1-table-of-contents)

# 3. Directory Tree

```console
mocap/
├── __init__.py
├── pip_requirements.txt
├── conda_environment.yml
├── README.md
├── utils.py
├── calibration_stationary.py
├── calibration_auto.py
├── calibration_manual.py
└── data_processor.py
```

## 3.1. Files of Note

- **Configuration**
  - [pip_requirements.txt](pip_requirements.txt) - Python package dependencies for the calibration system
  - [conda_environment.yml](conda_environment.yml) - Conda environment configuration file for setting up the required Python environment
- **Core Utilities**
  - [utils.py](utils.py) - Shared utility functions for data loading, processing, and visualization
- **Processing Scripts**
  - [data_processor.py](data_processor.py) - Fixing the radar range offset and mocap coordinate system
- **Calibration Scripts**
  - [calibration_stationary.py](calibration_stationary.py) - Stationary radar calibration processor with baseline movement detection
  - [calibration_auto.py](calibration_auto.py) - Automatic radar calibration using matched filtering for non-stationary radar scenarios
  - [calibration_manual.py](calibration_manual.py) - Manual radar calibration with interactive lag adjustment for non-stationary radar scenarios

[**Go to Top**](#1-table-of-contents)

# 4. Prerequisites

## 4.1. Python/Modules

The following lists the required Python modules to run the calibration system.

| Required Module                                 | Minimum Tested Version |
| :---------------------------------------------- | :--------------------- |
| [Python](https://www.python.org/)               | 3.8.5                  |
| [NumPy](https://numpy.org/)                     | 1.24.0                 |
| [Pandas](https://pandas.pydata.org/)            | 2.0.0                  |
| [SciPy](https://www.scipy.org/)                 | 1.10.0                 |
| [Matplotlib](https://matplotlib.org/)           | 3.7.0                  |
| [PyYAML](https://pyyaml.org/)                   | 6.0.0                  |
| [pprintpp](https://github.com/wolever/pprintpp) | 0.4.0                  |


### 4.1.1. [conda](https://docs.conda.io/en/latest/)

In addition to installing requested modules and necessary dependencies, conda can install these items in a [virtual environment](https://realpython.com/python-virtual-environments-a-primer/) that is useful for minimizing the complexity of your development and execution environment. The following steps do exactly this.

1. [Create 'mocap' environment from environment file](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file) - `conda env create -f conda_environment.yml`
2. [Activate 'mocap' environment](https://docs.conda.io/en/latest/) - `conda activate mocap`

Alternatively, create manually:
```bash
conda create -n mocap python=3.8
conda activate mocap
conda install numpy pandas scipy matplotlib pyyaml
```

### 4.1.2. [pip](https://pip.pypa.io/en/stable/)

1. [Install from requirements file](https://pip.pypa.io/en/stable/user_guide/#requirements-files) - `pip install -r pip_requirements.txt`

## 4.2. Data Requirements

The calibration system requires two types of input data in pickle format:

**Radar Data Requirements:**
- `timestamps`: Array of radar scan timestamps (typically in milliseconds)
- `range_bins`: Array of range bin distances (in meters)
- `scan_data`: 2D array of radar scan data (raw amplitude values)

**Motion Capture Data Requirements:**
- `timestamps`: Array of motion capture sample timestamps (typically in milliseconds)
- `platform_pos`: Array of platform positions (Nx3 array with X, Y, Z coordinates)
- `ref_obj1`: Reference object 1 position (3D coordinates in meters)
- `ref_obj2`: Reference object 2 position (3D coordinates in meters)

**Data Quality Requirements:**
- Timestamps should be monotonically increasing
- Platform positions should be in the same coordinate system as reference objects
- Reference objects should be stationary reflectors with known positions
- Data should cover overlapping time periods

[**Go to Top**](#1-table-of-contents)

# 5. Usage and Behavior

The usage and behavior of the calibration system is designed to be flexible and accommodate different deployment scenarios. The system provides command-line interfaces for all calibration modes with extensive parameter control.

## 5.1 Basic Usage

The calibration system is designed to be used with pre-recorded radar and motion capture data. The following is the basic, ordered sequence of events that are expected to occur:

1. Process radar and motion capture data for calibration
2. Command line invocation of the appropriate calibration script
3. Interactive parameter adjustment (unless skipped)
4. Data processing and alignment
5. Generation of verification plots and output data

### 5.1.1 Interactive Parameter Adjustment

Both calibration scripts provide interactive GUI parameter adjustment capabilities (except for calibration_auto.py). In this mode:

1. The system displays plots showing the current parameter settings
2. Users can adjust parameters using sliders or keyboard controls
3. Plots update in real-time to show the effects of parameter changes
4. Users confirm or cancel the parameter settings
5. Processing continues with the confirmed parameters

To skip interactive adjustment, use the `--skip-interactive` flag.

## 5.2 [calibration_stationary.py](calibration_stationary.py)

[calibration_stationary.py](calibration_stationary.py) is designed to calibrate data from scenarios where the radar is initially stationary.

### 5.2.1 Arguments

`radar_file`
- **Description/Purpose:** Path and name of pickle file containing radar data.
- **Type**: string
- **Required:** Yes

`mocap_file`
- **Description/Purpose:** Path and name of pickle file containing motion capture data.
- **Type**: string
- **Required:** Yes

`--baseline-scans`
- **Description/Purpose:** Number of initial scans to use as baseline for movement detection.
- **Type**: int
- **Choices/Requirements:** Must be positive integer less than total number of scans.
- **Default:** 20

`--k-multiplier`
- **Description/Purpose:** Multiplier for standard deviation threshold in radar movement detection.
- **Type**: float
- **Choices/Requirements:** Positive float value.
- **Default:** 20.0

`--velocity-threshold`
- **Description/Purpose:** Velocity threshold for motion capture movement detection.
- **Type**: float
- **Choices/Requirements:** Positive float value in units of position change per frame.
- **Default:** 0.0005

`--window-size`
- **Description/Purpose:** Window size for sustained movement detection in motion capture data.
- **Type**: int
- **Choices/Requirements:** Positive integer less than total number of frames.
- **Default:** 14

`--save-plots`
- **Description/Purpose:** Save all plots to PNG files.
- **Type**: flag
- **Choices/Requirements:** Optional flag.

`--save-data`
- **Description/Purpose:** Save processed data to pickle file.
- **Type**: flag
- **Choices/Requirements:** Optional flag.

`--output-name`
- **Description/Purpose:** Output filename base name for saved files.
- **Type**: string
- **Choices/Requirements:** Valid filename string.
- **Default:** 'run_0'

`--skip-interactive`
- **Description/Purpose:** Skip interactive parameter adjustment.
- **Type**: flag
- **Choices/Requirements:** Optional flag.

## 5.3 [calibration_auto.py](calibration_auto.py)

[calibration_auto.py](calibration_auto.py) is designed to calibrate data from scenarios where the radar is moving throughout the data collection period. This script uses a matched filtering approach to automatically align the radar and motion capture data, requiring no manual adjustment.

### 5.3.1 Arguments

`radar_file`
- **Description/Purpose:** Path and name of pickle file containing radar data.
- **Type**: string
- **Required:** Yes

`mocap_file`
- **Description/Purpose:** Path and name of pickle file containing motion capture data.
- **Type**: string
- **Required:** Yes

`--sigma`
- **Description/Purpose:** Sigma for Gaussian smoothing of mocap template.
- **Type**: float
- **Choices/Requirements:** Positive float value.
- **Default:** 0.5

`--velocity-threshold`
- **Description/Purpose:** Velocity threshold for motion capture movement detection.
- **Type**: float
- **Choices/Requirements:** Positive float value in units of position change per frame.
- **Default:** 0.0005

`--window-size`
- **Description/Purpose:** Window size for sustained movement detection in motion capture data.
- **Type**: int
- **Choices/Requirements:** Positive integer less than total number of frames.
- **Default:** 14

`--save-plots`
- **Description/Purpose:** Save all plots to PNG files.
- **Type**: flag
- **Choices/Requirements:** Optional flag.

`--save-data`
- **Description/Purpose:** Save processed data to pickle file.
- **Type**: flag
- **Choices/Requirements:** Optional flag.

`--output-name`
- **Description/Purpose:** Output filename base name for saved files.
- **Type**: string
- **Choices/Requirements:** Valid filename string.
- **Default:** 'run_0'

`--skip-interactive`
- **Description/Purpose:** Skip interactive parameter adjustment.
- **Type**: flag
- **Choices/Requirements:** Optional flag.

## 5.4 [calibration_manual.py](calibration_manual.py)

[calibration_manual.py](calibration_manual.py) is designed for manual alignment of radar and mocap data. The user interactively adjusts the lag between the two data streams using keyboard controls and visual feedback.

### 5.4.1 Arguments

`radar_file`
- **Description/Purpose:** Path and name of pickle file containing radar data.
- **Type**: string
- **Required:** Yes

`mocap_file`
- **Description/Purpose:** Path and name of pickle file containing motion capture data.
- **Type**: string
- **Required:** Yes

`--velocity-threshold`
- **Description/Purpose:** Velocity threshold for motion capture movement detection.
- **Type**: float
- **Choices/Requirements:** Positive float value in units of position change per frame.
- **Default:** 0.0005

`--window-size`
- **Description/Purpose:** Window size for sustained movement detection in motion capture data.
- **Type**: int
- **Choices/Requirements:** Positive integer less than total number of frames.
- **Default:** 14

`--save-plots`
- **Description/Purpose:** Save all plots to PNG files.
- **Type**: flag
- **Choices/Requirements:** Optional flag.

`--save-data`
- **Description/Purpose:** Save processed data to pickle file.
- **Type**: flag
- **Choices/Requirements:** Optional flag.

`--output-name`
- **Description/Purpose:** Output filename base name for saved files.
- **Type**: string
- **Choices/Requirements:** Valid filename string.
- **Default:** 'run_0'

`--skip-interactive`
- **Description/Purpose:** Skip interactive parameter adjustment.
- **Type**: flag
- **Choices/Requirements:** Optional flag.

## 5.5. Input/Parameter Files

The calibration system does not use external parameter files. All parameters are specified via command-line arguments or adjusted interactively during execution.

[**Go to Top**](#1-table-of-contents)

# 6. Calibration Data

## 6.1. Input Data Files

The calibration system expects input data in pickle format with specific structures.

**Radar Data File Structure:**
```python
{
    'timestamps': np.array,  # Radar scan timestamps (milliseconds)
    'range_bins': np.array,  # Range bin distances (meters)
    'scan_data': np.array    # 2D radar scan data (raw amplitude)
}
```

**Motion Capture Data File Structure:**
```python
{
    'timestamps': np.array,      # Motion capture timestamps (milliseconds)
    'platform_pos': np.array,    # Platform positions (Nx3 array, meters)
    'ref_obj1': np.array,        # Reference object 1 position (3D, meters)
    'ref_obj2': np.array         # Reference object 2 position (3D, meters)
}
```

**File Naming Conventions:**
- Radar data files typically use `.pkl` extension
- Motion capture data files typically use `.pkl` extension
- Files should be named descriptively (e.g., `radar_run1.pkl`, `mocap_run1.pkl`)

## 6.2. Output Data Files

The calibration system generates several types of output files.

**Processed Data File:**
```python
{
    'scan_data': np.array,       # Aligned radar scan data (raw amplitude)
    'platform_pos': np.array,    # Aligned platform positions (Nx3, meters)
    'range_bins': np.array       # Range bin distances (meters)
}
```

**Plot Files (when --save-plots is used):**
- `{output_name}_calibration.png` - Calibration verification plot
- `{output_name}_radar_movement.png` - Radar movement detection plot (stationary mode)
- `{output_name}_rti.png` - Range-Time Intensity plot (stationary mode)
- `{output_name}_filter_template.png` - Plot of the sliding matched filter template

**File Locations:**
- Processed data files are saved to `../backprojection/` directory
- Plot files are saved to the current working directory
- All files use the specified `--output-name` as the base filename

## 6.3. Logging

Each calibration script automatically generates a detailed log file for every run, saved in the `logs/` folder. These logs are designed to provide a full audit trail for reproducibility and debugging.

**Log File Features:**
- **Location:** All logs are saved in the `logs/` subfolder of the project.
- **Naming Convention:** Log files are named according to the script and timestamp, e.g., `calibration_auto_YYYYMMDD_HHMMSS.log`.
- **Content:**
  - All input parameters (command-line arguments) used for the run
  - Initial data shapes for radar and motion capture data (before any processing)
  - All indices and parameters used for data cutting/trimming (e.g., start_index, end_index, lag, offset, velocity_threshold, window_size, baseline_scans, k_multiplier)
  - Final data shapes after all cuts/trims
  - Any alignment or movement detection parameters
  - The log is written incrementally as the script processes the data

[**Go to Top**](#1-table-of-contents)

# 7. Interactive Features

The calibration system provides extensive interactive features for parameter adjustment and visualization.

## 7.1. Stationary Radar Interactive Features

**Radar Movement Detection:**
- Slider for adjusting k-multiplier (1-100 range)
- Real-time plot updates showing MAD values and threshold
- Visual indication of detected movement points
- Confirm/Quit buttons for parameter acceptance

**Motion Capture Movement Detection:**
- Slider for velocity threshold (0.00001-0.002 range)
- Slider for window size (5-50 range)
- Real-time plot updates showing velocity changes
- Visual indication of detected movement start/end points
- Time information display in seconds

## 7.2. Manual Radar Interactive Features

**Alignment Adjustment:**
- Keyboard controls (UP/DOWN arrows) for lag adjustment (5 frames per press, 50 with shift)
- Real-time visualization of reference object trajectories
- RTI plot with overlaid trajectory lines
- Enter to confirm, Escape to cancel

## 7.3. Automatic Radar Interactive Features

**Matched Filtering:**
- Sigma parameter controls the width of the Gaussian template
- 2D template (from mocap trajectory) is automatically slid over radar data to find best alignment
- Plots of the template and verification overlays are generated automatically

[**Go to Top**](#1-table-of-contents)

# 8. Troubleshooting

## 8.1. Common Issues

**File Not Found Errors:**
- Ensure radar and motion capture files exist and are accessible
- Check file paths are correct and absolute if needed
- Verify file permissions allow reading

**Data Format Errors:**
- Ensure pickle files contain all required fields
- Check data types match expected formats
- Verify array shapes are correct

**Memory Errors:**
- Large datasets may exceed available memory
- Consider processing smaller time windows
- Close other applications to free memory

**Interactive Display Issues:**
- Ensure matplotlib backend supports GUI
- Use `--skip-interactive` in headless environments
- Check display settings in remote sessions

## 8.2. Parameter Adjustment Guidelines

**Radar Movement Detection (Stationary Mode):**
- Start with default k-multiplier (20.0)
- Increase for more sensitive detection
- Decrease for less sensitive detection
- Baseline scans should cover stationary period

**Motion Capture Movement Detection:**
- Velocity threshold depends on data quality and movement speed
- Window size should be large enough for sustained movement
- Adjust based on visual feedback from plots

**Manual Adjustment:**
- Make large adjustments (50-frame steps)
- Refine with small adjustments (5-frame steps)
- Verify alignment with reference object trajectories
- Check for consistent alignment across entire dataset

**Matched Filter Template Generation:**
- Sigma controls template width - start with 0.3 - 0.7
- Increase sigma for wider/smoother templates
- Decrease sigma for narrower/sharper templates
- Template width should roughly match expected signal width
- Verify template shape matches expected trajectory pattern
- Check alignment score distribution for optimal sigma

## 8.3. Data Quality Issues

**Poor Alignment:**
- Check reference object positions are accurate
- Verify coordinate system consistency
- Consider data quality and noise levels

**Missing Movement Detection:**
- Adjust sensitivity parameters
- Check data covers expected movement periods
- Verify movement is above noise floor

[**Go to Top**](#1-table-of-contents)

# 9. Credits

Credit for this codebase goes to the following persons (in alphabetical order):
- Calvin Zhou

[**Go to Top**](#1-table-of-contents) 