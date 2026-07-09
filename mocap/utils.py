#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Shared utilities for motion capture and radar data processing."""

import pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from pathlib import Path

def load_radar_data(filename):
    """
    Load radar data from pickle file.
    
    Args:
        filename (str): Path and name of pickle file containing radar data.

    Returns:
        data (dict): Radar data dictionary with keys:
            - 'timestamps': Array of timestamps for each scan
            - 'range_bins': Array of range bin values
            - 'scan_data': 2D array of radar scan data

    Raises:
        FileNotFoundError: If the specified file doesn't exist
        pickle.UnpicklingError: If the file is not a valid pickle file
        KeyError: If required data fields are missing
    """
    try:
        with open(filename, 'rb') as f:
            data = pickle.load(f)
            
        required_keys = ['timestamps', 'range_bins', 'scan_data']
        if not all(key in data for key in required_keys):
            raise KeyError(f"Radar data must contain keys: {required_keys}")
            
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"Radar data file not found: '{filename}'")
    except pickle.UnpicklingError:
        raise pickle.UnpicklingError(f"Invalid pickle file format: '{filename}'")

def load_mocap_data(filename):
    """Load motion capture data from pickle file.

    Args:
        filename (str): Path and name of pickle file containing motion capture data.

    Returns:
        data (dict): Motion capture data dictionary with keys:
            - 'timestamps': Array of timestamps for each sample
            - 'platform_pos': Array of platform positions
            - 'ref_obj1': Reference object 1 position
            - 'ref_obj2': Reference object 2 position

    Raises:
        FileNotFoundError: If the specified file doesn't exist
        pickle.UnpicklingError: If the file is not a valid pickle file
        KeyError: If required data fields are missing
    """
    try:
        with open(filename, 'rb') as f:
            data = pickle.load(f)
            
        required_keys = ['timestamps', 'platform_pos', 'ref_obj1', 'ref_obj2']
        if not all(key in data for key in required_keys):
            raise KeyError(f"Motion capture data must contain keys: {required_keys}")
            
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"Motion capture data file not found: '{filename}'")
    except pickle.UnpicklingError:
        raise pickle.UnpicklingError(f"Invalid pickle file format: '{filename}'")

def process_radar_data(data):
    """Process radar data and convert to dB.
    
    Args:
        data (dict): Dictionary containing radar data.

    Returns:
        dict: Dictionary containing processed radar data with timestamps starting at 0.
    """
    timestamps = np.array(data['timestamps'] - data['timestamps'][0])  # start at 0
    range_bins = np.array(data['range_bins'])
    scan_data = np.array(data['scan_data'])
    scan_data_db = np.log10(np.abs(scan_data)) * 20

    return {
        'timestamps': timestamps,
        'range_bins': range_bins,
        'scan_data': scan_data,
        'scan_data_db': scan_data_db
    }

def distance_to_object(platform_pos, ref_obj):
    """
    Calculate Euclidean distance between platform positions and reference object.

    Args:
        platform_pos (ndarray): Array of platform positions with shape (n, 3).
        ref_obj (ndarray): Reference object position with shape (3,).

    Returns:
        ndarray: Array of distances with shape (n,).
    """
    # ============================== STUDENT TODO (PIPELINE) ==============================
    # Compute the straight-line (Euclidean) distance from EVERY platform position to the
    # reference object -- the same distance formula as backprojection Part 1, but for all
    # positions at once.
    #   HINT: subtract ref_obj from platform_pos (broadcasting handles the shapes), then
    #         np.linalg.norm(..., axis=1) gives the length of each row's difference vector.
    #   QUICK TEST in a Python shell:
    #         distance_to_object(np.array([[0, 0, 0]]), np.array([3, 4, 0]))  ->  [5.0]
    # ======================================================================================
    raise NotImplementedError("distance_to_object: delete this line once implemented!")

