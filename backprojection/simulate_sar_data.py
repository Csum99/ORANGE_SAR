#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SAR data simulation.

Simulates data needed to create a SAR image via backprojection. Intended to be compatible with 
backprojection.py.
"""

"""Listed below is the superset of key-value pairs that govern the simulation. The requirements on 
any given key-value pair depends on the type of simulation done.

platform_init_pos (array-like)
    Initial platform [X, Y, Z] position (m).
            
stationary_time (list)
    Stationary time before takeoff and after landing (s).
            
radar_offsets (list)
    Time offset (s) before takeoff and after landing at which radar is turned on and off, 
    respectively.
            
motion_offsets (list)
    Time offset (s) before turning radar and off at which motion capture is turned on and off, 
    respectively.
            
time_misalignment (float)
    Time misalignment (s) to be applied between the scan and motion capture times. 
            
radar_displacement (array-like)
    Displacement of the radar (m) from the motion capture reference point to be applied to the 
    motion captured position data.

platform_vel (array-like)
    Constant platform [X, Y, Z] velocity (m/s).
            
center_freq (float)
    Center frequency (Hz).
            
bandwidth (float)
    Bandwidth (Hz).
            
scan_rate (float)
    Scan/pulse repetition frequency (Hz).
            
duration (float)
    Simulation duration (s).
            
range_min (float)
    Minimum range (m) of scan/pulse returns.
            
range_max (float)
    Maximum range (m) of scan/pulse returns.
                
source_image (str)
    Path and name of image to use.

downsampling_factor (int)
    Downsampling factor.
            
image_center (array-like)
    [X, Y] coordinates (m) of image.
            
pixel_res (array-like)
    [X, Y] pixel resolution (m) of image.
            
pixel_thresholds (list)
    Upper and lower thresholds between 0 and 255 for which pixels above or below these values, 
    respectively, will be set to zero.
