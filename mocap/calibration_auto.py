#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Auto-calibration of motion capture and radar data using matched filtering for non-stationary radar starts."""

__author__ = "Calvin Zhou"
__version__ = "1.0"
__maintainer__ = "Calvin Zhou"
__email__ = "calvinyaozhou@gmail.com"

# Update path
from pathlib import Path
import sys

if Path('..//').resolve().as_posix() not in sys.path:
    sys.path.insert(0, Path('..//').resolve().as_posix())

# Import required modules and methods
import argparse
import pprint
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import correlate2d
from scipy.interpolate import interp1d
from scipy.stats import norm

from utils import (
    load_radar_data,
    load_mocap_data,
    process_radar_data,
    distance_to_object,
    plot_calibration_verification,
    save_processed_data,
    find_movement_start_end,
    interactive_mocap_movement_detection
)
from common.helper_functions import is_valid_file


def resample_to_same_rate(source_time, source_data, target_time):
    """
    Resample source data to match the sampling rate of target_time.
    Args:
        source_time: (N,) array of timestamps for the original data
        source_data: (N, ...) data to be interpolated
        target_time: (M,) array of timestamps defining desired sampling rate
    Returns:
        new_time: resampled time array with same rate as target_time
        new_data: data resampled at new_time
    """
    # Compute target sampling rate (assumes uniform spacing), by finding the median of the time differences
    dt = np.median(np.diff(target_time))

    # Resample source data to target time, by using interpolation
    interpolator = interp1d(source_time, source_data, axis=0, bounds_error=False, fill_value='extrapolate')
    new_time = target_time
    new_data = interpolator(new_time)

    return new_time, new_data




def build_mocap_template(mocap_time, dist_obj, range_bins, sigma):
    """
    Convert 1D distance trace to 2D template matching RTI shape.
    Args:
        mocap_time: (N,) timestamps
        dist_obj: (N,) object distances at each timestamp
        range_bins: (R,) array of range bin centers (e.g., 0 to 10 m)
        sigma: width of Gaussian to spread target across nearby bins
    Returns:
        template: (N, R) 2D array of same structure as RTI
    """
    num_time = len(mocap_time)
    num_range_bins = len(range_bins)
    template = np.zeros((num_time, num_range_bins))

    for i in range(num_time):
        # Compute Gaussian around this distance over the range bins
        distance = dist_obj[i]
        gaussian = norm.pdf(range_bins, loc=distance, scale=sigma)
        template[i, :] = gaussian

    return template




def sliding_matched_filter(radar_data, mocap_template, start_index):
    """
    Slide the MoCap template vertically (in time) against radar_data using 2D cross-correlation.
    Args:
        radar_data: (T_radar, R) RTI data, time x range
        mocap_template: (T_mocap, R) MoCap template, longer in time than radar
        start_index: negative index (e.g., -691), where to start sliding
    Returns:
        best: dict of best match info
        results: list of all match results
    """
    results = []

    # Normalize radar data
    radar_norm = (radar_data - np.mean(radar_data)) / np.std(radar_data)

    radar_T = radar_data.shape[0]
    template_T = mocap_template.shape[0]

    # Slide template across radar data
    for offset in range(start_index, 1):
        start = -offset
        end = start + radar_T
        if end > template_T:
            break # skip if mocap slice would exceed template bounds

        # Get slice of mocap template and normalize
        mocap_slice = mocap_template[start:end, :]
        mocap_norm = (mocap_slice - np.mean(mocap_slice)) / np.std(mocap_slice)

        # Compute cross-correlation between normalized radar and mocap slices
        response = correlate2d(radar_norm, mocap_norm, mode='valid')
        max_corr = np.max(response)

        results.append({
            'time_offset': offset,
            'max_correlation': max_corr,
            'response_map': response
        })
    
    # Find best match
    best = max(results, key=lambda x: x['max_correlation'])

    return best, results