def distances_to_bin_indices(range_bins, distances):
    """
    For each distance, find the index of the closest range bin.

    Args:
        range_bins (ndarray): Array of range bin distances
        distances (ndarray): Array of distances to convert

    Returns:
        ndarray: Array of bin indices
    """
    # ============================== STUDENT TODO (PIPELINE) ==============================
    # For each distance, find the INDEX of the closest range bin -- exactly the same
    # "nearest range bin" idea as backprojection Part 1, Step 5, but for a whole vector of
    # distances at once.
    #   HINT: np.abs(range_bins[:, np.newaxis] - distances) is a (num_bins x num_distances)
    #         table of how far each bin is from each distance; np.argmin(..., axis=0) picks
    #         the closest bin index for each distance.
    #   QUICK TEST: distances_to_bin_indices(np.array([0.0, 1.0, 2.0]), np.array([1.1]))
    #               ->  [1]
    # ======================================================================================
    raise NotImplementedError("distances_to_bin_indices: delete this line once implemented!")


def select_closest_mocap_to_radar(radar_timestamps, mocap_timestamps, platform_pos):
    """
    For each radar timestamp, find the closest mocap timestamp and return corresponding mocap positions.

    Args:
        radar_timestamps (ndarray): (N,) array of radar scan times
        mocap_timestamps (ndarray): (M,) array of mocap sample times
        platform_pos (ndarray): (M, 3) mocap platform position array

    Returns:
        matched_positions (ndarray): (N, 3) array of mocap positions closest to each radar timestamp
    """    
    radar_timestamps = np.asarray(radar_timestamps)
    mocap_timestamps = np.asarray(mocap_timestamps)
    platform_pos = np.asarray(platform_pos)

    # Ensure all arrays are the same length
    min_length = min(len(mocap_timestamps), len(platform_pos))
    mocap_timestamps = mocap_timestamps[:min_length]
    platform_pos = platform_pos[:min_length]

    # Find closest indices
    idx_closest = np.abs(mocap_timestamps[:, None] - radar_timestamps).argmin(axis=0)
    
    # Clip indices to valid range
    idx_closest = np.clip(idx_closest, 0, len(platform_pos) - 1)
    
    matched_positions = platform_pos[idx_closest]
    
    return matched_positions

def plot_calibration_verification(scan_data_aligned, platform_pos_aligned, radar_times_aligned, 
                                range_bins, ref_obj1, ref_obj2, figsize=(12, 10), cmap='viridis', num_ticks=10):
    """
    Plot RTI with reference object trajectories for calibration verification.

    Args:
        scan_data_aligned (ndarray): 2D array (aligned radar scans in dB)
        platform_pos_aligned (ndarray): Nx3 array of aligned platform positions 
        radar_times_aligned (ndarray): 1D array aligned radar timestamps
        range_bins (ndarray): 1D array of range bin distances
        ref_obj1, ref_obj2 (ndarray): 3D coordinates of reference objects
        figsize, cmap, num_ticks: plot styling options

    Returns:
        fig (matplotlib.figure.Figure): The created figure object.
        ax (matplotlib.axes.Axes): The axes object containing the plot.
    """    
    # Compute distances from platform positions to reference objects
    dist_obj1 = distance_to_object(platform_pos_aligned, ref_obj1)
    dist_obj2 = distance_to_object(platform_pos_aligned, ref_obj2)

    # Convert distances to bin indices
    bins_obj1 = distances_to_bin_indices(range_bins, dist_obj1)
    bins_obj2 = distances_to_bin_indices(range_bins, dist_obj2)

    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(scan_data_aligned, aspect='auto', cmap=cmap, interpolation='nearest')
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('dB')

    # Plot reference object trajectories
    ax.plot(bins_obj1, np.arange(len(bins_obj1)), 'r-', linewidth=2,
            label=f'Ref Obj 1 ({ref_obj1[0]:.2f}, {ref_obj1[1]:.2f}, {ref_obj1[2]:.2f})')
    ax.plot(bins_obj2, np.arange(len(bins_obj2)), 'b-', linewidth=2,
            label=f'Ref Obj 2 ({ref_obj2[0]:.2f}, {ref_obj2[1]:.2f}, {ref_obj2[2]:.2f})')

    ax.set_ylabel('Time Index')
    ax.set_xlabel('Range Bin Index')
    ax.set_title('Calibration Verification: RTI with Reference Object Trajectories')
    ax.legend()

    # Set x-axis ticks for range bins
    range_axis = np.linspace(0, range_bins[-1], len(range_bins))
    tick_positions = np.linspace(0, len(range_bins) - 1, num_ticks).astype(int)
    tick_labels = range_axis[tick_positions]
    plt.xticks(tick_positions, np.round(tick_labels, 2), rotation=45)

    # Set y-axis ticks for time
    y_tick_positions = np.linspace(0, len(radar_times_aligned) - 1, num_ticks).astype(int)
    y_tick_labels = np.linspace(radar_times_aligned[0] / 1000, radar_times_aligned[-1] / 1000, num_ticks)
    plt.yticks(y_tick_positions, np.round(y_tick_labels, 2))

    plt.tight_layout()

    print("\n=== Calibration Verification ===")
    print(f"Reference Object 1: {ref_obj1}")
    print(f"Reference Object 2: {ref_obj2}")
    print(f"Bin range for Obj1: {bins_obj1.min()} to {bins_obj1.max()}")
    print(f"Bin range for Obj2: {bins_obj2.min()} to {bins_obj2.max()}")

    return fig, ax

