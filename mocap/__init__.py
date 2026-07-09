#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""mocap package initialization."""

# Expose modules to package
from mocap import data_processor
from mocap import calibration_stationary
from mocap import calibration_manual
from mocap import calibration_auto
from mocap import utils

__all__ = ['data_processor', 'calibration_stationary', 'calibration_manual', 'calibration_auto', 'utils'] 