def plot_mocap_template(mocap_template, range_bins, resampled_time):
    """
    Plot the 2D MoCap template for verification.
    Args:
        mocap_template: (N, R) 2D array of MoCap template
        range_bins: (R,) array of range bin centers
        resampled_time: (N,) array of resampled time stamps
        save_path: (str or Path, optional) If provided, save the plot to this path
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    plt.imshow(mocap_template, aspect='auto', extent=[range_bins[0], range_bins[-1], resampled_time[-1], resampled_time[0]])
    plt.colorbar(label='Normalized Intensity')
    plt.xlabel('Range (m)')
    plt.ylabel('MoCap Time (s)')
    plt.title('2D MoCap Template (Time vs Range)')
    plt.show()

    return fig, ax



def align_radar_mocap_data(radar_data, mocap_data, sigma=0.5, reflector_choice=1):
    """
    Align radar and mocap data using template matching.
    Returns:
        scan_data, scan_data_db, platform_pos_aligned, radar_times_aligned, offset, mocap_template, resampled_time, range_bins
    """
    # Extract and preprocess radar and mocap data
    scan_data = radar_data['scan_data']
    scan_data_db = radar_data['scan_data_db']
    radar_timestamps = np.array(radar_data['timestamps'])
    range_bins = np.array(radar_data['range_bins'])
    platform_pos = np.array(mocap_data['platform_pos'])
    mocap_timestamps = np.array(mocap_data['timestamps'])
    ref_obj1 = np.array(mocap_data['ref_obj1'])
    ref_obj2 = np.array(mocap_data['ref_obj2'])

    # Compute distances from platform to first reference object (stronger return) (Consider distance_to_object)
    dist_obj1 = distance_to_object(platform_pos, ref_obj1)
    dist_obj2 = distance_to_object(platform_pos, ref_obj2)

    # Select the correct reference object for alignment
    if reflector_choice == 2:
        dist_obj = dist_obj2
    else:
        dist_obj = dist_obj1

    # Resample mocap distances and positions to radar timestamps
    resampled_time, resampled_dist = resample_to_same_rate(mocap_timestamps, dist_obj, radar_timestamps)
    _, resampled_plat_pos = resample_to_same_rate(mocap_timestamps, platform_pos, radar_timestamps)

    # Build 2D MoCap template
    mocap_template = build_mocap_template(resampled_time, resampled_dist, range_bins, sigma)

    # Plot the 2D MoCap template for verification
    fig, ax = plot_mocap_template(mocap_template, range_bins, resampled_time)

    # Compute start index for sliding
    start_index = len(radar_timestamps) - len(resampled_time)

    # Run sliding matched filter to find best offset
    best, results = sliding_matched_filter(scan_data_db, mocap_template, start_index)
    offset = -best['time_offset'] # negative offset because we want to align radar to mocap

    # Align mocap data to radar using offset
    end_index = offset + len(radar_timestamps)
    platform_pos_aligned = resampled_plat_pos[offset:end_index]

    # Ensure all arrays have the same length
    min_length = min(len(scan_data_db), len(platform_pos_aligned), len(radar_timestamps))
    platform_pos_aligned = platform_pos_aligned[:min_length]

    return scan_data, scan_data_db, platform_pos_aligned, radar_timestamps, offset, fig, ax




def parse_args(args):
    """
    Input argument parser.

    Args:
        args (list): Input arguments as taken from command line execution via sys.argv[1:].

    Returns:
        parsed_args (namespace): Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description='Motion capture and radar data calibration processor for non-stationary radar scenarios'
    )
    parser.add_argument('radar_file', 
                        help='Path and name of pickle file containing radar data')
    parser.add_argument('mocap_file',
                        help='Path and name of pickle file containing motion capture data')
    parser.add_argument('--sigma', type=float, default=0.5,
                        help='Sigma for Gaussian smoothing of mocap template (default: 0.5)')
    parser.add_argument('--velocity-threshold', type=float, default=0.0005,
                        help='Velocity threshold for motion capture movement detection (default: 0.0005)')
    parser.add_argument('--window-size', type=int, default=14,
                        help='Window size for sustained movement detection (default: 14)')
    parser.add_argument('--save-plots', action='store_true',
                        help='Save all plots to PNG files')
    parser.add_argument('--save-data', action='store_true',
                        help='Save processed data to pickle file')
    parser.add_argument('--output-name', type=str, default='run_0',
                        help='Output filename name for saved files (default: run_0)')
    parser.add_argument('--skip-interactive', action='store_true',
                        help='Skip interactive parameter adjustment')
    
    parsed_args = parser.parse_args(args)

    # Check if files are accessible
    is_valid_file(parser, parsed_args.radar_file, 'r')
    is_valid_file(parser, parsed_args.mocap_file, 'r')

    return parsed_args