def save_processed_data(radar_data, mocap_data, output_name):
    """
    Save processed data to files. The exported radar scan_data should be the original (non-dB) data. Use dB-transformed data only for visualization.

    Args:
        radar_data (dict): Dictionary containing processed radar data.
        mocap_data (dict): Dictionary containing motion capture data.
        output_name (str): Output filename base name.
    """    
    data_dict = {
        'scan_data': radar_data['scan_data_trimmed'],
        'platform_pos': mocap_data['platform_pos_aligned'], 
        'range_bins': radar_data['range_bins']
    }

    file_path = Path('../backprojection/')
    file_path.mkdir(exist_ok=True)
    
    output_file = file_path / f"{output_name}.pkl"
    with open(output_file, 'wb') as file:
        pickle.dump(data_dict, file, protocol=pickle.HIGHEST_PROTOCOL)
    
    print(f"Processed data saved to '{output_file}'") 

def find_movement_start_end(platform_pos, velocity_threshold=0.0005, window=14):
    """
    Detects the start and end indices of sustained movement along the X-axis.

    Args:
        platform_pos (ndarray): Array of platform positions
        velocity_threshold (float): Velocity threshold for movement detection
        window (int): Window size for sustained movement detection

    Returns:
        tuple: (start_index, end_index) - If not found, returns (-1, -1)
    """
    x_positions = np.array([p[0] for p in platform_pos])
    dx = np.diff(x_positions)

    start_index = -1
    end_index = -1

    # Find movement start
    for i in range(len(dx) - window + 1):
        window_slice = dx[i:i+window]
        if np.all(np.abs(window_slice) >= velocity_threshold):
            start_index = i + 1  # Offset due to np.diff
            break

    # Find movement end, after start
    if start_index != -1:
        for j in range(start_index + window, len(dx) - window + 1):
            window_slice = dx[j:j+window]
            if np.all(np.abs(window_slice) < velocity_threshold):
                end_index = j + 1
                break

    return start_index, end_index