"""

__author__ = "Ramamurthy Bhagavatula, Brian Nowakowski, Robert Sweeney"
__version__ = "1.0"
__maintainer__ = "Ramamurthy Bhagavatula"
__email__ = "ramamurthy.bhagavatula@ll.mit.edu"

# Update path
from pathlib import Path
import sys

if Path("..//").resolve().as_posix() not in sys.path:
    sys.path.insert(0, Path("..//").resolve().as_posix())

# Import required modules and methods
import argparse
from common.constants import SPEED_OF_LIGHT
from common.helper_functions import deconflict_file, yes_or_no, is_valid_file, progress_bar
import imageio
from math import floor, ceil, sqrt
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
import pickle
from scipy.interpolate import interp1d
from scipy.spatial.distance import cdist
from skimage import transform
import time
import yaml


def read_sim_params(sim_params_file):
    """Reads simulation parameters from specified file.
    
    Args:
        sim_params_file (str)
            File from which to read simulation parameters. File contents are expected to be YAML 
            formatted and read into a dictionary using the yaml module. Valid contents are defined 
            by various other methods in this module.
    
    Returns:
        sim_params (dict)
            Simulation parameters read from sim_params_file.
    """
    # Load YAML formatted simulation parameters file
    with open(sim_params_file, 'r') as f:
        sim_params = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Read following simulation parameters from '{sim_params_file}' --> {sim_params}")
    return sim_params


def simulate_data(sim_params, show_progress_bar=False, num_threads=1):
    """Simulate SAR data based on specified parameters.
    
    Args:
        sim_params (dict)
            Simulation parameters. 'sim_type' key must be defined; remaining key-value pairs are 
            collectively governed by other methods invoked by this method.
            
        show_progress_bar (bool)
            Indicates whether or not to show progress bar. Defaults to False.
            
    Returns:
        sim_data (dict) 
            Simulated data, associated metadata, and originating simulation parameters; keys are 
            [scan_data, platform_pos, range_bins, sim_params].
            
    Raises:
        KeyError if sim_params['sim_type'] is unknown.
    """
    if sim_params['sim_type'] == 'point':
        sim_data = simulate_point_scatterers(sim_params, show_progress_bar)
    elif sim_params['sim_type'] == 'image':
        sim_data = simulate_image(sim_params, show_progress_bar, num_threads)
    elif sim_params['sim_type'] == 'image_misaligned':
        sim_data = simulate_image_misaligned(sim_params, show_progress_bar)
    else:
        raise KeyError("'scatterType' has unrecognized value of " 
                       f"'{sim_params['scattererType']}'")
    sim_data['sim_params'] = sim_params
    return sim_data


def simulate_point_scatterers(sim_params, show_progress_bar=False):
    """Simulate SAR data of a collection of discrete point scatters.
    
    Args:
        sim_params (dict)
            Simulation parameters. Refer to top-of-file comments for description of these 
            parameters and to method itself for their use.
        
        show_progress_bar (bool)
            Indicates whether or not to show progress bar. Defaults to False.
    
    Returns:
        sim_data (dict) 
            Simulated data; keys are [scan_data, platform_pos, range_bins].
    
    Raises:
        IndexError if shape of sim_params['scatter_pos'] does not match expectation.
    """
    # Initialization
    scatterer_pos = np.array(sim_params['scatterer_pos'])
    platform_init_pos = np.array(sim_params['platform_init_pos'])
    platform_vel = np.array(sim_params['platform_vel'])
    dt_slow = 1 / sim_params['scan_rate']
    num_scans = round(sim_params['duration'] / dt_slow)
    dt_fast = 1 / (2 * sim_params['center_freq'])
    two_way_t_min = 2 * sim_params['range_min'] / SPEED_OF_LIGHT
    two_way_t_max = 2 * sim_params['range_max'] / SPEED_OF_LIGHT
    min_range_bin = floor(two_way_t_min / dt_fast)
    max_range_bin = ceil(two_way_t_max / dt_fast)
    num_range_bins = max_range_bin - min_range_bin + 1
    if not num_range_bins % 2:
        max_range_bin += 1
        num_range_bins += 1

    # Check that scatterer positions matrix are of compatible shape
    if scatterer_pos.shape[1] != 3:
        raise IndexError(("Specified 'scattererPos' does not appear to be collection of 3-D " 
                          "[X, Y, Z] points"))

    # In order, fast time associated with range window, one-way range bins, scan/pulse indices,
    # associated per-scan/pulse platform positions, and two-way time delays to each scatterer for
    # each scan/pulse
    t = np.arange(min_range_bin, max_range_bin + 1, 1) * dt_fast
    range_bins = t * SPEED_OF_LIGHT / 2
    scan_idx = np.arange(0, num_scans)[:, np.newaxis]
    platform_pos = platform_init_pos + platform_vel * dt_slow * scan_idx
    one_way_range = cdist(scatterer_pos, platform_pos)
    time_delay = 2 * one_way_range / SPEED_OF_LIGHT

    # Include propagation loss if requested
    if sim_params['prop_loss']:
        prop_loss = 1 / one_way_range ** 4
    else:
        prop_loss = np.ones_like(one_way_range)

    # More initialization
    scan_data = np.zeros((num_scans, num_range_bins), dtype=np.complex128)
    total_steps = num_scans * scatterer_pos.shape[0]
    step = 0

    if show_progress_bar:
        progress_bar(step, total_steps, increment_name="Step", msg="Simulating scans/pulses", 
                     done=False, elapsed_time=0)

    # Iterate over each scan/pulse
    start_time = time.time()
    for ii in scan_idx:

        # Iterate over each scatterer and add its return signal to the current scan/pulse's total
        # return
        for jj in np.arange(0, scatterer_pos.shape[0]):
            scan_data[ii, :] += (sim_params['scatterer_RCS'][jj] * prop_loss[jj, ii] * 
                                 np.sinc(sim_params['bandwidth'] * (t - time_delay[jj, ii])) * 
                                 np.exp(1j * 2 * np.pi * sim_params["center_freq"] * 
                                 (t - time_delay[jj, ii])))
            step += 1
            if show_progress_bar:
                progress_bar(step, total_steps, increment_name="Step", 
                             msg="Simulating scans/pulses", done=False, 
                             elapsed_time=(time.time() - start_time))
                
    # Add noise if requested
    if sim_params['add_noise']:
        noise_var = sim_params['noise_magnitude'] / sqrt(2)
        scan_data += np.random.normal(
            loc=0, scale=noise_var, size=(scan_data.shape[0], 2 * scan_data.shape[1]),).view(np.complex128)
        
    if show_progress_bar:
        progress_bar(step, total_steps, increment_name="Step", msg="Simulating scans/pulses", 
                     done=True, elapsed_time=(time.time() - start_time))

    return {'scan_data': scan_data, 'platform_pos': platform_pos, 'range_bins': range_bins}


def simulate_image(sim_params, show_progress_bar=False, num_threads=1):
    """Simulate SAR data of a grayscale image as if each pixel is a point scatterer with an 
    amplitude equal to the pixel intensity.
    
    Args:
        sim_params (dict)
            Simulation parameters. Refer to top-of-file comments for description of these 
            parameters and to method itself for their use.
        
        show_progress_bar (bool)
            Indicates whether or not to show progress bar. Defaults to False.

        num_threads (int)
            Number of threads to use when simulating scans. Defaults to 1.
            
    Returns:
        sim_data (dict)
            Simulated data; keys are [scan_data, platform_pos, range_bins].
    """
    # Initialization
    platform_init_pos = np.array(sim_params['platform_init_pos'])
    platform_vel = np.array(sim_params['platform_vel'])
    dt_slow = 1 / sim_params['scan_rate']
    num_scans = round(sim_params['duration'] / dt_slow)
    dt_fast = 1 / (2 * sim_params['center_freq'])
    two_way_t_min = 2 * sim_params['range_min'] / SPEED_OF_LIGHT
    two_way_t_max = 2 * sim_params['range_max'] / SPEED_OF_LIGHT
    min_range_bin = floor(two_way_t_min / dt_fast)
    max_range_bin = ceil(two_way_t_max / dt_fast)
    num_range_bins = max_range_bin - min_range_bin + 1
    if not num_range_bins % 2:
        max_range_bin += 1
        num_range_bins += 1

    # Load image as grayscale image, spatially downsample it, rescale to [0, 255] intensities, and
    # threshold them
    img = imageio.imread(sim_params['source_image'])
    img = img[:, :, :3]
    img = np.sum(img / 3, 2)
    img -= np.min(img[:])
    img *= 255 / np.max(img[:])
    img = transform.rescale(img, 1 / sim_params['downsampling_factor'])
    img = np.floor(img)
    img[img < sim_params['pixel_thresholds'][0]] = 0
    img[img > sim_params['pixel_thresholds'][1]] = 0

    # Specify the scatterers as each non-zero pixel in the image
    scatterer_rcs = img.reshape(img.size)
    non_zero_scatterers = scatterer_rcs > 0
    scatterer_rcs = scatterer_rcs[non_zero_scatterers]
    scatterer_rcs = scatterer_rcs[np.newaxis, :]
    x_pos = (np.arange((1 - img.shape[1]) / 2, (img.shape[1] + 1) / 2, 1) * 
             sim_params['pixel_res'][0] + sim_params['image_center'][0])
    y_pos = (np.arange((img.shape[0] + 1) / 2, (1 - img.shape[0]) / 2, -1) * 
             sim_params['pixel_res'][1] + sim_params['image_center'][1])
    x_grid, y_grid = np.meshgrid(x_pos, y_pos)
    scatterer_pos = np.stack((x_grid.reshape(img.size), y_grid.reshape(img.size), 
                             np.zeros(img.size),), axis=-1)
    scatterer_pos = scatterer_pos[non_zero_scatterers, :]

    # Display transformed image for confirmation
    plt.figure()
    plt.subplot(111)
    plt.imshow(img, cmap="gray", extent=(x_pos[0], x_pos[-1], y_pos[-1], y_pos[0]))
    plt.title("Confirm Image")
    plt.xlabel("X (m)")
    plt.ylabel("Y (m)")
    plt.colorbar()
    plt.show()
    yes = yes_or_no("Proceed with SAR simulation of image?")
    if not yes:
        print("Halting simulation!")
        exit()

    # In order, fast time associated with range window, one-way range bins, scan/pulse indices,
    # associated per-scan platform positions, and two-way time delays to each scatterer for each
    # scan/pulse
    t = np.arange(min_range_bin, max_range_bin + 1, 1)[:, np.newaxis] * dt_fast
    range_bins = np.transpose(t * SPEED_OF_LIGHT / 2)
    scan_idx = np.arange(0, num_scans)
    platform_pos = platform_init_pos + platform_vel * dt_slow * scan_idx[:, np.newaxis]
    time_delay = 2 * cdist(platform_pos, scatterer_pos) / SPEED_OF_LIGHT

    # Intermediate calculations
    scan_data = np.zeros((num_scans, num_range_bins), dtype=np.complex128)
    exp_arg_t = np.exp(1j * 2 * np.pi * sim_params['center_freq'] * t)
    exp_arg_time_delay = np.exp(1j * 2 * np.pi * sim_params['center_freq'] * time_delay)

    # Multiprocessing setup
    manager = multiprocessing.Manager()
    all_process_results = manager.list([None] * num_scans)
    jobs = []
    pool = multiprocessing.Pool(num_threads)

    if show_progress_bar:
        progress_bar(0, num_scans, increment_name="Step", msg="Simulating scans/pulses", done=False,
                     elapsed_time=0)

    # For each scan/pulse, spawn an asynchronous process
    start_time = time.time()
    for ii in scan_idx:
        p = pool.apply_async(single_scan, 
                             (ii, scatterer_rcs, sim_params['bandwidth'], t, time_delay[ii], 
                              exp_arg_t, exp_arg_time_delay[ii], show_progress_bar, num_scans, 
                              start_time, all_process_results))
        jobs.append(p)

    # Wait for all jobs to finish
    [p.wait() for p in jobs]
    pool.close()
    pool.join()

    # Assemble individual process results into overall data
    scan_data = np.stack(all_process_results, axis=0)
    
    # Add noise if requested
    if sim_params['add_noise']:
        noise_var = sim_params['noise_magnitude'] / sqrt(2)
        scan_data += np.random.normal(
            loc=0, scale=noise_var, size=(scan_data.shape[0], 2 * scan_data.shape[1]),).view(np.complex128)
    
    if show_progress_bar:
        progress_bar(ii + 1, num_scans, increment_name="Step", msg="Simulating scans/pulses", 
                     done=True, elapsed_time=(time.time() - start_time))

    return {'scan_data': np.real(scan_data), 'platform_pos': platform_pos, 
            'range_bins': np.squeeze(range_bins)}


def single_scan(scan_idx, scatterer_rcs, bandwidth, t, time_delay, exp_arg_t, exp_arg_time_delay, 
                show_progress_bar, num_scans, start_time, return_list):
    """Simulate a single radar scan of a grayscale image as if each pixel is a point scatterer with 
    an amplitude equal to the pixel intensity.
    
    Args:
        scan_idx (int)
            The index of the scan being simulated.
        
        scatterer_rcs (2-D array with shape [1, M])
            The intensity of each pixel in the image, flattened into a 1xM array where M is the 
            number of downscaled pixels in the image.
        
        bandwidth (int)
            The bandwidth of the radar.
        
        t (1-D array with shape [N])
            The fast time associated with each range window.
        
        time_delay (2-D array with shape [NxM])
            An array containing all two-way time delays to each pixel for each scan.

        exp_arg_t (2-D array with shape [Nx1])
            Magic intermediary calculations.

        exp_arg_time_delay (2-D array with dimensions [NxM])
            Magic intermediary calculations.
        
        show_progress_bar (bool) 
            Indicates whether or not to show progress bar.
        
        num_scans (int)
            Total number of scans to be simulated.

        start_time (float)
            Time at which scan simulation began.

        return_list (multiprocessing.Manager().list)
            List where completed scans are stored.
    """
    return_list[scan_idx] = np.sum(np.sinc(bandwidth * (t - time_delay)) * scatterer_rcs * 
                                     exp_arg_t * exp_arg_time_delay, axis=1)
    if show_progress_bar:
        progress_bar(scan_idx + 1, num_scans, increment_name="Step", 
                     msg="Simulating scans/pulses", done=False, 
                     elapsed_time=(time.time() - start_time))


def simulate_image_misaligned(sim_params, show_progress_bar=False):
    """Simulate SAR data of a grayscale image as if each pixel is a point scatterer with an 
    amplitude equal to the pixel intensity and with the timestamps of the scans and the platform 
    positions are unaligned.
    
    Args:
        sim_params (dict)
            Simulation parameters. Refer to top-of-file comments for description of these 
            parameters and to method itself for their use.
        
        show_progress_bar (bool)
            Indicates whether or not to show progress bar. Defaults to False.  

    Returns:
        sim_data (dict)
            Simulated data; keys are [scan_data, platform_pos, range_bins].
    """
    # Initialization
    corner_reflector_pos = np.array(sim_params['scatterer_pos'])
    num_corner_reflectors = corner_reflector_pos.shape[0]
    dt_slow = 1 / sim_params['scan_rate']
    motion_step = 1 / sim_params['motion_rate']
    dt_fast = 1 / (2 * sim_params['center_freq'])
    two_way_t_min = 2 * sim_params['range_min'] / SPEED_OF_LIGHT
    two_way_t_max = 2 * sim_params['range_max'] / SPEED_OF_LIGHT
    min_range_bin = floor(two_way_t_min / dt_fast)
    max_range_bin = ceil(two_way_t_max / dt_fast)
    num_range_bins = max_range_bin - min_range_bin + 1
    if not num_range_bins % 2:
        max_range_bin += 1
        num_range_bins += 1
    fast_time = np.arange(min_range_bin, max_range_bin + 1, 1)[:, np.newaxis] * dt_fast
    range_bins = np.transpose(fast_time * SPEED_OF_LIGHT / 2)

    # Compute anchor points for platform motion
    platform_init_pos = np.array(sim_params['platform_init_pos'])
    platform_vel = np.array(sim_params['platform_vel'])
    platform_final_pos = platform_init_pos + platform_vel * sim_params['duration']

    # Compute timing
    takeoff_duration = platform_init_pos[2] / sim_params['takeoff_speed']
    landing_duration = platform_final_pos[2] / sim_params['landing_speed']
    takeoff_time = sim_params['motion_offset'][0] + sim_params['radar_offset'][0]
    aperture_start_time = takeoff_time + takeoff_duration
    aperture_end_time = aperture_start_time + sim_params['duration']
    landing_time = aperture_end_time + landing_duration
    total_flight_duration = landing_time - takeoff_time
    total_radar_duration = (total_flight_duration + sim_params['radar_offset'][0] + 
                            sim_params['radar_offset'][1])
    total_motion_duration = (total_radar_duration + sim_params['motion_offset'][0] + 
                             sim_params['motion_offset'][1])

    # Compute scan and motion capture counts and initialize outputs
    total_num_scans = ceil(total_radar_duration / dt_slow)
    total_num_motion = ceil(total_motion_duration / motion_step)
    scan_times = np.arange(0, total_num_scans, 1) * dt_slow + sim_params['motion_offset'][0]
    motion_times = np.arange(0, total_num_motion, 1) * motion_step
    platform_pos_scan = np.zeros((total_num_scans, 3))
    platform_pos_motion = np.zeros((total_num_motion, 3))

    # Compute per-scan platform positions
    # Pre-takeoff
    pre_takeoff_idx = np.where(np.logical_and(
        sim_params['motion_offset'][0] <= scan_times, scan_times < takeoff_time,))[0]
    platform_pos_scan[pre_takeoff_idx, :2] = platform_init_pos[:2]
    # Takeoff
    takeoff_idx = np.logical_and(takeoff_time <= scan_times, scan_times < aperture_start_time)
    platform_pos_scan[takeoff_idx, :2] = platform_init_pos[:2]
    platform_pos_scan[takeoff_idx, 2] = (sim_params['takeoff_speed'] * 
                                         (scan_times[takeoff_idx] - takeoff_time))
    # Synthetic aperture
    aperture_idx = np.logical_and(aperture_start_time <= scan_times, scan_times < aperture_end_time)
    platform_pos_scan[aperture_idx, :] = (platform_init_pos + platform_vel[np.newaxis, :] * 
                                          (scan_times[aperture_idx] - aperture_start_time)[:, np.newaxis])
    # Landing
    landing_idx = np.logical_and(aperture_end_time <= scan_times, scan_times < landing_time)
    platform_pos_scan[landing_idx, :2] = platform_final_pos[:2]
    platform_pos_scan[landing_idx, 2] = (platform_final_pos[2] - sim_params['landing_speed'] * 
                                         (scan_times[landing_idx] - aperture_end_time))
    # Post-landing
    post_landing_idx = np.where(scan_times >= landing_time)[0]
    platform_pos_scan[post_landing_idx, :2] = platform_final_pos[:2]
    # Add noise to platform motion if requested
    if sim_params['random_motion']:
        random_motion = (2 * sim_params['random_motion_magnitude'] * 
                         np.random.rand(post_landing_idx[0] - pre_takeoff_idx[-1], 3) - 0.5)
        platform_pos_scan[pre_takeoff_idx[-1]:post_landing_idx[0], :] = (
            platform_pos_scan[pre_takeoff_idx[-1] : post_landing_idx[0], :] + random_motion)

    # Compute motion captured platform positions by interpolating the per-scan platform positions
    platform_pos_motion_fun = interp1d(scan_times, platform_pos_scan, axis=0)
    within_scan_motion_times = np.where(np.logical_and(motion_times >= scan_times[0], 
                                                       motion_times <= scan_times[-1]))[0]
    platform_pos_motion[: within_scan_motion_times[0], :2] = platform_init_pos[:2]
    platform_pos_motion[within_scan_motion_times[-1] :, :2] = platform_final_pos[:2]
    platform_pos_motion[within_scan_motion_times, :] = \
        platform_pos_motion_fun(motion_times[within_scan_motion_times])

    #    # Pre-takeoff
    #    pre_takeoff_idx = motion_times < takeoff_time
    #    platform_pos_motion[pre_takeoff_idx, :2] = platform_init_pos[:2]
    #    # Takeoff
    #    takeoff_idx = np.logical_and(takeoff_time <= motion_times, motion_times < aperture_start_time)
    #    platform_pos_motion[takeoff_idx, :2] = platform_init_pos[:2]
    #    platform_pos_motion[takeoff_idx, 2] = (sim_params['takeoff_speed'] *
    #                       (motion_times[takeoff_idx] - takeoff_time))
    #    # Synthetic aperture
    #    aperture_idx = np.logical_and(aperture_start_time <= motion_times,
    #                                  motion_times < aperture_end_time)
    #    platform_pos_motion[aperture_idx, :] = (platform_init_pos + platform_vel[np.newaxis, :] *
    #                       (motion_times[aperture_idx] - aperture_start_time)[:, np.newaxis])
    #    # Landing
    #    landing_idx = np.logical_and(aperture_end_time <= motion_times, motion_times < landing_time)
    #    platform_pos_motion[landing_idx, :2] = platform_final_pos[:2]
    #    platform_pos_motion[landing_idx, 2] = (platform_final_pos[2] - sim_params['landing_speed'] *
    #                       (motion_times[landing_idx] - aperture_end_time))
    #    # Post-landing
    #    post_landing_idx = motion_times >= landing_time
    #    platform_pos_motion[post_landing_idx, :2] = platform_final_pos[:2]

    # Load image as grayscale image, spatially downsample it, rescale to [0, 255] intensities, and
    # threshold them
    img = imageio.imread(sim_params['source_image'])
    img = img[:, :, :3]
    img = np.sum(img / 3, 2)
    img -= np.min(img[:])
    img *= 255 / np.max(img[:])
    img = transform.rescale(img, 1 / sim_params['downsampling_factor'], multichannel=False)
    img[img < sim_params['pixel_thresholds'][0]] = 0
    img[img > sim_params['pixel_thresholds'][1]] = 0

    # Initialize scatterer RCS
    scatterer_rcs = img.reshape(img.size)
    non_zero_scatterers = scatterer_rcs > 0
    scatterer_rcs = scatterer_rcs[non_zero_scatterers]
    scatterer_rcs = scatterer_rcs[np.newaxis, :]
    max_scatterer_idx = np.argmax(scatterer_rcs)

    # Specify the scatterers as each non-zero pixel in the image
    x_pos = (np.arange((1 - img.shape[1]) / 2, (img.shape[1] + 1) / 2, 1) * 
             sim_params['pixel_res'][0] + sim_params['image_center'][0])
    y_pos = (np.arange((img.shape[0] + 1) / 2, (1 - img.shape[0]) / 2, -1) * 
             sim_params['pixel_res'][1] + sim_params['image_center'][1])
    x_grid, y_grid = np.meshgrid(x_pos, y_pos)
    scatterer_pos = np.stack(
        (x_grid.reshape(img.size), y_grid.reshape(img.size), np.zeros(img.size)), axis=-1)
    scatterer_pos = scatterer_pos[non_zero_scatterers, :]

    # Display transformed image for confirmation
    plt.figure()
    plt.subplot(111)
    plt.imshow(img, cmap="gray", extent=(x_pos[0], x_pos[-1], y_pos[-1], y_pos[0]))
    plt.title("Confirm Image")
    plt.xlabel("X (m)")
    plt.ylabel("Y (m)")
    plt.colorbar()
    plt.show()
    yes = yes_or_no("Proceed with SAR simulation of image?")
    if not yes:
        print("Halting simulation!")
        exit()

    # Add the discrete scatterers
    scatterer_rcs = np.concatenate(
        (scatterer_rcs, np.array(sim_params['scatterer_RCS'])[np.newaxis, :]), axis=1,)
    scatterer_pos = np.concatenate((scatterer_pos, corner_reflector_pos), axis=0)

    # Initialize scan data and some intermediates
    scan_data = np.zeros((total_num_scans, num_range_bins), dtype=np.complex128)
    one_way_range = cdist(platform_pos_scan, scatterer_pos)
    time_delay = 2 * one_way_range / SPEED_OF_LIGHT
    exp_arg_fast_time = np.exp(1j * 2 * np.pi * sim_params['center_freq'] * fast_time)
    exp_arg_time_delay = np.exp(1j * 2 * np.pi * sim_params['center_freq'] * time_delay)

    # Include propagation loss if requested
    img_scatterer_factor = sim_params['max_signal_val'] / scatterer_rcs[0, max_scatterer_idx]
    if sim_params['prop_loss']:
        prop_loss = 1 / one_way_range ** 4
        img_scatterer_factor *= np.min(one_way_range[:, max_scatterer_idx]) ** 4
    else:
        prop_loss = np.ones_like(one_way_range)
    scatterer_rcs[0, :-num_corner_reflectors] = (scatterer_rcs[0, :-num_corner_reflectors] * 
                                                 img_scatterer_factor)

    if show_progress_bar:
        progress_bar(0, total_num_scans, increment_name="Step", msg="Simulating scans/pulses", 
                     done=False, elapsed_time=0)

    # Iterate over each scan/pulse
    start_time = time.time()
    for ii in range(total_num_scans):
        scan_data[ii, :] = np.sum(scatterer_rcs * prop_loss[ii, :] * 
                                  np.sinc(sim_params['bandwidth'] * (fast_time - time_delay[ii, :])) 
                                  * exp_arg_fast_time * exp_arg_time_delay[ii, :], axis=1,)
        if show_progress_bar:
            progress_bar(ii + 1, total_num_scans, increment_name="Step", 
                         msg="Simulating scans/pulses", done=False, 
                         elapsed_time=(time.time() - start_time))

    if show_progress_bar:
        progress_bar(ii + 1, total_num_scans, increment_name="Step", msg="Simulating scans/pulses", 
                     done=True, elapsed_time=(time.time() - start_time))

    # Apply time misalignment and radar displacement
    scan_times -= sim_params['time_misalignment']
    platform_pos_motion += np.asarray(sim_params['radar_displacement'])[np.newaxis, :]

    # Remove some fraction of platform data
    num_missing = floor(sim_params['missing_fraction'] * platform_pos_motion.shape[0])
    random_order = np.random.permutation(platform_pos_motion.shape[0])
    platform_pos_motion[random_order[:num_missing], :] = np.nan

    # Add noise if requested
    if sim_params['add_noise']:
        noise_var = sim_params['noise_magnitude'] / sqrt(2)
        scan_data += np.random.normal(
            loc=0, scale=noise_var, size=(scan_data.shape[0], 2 * scan_data.shape[1]),).view(np.complex128)

    return {'scan_data': scan_data, 'platform_pos': platform_pos_motion,
            'motion_timestamps': motion_times, 'scan_timestamps': scan_times,
            'range_bins': range_bins, 'corner_reflector_pos': corner_reflector_pos}


def parse_args(args, cmd_line):
    """Input argument parser.
    
    Args:
        args (list)
            Input arguments as taken from command line execution via sys.argv[1:].
            
        cmd_line (bool)
            Indicates whether or not method was called via command line.
    
    Returns:
        parsed_args (Namespace)
            Parsed arguments.
    """
    # Parse input arguments
    parser = argparse.ArgumentParser(
            description="SAR data simulation",
            epilog=("Simulates data needed to create a SAR image via backprojection. Intended to "
                    "be compatible with backprojection.py."))
    parser.add_argument('sim_params_file', nargs='?', type=str,
                        help=("YAML file containing parameters specifying how to simulate data. "
                              "Users should inspect this code to understand required parameters "
                              "as a function of the desired and allowed simulations."))
    parser.add_argument('sim_data_file', nargs='?', type=str, default=None,
                        help=("File to pickle simulated data to; content will be a dictionary with "
                              "keys [scan_data, platform_pos, range_bins, sim_params]."))
    parser.add_argument('-r', '--return_data', action='store_true',
                        help=("Return simulated data; only useful if calling main method in other "
                              "code."))
    parser.add_argument('-p', '--progress_bar', action='store_true', help="Show progress bar")
    parser.add_argument('-t', '--num_threads', type=int, default=1, 
                        help="Number of threads to use when simulating scans")
    parsed_args = parser.parse_args(args)
    
    # Do some additional checks to make sure simulated data is being saved
    if parsed_args.sim_data_file:
        if os.path.exists(parsed_args.sim_data_file):
            if cmd_line:
                yes = yes_or_no(("Specified simulated SAR data file already exists; do you want to " 
                                "overwrite it?"))
                if not yes:
                    parsed_args.sim_data_file = deconflict_file(parsed_args.sim_data_file)
                    print((f"Overwriting \'{parsed_args.sim_data_file}\' to save simulated SAR "
                           "data..."))
            else:
                parsed_args.sim_data_file = deconflict_file(parsed_args.sim_data_file)
                print(("Specified simulated SAR data file already exists; using "
                       f"\'{parsed_args.sim_data_file}\' as simulated SAR data save file..."))
    elif not parsed_args.return_data:
        parser.error("Simulated data is not being saved or returned!")
    is_valid_file(parser, parsed_args.sim_params_file, 'r')
    is_valid_file(parser, parsed_args.sim_data_file, 'w')
    
    return parsed_args


def main(args, cmd_line=False):
    """Main execution method to simulate SAR data.
    
    Args:
        args (list)
            Input arguments as taken from command line execution via sys.argv[1:].
            
        cmd_line (bool)
            Indicates whether or not method was called via command line.
    
    Returns:
        sim_data (dict) 
            Simulated data; keys are [scan_data, platform_pos, range_bins, sim_params].
    """
    # Parse input arguments
    parsed_args = parse_args(args, cmd_line)

    # Read the parameters file
    sim_params = read_sim_params(parsed_args.sim_params_file)

    # Simulate data
    sim_data = simulate_data(sim_params, parsed_args.progress_bar, parsed_args.num_threads)

    # Save simulated data to file if requested
    if parsed_args.sim_data_file:
        with open(parsed_args.sim_data_file, "wb") as f:
            pickle.dump(sim_data, f)

    # Return data if requested
    if parsed_args.return_data:
        return sim_data


if __name__ == "__main__":
    """Standard Python alias for command line execution."""
    main(sys.argv[1:], True)