def main(args):
    """
    Main function to process motion capture and radar data using matched filtering.

    Args:
        args (list): Input arguments as taken from command line execution via sys.argv[1:].

    Returns:
        scan_data (ndarray): Processed radar data
        platform_pos (ndarray): Processed motion capture data
        radar_times (ndarray): Processed radar timestamps
        range_bins (ndarray): Processed range bins
    """
    # Parse input arguments
    parsed_args = parse_args(args)

    # Load and process radar data
    print(f"Loading radar data from '{parsed_args.radar_file}'...")
    radar_data_raw = load_radar_data(parsed_args.radar_file)
    radar_data = process_radar_data(radar_data_raw)

    # Load motion capture data
    print(f"Loading motion capture data from '{parsed_args.mocap_file}'...")
    mocap_data_raw = load_mocap_data(parsed_args.mocap_file)

    # Prompt for reflector selection
    reflector_choice = None
    while True:
        ref_input = input("Which reflector to use for alignment? (1 or 2): ").strip()
        if ref_input == '1':
            reflector_choice = 1
            break
        elif ref_input == '2':
            reflector_choice = 2
            break
        elif ref_input == '':
            reflector_choice = 1
            print("No input, defaulting to reflector 1.")
            break
        else:
            print("Please enter '1' or '2'.")

    # --- Logging setup ---
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = logs_dir / f"calibration_auto_{timestamp}.log"


    for key in radar_data.keys():
        radar_data[key] = np.array(radar_data[key])
    for key in mocap_data_raw.keys():
        mocap_data_raw[key] = np.array(mocap_data_raw[key])


    with open(log_file, "a") as logf:
        logf.write("[Parameters]\n")
        logf.write(pprint.pformat(vars(parsed_args)) + "\n")
        logf.write(f"\nReflector used for alignment: {reflector_choice}\n")
        logf.write(f"\n[Initial Radar Data]\n")
        logf.write(f"  scan_data shape: {radar_data['scan_data'].shape}\n")
        logf.write(f"  timestamps shape: {radar_data['timestamps'].shape}\n")
        logf.write(f"  range_bins shape: {radar_data['range_bins'].shape}\n")
        logf.write(f"\n[Initial Mocap Data]\n")
        logf.write(f"  platform_pos shape: {mocap_data_raw['platform_pos'].shape}\n")
        logf.write(f"  timestamps shape: {mocap_data_raw['timestamps'].shape}\n")
        logf.write(f"  ref_obj1: {mocap_data_raw['ref_obj1']}\n")
        logf.write(f"  ref_obj2: {mocap_data_raw['ref_obj2']}\n")
        logf.write("---\n")
    # --- End logging setup ---

    # Align radar and mocap data using template matching
    print("Aligning radar and motion capture data using matched filtering...")
    scan_data, scan_data_db, platform_pos_aligned, radar_timestamps, offset, template_fig, template_ax = align_radar_mocap_data(
        radar_data, mocap_data_raw, sigma=parsed_args.sigma, reflector_choice=reflector_choice)
    print('Finished')

    if parsed_args.save_plots:
        template_filename = f"{parsed_args.output_name}_filter_template.png"
        print(f"Saving matched filter template plot to '{template_filename}'...")
        template_fig.savefig(template_filename, dpi=300, bbox_inches='tight')

    # After alignment (offset)
    with open(log_file, "a") as logf:
        logf.write(f"\n[Alignment Parameters]\n")
        logf.write(f"  offset: {offset}\n")
        logf.write("---\n")

    # Interactive motion capture movement detection
    if not parsed_args.skip_interactive:
        print("Running interactive motion capture movement detection...")
        velocity_threshold, window_size, start_index, end_index, confirmed = interactive_mocap_movement_detection(
            platform_pos_aligned, radar_timestamps, initial_velocity_threshold=parsed_args.velocity_threshold, initial_window=parsed_args.window_size
        )
        if not confirmed:
            print("Motion capture movement detection cancelled. Exiting...")
            return None
    else:
        print("Using command line parameters for motion capture movement detection...")
        start_index, end_index = find_movement_start_end(
            platform_pos_aligned, parsed_args.velocity_threshold, parsed_args.window_size
        )
        velocity_threshold = parsed_args.velocity_threshold
        window_size = parsed_args.window_size

    # After interactive/cmdline movement detection and before trimming
    with open(log_file, "a") as logf:
        logf.write(f"\n[Cutting Indices/Parameters]\n")
        logf.write(f"  start_index: {start_index}\n")
        logf.write(f"  end_index: {end_index}\n")
        logf.write(f"  velocity_threshold: {velocity_threshold}\n")
        logf.write(f"  window_size: {window_size}\n")
        logf.write("---\n")

    # Trim aligned data based on movement detection
    platform_pos_trimmed = platform_pos_aligned[start_index:end_index]
    radar_times_trimmed = radar_timestamps[start_index:end_index]
    scan_data_trimmed = scan_data[start_index:end_index]
    scan_data_db_trimmed = scan_data_db[start_index:end_index]
    radar_times_trimmed -= radar_times_trimmed[0]

    # Show calibration verification plot
    print("Showing calibration verification plot...")
    calib_fig, calib_ax = plot_calibration_verification(
        scan_data_db_trimmed, platform_pos_trimmed, radar_times_trimmed, radar_data['range_bins'], mocap_data_raw['ref_obj1'], mocap_data_raw['ref_obj2'], figsize=(12, 10)
    )

    if parsed_args.save_plots:
        calib_filename = f"{parsed_args.output_name}_calibration.png"
        print(f"Saving calibration plot to '{calib_filename}'...")
        calib_fig.savefig(calib_filename, dpi=300, bbox_inches='tight')
    
    # Save processed data if requested
    if parsed_args.save_data:
        radar_data_processed = {
            'scan_data_trimmed': scan_data_trimmed,
            'radar_times_trimmed': radar_times_trimmed,
            'range_bins': radar_data['range_bins']
        }

        mocap_data_processed = {
            'platform_pos_aligned': platform_pos_trimmed,
            'ref_obj1': mocap_data_raw['ref_obj1'],
            'ref_obj2': mocap_data_raw['ref_obj2']
        }

        save_processed_data(radar_data_processed, mocap_data_processed, parsed_args.output_name)

    # Display plots
    print("\n" + "="*60)
    print("All processing completed!")
    print("="*60)
    plt.show()

    # After trimming
    with open(log_file, "a") as logf:
        logf.write(f"\n[Final Data Shapes After Trimming]\n")
        logf.write(f"  scan_data_trimmed shape: {scan_data_trimmed.shape}\n")
        logf.write(f"  platform_pos_trimmed shape: {platform_pos_trimmed.shape}\n")
        logf.write(f"  radar_times_trimmed shape: {radar_times_trimmed.shape}\n")
        logf.write("---\n")
    print(f"\n[LOG] Data log saved to {log_file}")
    # --- End logging ---

    return {
        'scan_data': scan_data_trimmed,
        'platform_pos': platform_pos_trimmed,
        'times': radar_times_trimmed,
        'range_bins': radar_data['range_bins']
    }


if __name__ == "__main__":
    """Standard Python alias for command line execution."""
    main(sys.argv[1:]) 