def interactive_mocap_movement_detection(platform_pos, mocap_timestamps, initial_velocity_threshold=0.0005, initial_window=14):
    """
    Interactive adjustment of motion capture movement detection parameters.

    Args:
        platform_pos (ndarray): Array of platform positions
        mocap_timestamps (ndarray): Array of mocap timestamps
        initial_velocity_threshold (float): Initial velocity threshold
        initial_window (int): Initial window size

    Returns:
        tuple: (final_velocity_threshold, final_window, start_index, end_index, confirmed)
    """
    current_velocity_threshold = initial_velocity_threshold
    current_window = initial_window
    
    print(f"\nAdjusting motion capture movement detection parameters")
    print(f"Available range: velocity_threshold 0.0001 to 0.01, window 5 to 50")
    print(f"Use the sliders to adjust parameters, then click 'Confirm' or 'Quit'")
    
    # Create the main figure with subplots
    fig = plt.figure(figsize=(15, 10))
    ax_main = plt.subplot2grid((5, 4), (0, 0), colspan=4, rowspan=4)
    
    # Create slider and button areas
    ax_velocity_slider = plt.subplot2grid((5, 4), (4, 1), colspan=1)
    ax_window_slider = plt.subplot2grid((5, 4), (4, 2), colspan=1)
    ax_confirm = plt.subplot2grid((5, 4), (4, 0))
    ax_quit = plt.subplot2grid((5, 4), (4, 3))
    
    # Initial detection
    start_index, end_index = find_movement_start_end(platform_pos, current_velocity_threshold, current_window)
    
    # Create initial plot
    x_positions = [p[0] for p in platform_pos]
    dx = np.diff(x_positions)
    
    line_dx, = ax_main.plot(dx, label='dx')
    line_threshold_pos = ax_main.axhline(y=current_velocity_threshold, color='r', linestyle='--', label='Threshold')
    line_threshold_neg = ax_main.axhline(y=-current_velocity_threshold, color='r', linestyle='--')
    
    # Initial vertical lines for start and end indices
    line_start = ax_main.axvline(x=start_index, color='orange', linestyle='--', label='Start')
    line_end = ax_main.axvline(x=end_index, color='orange', linestyle='--', label='End')

    ax_main.set_xlabel("Frame")
    ax_main.set_ylabel("ΔX (velocity)")
    ax_main.set_title(f"X-axis movement over time (Start: {start_index} / {mocap_timestamps[start_index] / 1e3:.2f} s, End: {end_index} / {mocap_timestamps[end_index] / 1e3:.2f} s)")
    ax_main.legend()
    ax_main.grid(True)
    
    # Create sliders
    velocity_slider = Slider(
        ax_velocity_slider, 'Velocity Threshold', -0.02, 0.02,
        valinit=current_velocity_threshold, valstep=0.00001
    )
    
    window_slider = Slider(
        ax_window_slider, 'Window Size', 5, 50,
        valinit=current_window, valstep=1
    )
    
    # Create buttons
    confirm_button = Button(ax_confirm, 'Confirm', color='lightgreen', hovercolor='green')
    quit_button = Button(ax_quit, 'Quit', color='lightcoral', hovercolor='red')
    
    # Variables to store the result
    result = {'velocity_threshold': None, 'window': None, 'start_index': None, 'end_index': None, 'confirmed': False}
    
    def update(val):
        """Update the plot when sliders change."""
        nonlocal current_velocity_threshold, current_window, start_index, end_index, line_start, line_end
        
        current_velocity_threshold = velocity_slider.val
        current_window = int(window_slider.val)
        
        # Update detection
        start_index, end_index = find_movement_start_end(platform_pos, current_velocity_threshold, current_window)

        # Update plot data
        line_threshold_pos.set_ydata([current_velocity_threshold, current_velocity_threshold])
        line_threshold_neg.set_ydata([-current_velocity_threshold, -current_velocity_threshold])
        
        # Calculate times in seconds
        start_time = mocap_timestamps[start_index] / 1e3 if start_index >= 0 else 0
        end_time = mocap_timestamps[end_index] / 1e3 if end_index >= 0 else 0

        # Update vertical lines
        line_start.set_xdata([start_index, start_index])
        line_end.set_xdata([end_index, end_index])

        # Update title
        ax_main.set_title(f"X-axis movement over time (Start: {start_index} / {start_time:.2f} s, End: {end_index} / {end_time:.2f} s)")
        
        fig.canvas.draw_idle()
    
    def confirm(event):
        """Handle confirm button click."""
        result['velocity_threshold'] = current_velocity_threshold
        result['window'] = current_window
        result['start_index'] = start_index
        result['end_index'] = end_index
        result['confirmed'] = True
        plt.close(fig)
    
    def quit_app(event):
        """Handle quit button click."""
        result['confirmed'] = False
        plt.close(fig)
    
    # Connect the sliders and buttons
    velocity_slider.on_changed(update)
    window_slider.on_changed(update)
    confirm_button.on_clicked(confirm)
    quit_button.on_clicked(quit_app)
    
    # Show the plot
    plt.tight_layout()
    plt.show()
    
    # Return the result
    if result['confirmed']:
        print(f"Confirmed parameters: velocity_threshold={result['velocity_threshold']:.4f}, window={result['window']}, start_index={result['start_index']}, end_index={result['end_index']}")
        return result['velocity_threshold'], result['window'], result['start_index'], result['end_index'], True
    else:
        print("Exiting without confirming motion capture movement detection parameters.")
        return None, None, None, None, False 