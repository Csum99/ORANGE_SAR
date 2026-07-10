# Radar Data Collection Guide

This guide explains how to collect radar data using the **ORANGE SAR**
software and convert the recorded radar data into a Python-readable
`.pkl` file for processing and visualization.


------------------------------------------------------------------------

## 1. Clone the Repository

``` bash
git clone https://github.com/Csum99/ORANGE_SAR.git
```

------------------------------------------------------------------------

## 2. Connect to the Radar Computer

Replace `username` and `ip_address` with your login credentials.

``` bash
ssh username@ip_address
```

------------------------------------------------------------------------

## 3. Navigate to the Radar Software

``` bash
cd ORANGE_SAR/pulson440
```

------------------------------------------------------------------------

## 4. Install Required Python Packages

``` bash
pip install -r pip_requirements.txt
```

> This only needs to be done once for a new Python environment.

------------------------------------------------------------------------

## 5. Start Data Collection

``` bash
python control.py --collect
```

The radar will continuously collect data until stopped.

------------------------------------------------------------------------

## 6. Stop Data Collection

Press **Ctrl + C** to stop the scan.

The collected radar data will be saved as a `.prd` file (for example,
`collect_1.prd`).

------------------------------------------------------------------------

## 7. Convert the Data

Convert the `.prd` file into a `.pkl` file for processing.

``` bash
python unpack.py collect_#.prd collect_#.pkl -v
```

Replace `#` with the appropriate scan number.

### Example

``` bash
python unpack.py collect_1.prd collect_1.pkl -v
```

The `-v` flag enables verbose output during conversion.
