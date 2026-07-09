#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Motion capture and radar data processing module."""

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
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from scipy.interpolate import interp1d
from utils import (
    load_radar_data,
    distance_to_object
)
from common.helper_functions import is_valid_file


def load_mocap_csv(filename, platform_name, corner_right_name, corner_left_name, swap_coords):
    """
    Load and process motion capture data from CSV file.

    Handles OptiTrack CSV export format with:
    - 3 header rows (skipped)
    - Rigid body position data in X, Y, Z columns
    - Multiple rigid bodies identified by name prefixes

    Args:
        filename (str): Path to the CSV file
        platform_name (str): Column prefix for the radar platform/drone
        corner_right_name (str): Column prefix for right corner reflector
        corner_left_name (str): Column prefix for left corner reflector

    Returns:
        dict: Processed motion capture data containing:
            - timestamps (ndarray): Time points in milliseconds
            - platform_pos (ndarray): Platform positions [N, 3] in (z, x, y) order
            - ref_obj1 (ndarray): Left corner reflector position (z, x, y)
            - ref_obj2 (ndarray): Right corner reflector position (z, x, y)

    Notes:
        - Coordinate system is converted from OptiTrack (x,y,z) to radar (z,x,y)
        - Missing corner reflector data is replaced with [0,0,0]
        - All positions are in meters
    """
    try:
        # Read CSV file, skipping system header rows
        csv = pd.read_csv(filename, skiprows=3)
        
        # Process column headers to include all metadata
        df = csv.iloc[1:]  # Remove second row, keep headers
        df.columns = [f"{df.columns[i]}_{df.iloc[0, i]}_{df.iloc[1, i]}" 
                     for i in range(len(df.columns))]
        
        # Clean up column names and data
        df = df.rename(columns={
            'Unnamed: 0_nan_Frame': 'Frame',
            'Name_nan_Time (Seconds)': 'Time_Seconds'
        })
        
        # Remove header rows and clean data
        df = df.iloc[3:].reset_index(drop=True)
        df = df.dropna(axis=1, how='all')  # Remove empty columns
        df = df.dropna()  # Remove rows with any missing values

        # Check if we have any data after processing
        if len(df) == 0:
            raise ValueError("No data found after processing CSV file. Check if the file format is correct.")
        
        # Extract timestamps
        timestamps = np.array(df.iloc[:, 1].T).astype(float) * 1e3  # Convert to milliseconds
        
        # Extract platform positions
        plat_x_col = f'{platform_name}.4_Position_X'
        plat_y_col = f'{platform_name}.5_Position_Y'
        plat_z_col = f'{platform_name}.6_Position_Z'
        
        # Check if platform columns exist
        plat_columns = [plat_x_col, plat_y_col, plat_z_col]
        missing_plat = [col for col in plat_columns if col not in df.columns]
        if missing_plat:
            print(f"Available columns: {list(df.columns)}")
            raise ValueError(f"Platform columns not found: {missing_plat}. Please check the platform name '{platform_name}'.")
        
        df_plat = df[[plat_x_col, plat_y_col, plat_z_col]].astype(float)
        
        # Check if platform data is not empty
        if len(df_plat) == 0:
            raise ValueError(f"No platform data found for name '{platform_name}'. Check if the data exists in the CSV.")
        
        # Rearrange platform positions
        platform_pos = np.array(pd.concat([df_plat.iloc[:, swap_coords[0]], df_plat.iloc[:, swap_coords[1]], df_plat.iloc[:, swap_coords[2]]], 
                                        axis=1, ignore_index=True))
        
        # Extract reference object positions
        corner_right_x_col = f'{corner_right_name}.4_Position_X'
        corner_right_y_col = f'{corner_right_name}.5_Position_Y'
        corner_right_z_col = f'{corner_right_name}.6_Position_Z'
        
        corner_left_x_col = f'{corner_left_name}.4_Position_X'
        corner_left_y_col = f'{corner_left_name}.5_Position_Y'
        corner_left_z_col = f'{corner_left_name}.6_Position_Z'
        
        # Check if corner reflector columns exist
        corner_right_columns = [corner_right_x_col, corner_right_y_col, corner_right_z_col]
        corner_left_columns = [corner_left_x_col, corner_left_y_col, corner_left_z_col]
        
        missing_right = [col for col in corner_right_columns if col not in df.columns]
        missing_left = [col for col in corner_left_columns if col not in df.columns]
        
        if missing_left:
            print(f"Warning: Left corner reflector columns not found: {missing_left}")
            ref_obj1_rearranged = np.array([0, 0, 0])  # Default position
        else:
            df_c_left = df[corner_left_columns].astype(float)
            if len(df_c_left) == 0:
                print(f"Warning: No left corner reflector data found for name '{corner_left_name}'")
                ref_obj1_rearranged = np.array([0, 0, 0])
            else:
                ref_obj1 = np.array(df_c_left.mean())
                ref_obj1_rearranged = np.array([ref_obj1[swap_coords[0]], ref_obj1[swap_coords[1]], ref_obj1[swap_coords[2]]])
        
        if missing_right:
            print(f"Warning: Right corner reflector columns not found: {missing_right}")
            ref_obj2_rearranged = np.array([0, 0, 0])  # Default position
        else:
            df_c_right = df[corner_right_columns].astype(float)
            if len(df_c_right) == 0:
                print(f"Warning: No right corner reflector data found for name '{corner_right_name}'")
                ref_obj2_rearranged = np.array([0, 0, 0])
            else:
                ref_obj2 = np.array(df_c_right.mean())
                ref_obj2_rearranged = np.array([ref_obj2[swap_coords[0]], ref_obj2[swap_coords[1]], ref_obj2[swap_coords[2]]])
        
        # Final check to ensure we have valid data
        if len(platform_pos) == 0:
            raise ValueError("Platform position data is empty. Check the CSV file format and column names.")
        
        print(f"Successfully loaded {len(platform_pos)} platform positions and {len(timestamps)} timestamps")
        
        return {
            'timestamps': timestamps,
            'platform_pos': platform_pos,
            'ref_obj1': ref_obj1_rearranged,
            'ref_obj2': ref_obj2_rearranged
        }
        
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file '{filename}' not found")
    except pd.errors.EmptyDataError:
        raise pd.errors.EmptyDataError(f"CSV file '{filename}' is empty")

def process_radar_data(data, start_bin=0):
    """
    Process radar data by cutting beginning returns and rescaling range.

    Args:
        data (dict): Dictionary containing radar data.
        start_bin (int, optional): Starting range bin to cut from. Defaults to 0.

    Returns:
        dict: Dictionary containing processed radar data.
    """
    range_bins = np.array(data['range_bins'])
    scan_data = np.array(data['scan_data'])
    
    # Ensure start_bin is within valid range
    start_bin = max(0, min(start_bin, len(range_bins) - 1))
    
    # Process data
    range_bins = range_bins[start_bin:]
    scan_data = scan_data[:, start_bin:]
    range_bins_rescaled = range_bins - range_bins[0]
    scan_data_db = np.log10(np.abs(scan_data)) * 20

    return {
        'timestamps': data['timestamps'],
        'range_bins': range_bins_rescaled,
        'scan_data': scan_data,  # Original data
        'scan_data_db': scan_data_db  # dB converted data for display
    }

def create_rti_plot(radar_data, mocap_data=None, figsize=(12, 10), num_ticks=10, cmap='viridis'):
    """
    Create Range-Time Intensity (RTI) plot from radar data with optional distance overlay.

    Args:
        radar_data (dict): Dictionary containing processed radar data.
        mocap_data (dict, optional): Dictionary containing motion capture data for distance overlay.
        figsize (tuple, optional): Figure size as (width, height) in inches. Defaults to (12, 10).
        num_ticks (int, optional): Number of ticks on axes. Defaults to 10.
        cmap (str, optional): Colormap for the plot. Defaults to 'viridis'.

    Returns:
        fig (matplotlib.figure.Figure): The created figure object.
        ax (matplotlib.axes.Axes): The axes object containing the plot.
    """
    timestamps = radar_data['timestamps']
    range_bins = radar_data['range_bins']
    scan_data = radar_data['scan_data_db']  # Use dB data for display
    
    # Create the RTI plot
    fig, ax = plt.subplots(figsize=figsize)
    
    # Display the data as an image
    im = ax.imshow(scan_data, aspect='auto', cmap=cmap, interpolation='nearest')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('dB')
    
    # Set labels and title
    ax.set_ylabel('Time (s)')
    ax.set_xlabel('Range (m)')
    
    # Set title based on whether overlay is included
    if mocap_data is not None:
        ax.set_title('Range-Time Intensity Plot with Distance Overlay')
    else:
        ax.set_title('Range-Time Intensity Plot')
    
    # Range axis ticks
    range_axis = np.linspace(0, range_bins[-1], len(range_bins))
    tick_positions = np.linspace(0, len(range_bins) - 1, num_ticks).astype(int)
    tick_labels = range_axis[tick_positions]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(np.round(tick_labels, 2), rotation=45)
    
    # Time axis ticks
    y_tick_positions = np.linspace(0, len(timestamps) - 1, num_ticks).astype(int)
    y_tick_labels = np.linspace(0, timestamps[-1] / 1000, num_ticks)  # Convert from milliseconds to seconds
    ax.set_yticks(y_tick_positions)
    ax.set_yticklabels(np.round(y_tick_labels, 2))
    
    # Add distance overlay if mocap data is provided
    if mocap_data is not None:
        add_distance_overlay(ax, mocap_data, timestamps)
    
    return fig, ax

def add_distance_overlay(ax, mocap_data, timestamps):
    """
    Add distance overlay lines to the RTI plot.
    
    Args:
        ax (matplotlib.axes.Axes): The axes object to draw on.
        mocap_data (dict): Dictionary containing motion capture data.
        timestamps (ndarray): Array of radar timestamps.
    """
    platform_pos = mocap_data['platform_pos']
    ref_obj1 = mocap_data['ref_obj1']
    ref_obj2 = mocap_data['ref_obj2']
    
    # Calculate distances to reference objects
    dist_obj1 = distance_to_object(platform_pos, ref_obj1)
    dist_obj2 = distance_to_object(platform_pos, ref_obj2)
    
    # Get current x-axis tick positions and labels
    x_ticks = ax.get_xticks()
    x_labels = [float(label.get_text()) for label in ax.get_xticklabels()]
    
    # Create interpolation function for mapping distances to plot coordinates
    range_to_plot = interp1d(x_labels, x_ticks, bounds_error=False, fill_value='extrapolate')
    
    # Convert distances to plot coordinates
    plot_coords_obj1 = range_to_plot(dist_obj1)
    plot_coords_obj2 = range_to_plot(dist_obj2)
    
    # Create time indices and plot
    mocap_time_indices = np.linspace(0, len(timestamps) - 1, len(dist_obj1))
    
    # Plot distance lines
    ax.plot(plot_coords_obj1, mocap_time_indices, 'r-', linewidth=2, 
            label=f'Distance to Object 1 (min: {np.min(dist_obj1):.1f}m)')
    ax.plot(plot_coords_obj2, mocap_time_indices, 'orange', linewidth=2, 
            label=f'Distance to Object 2 (min: {np.min(dist_obj2):.1f}m)')
    ax.legend(loc='upper right')

def create_distance_plot(mocap_data, radar_data, figsize=(8, 10)):
    """
    Create distance plot showing platform distance to reference objects over time.

    Args:
        mocap_data (dict): Dictionary containing motion capture data.
        radar_data (dict): Dictionary containing radar data for range limits.
        figsize (tuple, optional): Figure size as (width, height) in inches. Defaults to (8, 10).

    Returns:
        fig (matplotlib.figure.Figure): The created figure object.
        ax (matplotlib.axes.Axes): The axes object containing the plot.
    """
    timestamps = mocap_data['timestamps']
    platform_pos = mocap_data['platform_pos']
    ref_obj1 = mocap_data['ref_obj1']
    ref_obj2 = mocap_data['ref_obj2']
    
    # Calculate distances
    dist_obj1 = distance_to_object(platform_pos, ref_obj1)
    dist_obj2 = distance_to_object(platform_pos, ref_obj2)
    
    # Create plot
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(dist_obj1, timestamps / 1000, label='Distance to Object 1')
    ax.plot(dist_obj2, timestamps / 1000, label='Distance to Object 2')
    
    ax.set_xlim(2, radar_data['range_bins'][-1])
    ax.set_ylabel('Time (s)')
    ax.set_xlabel('Distance (Range) (m)')
    ax.set_title('RTI-style Distance Plot (Range vs. Time)')
    ax.legend()
    ax.grid(True)
    ax.invert_yaxis()
    
    return fig, ax

def create_3d_trajectory_plot(mocap_data, figsize=(10, 8)):
    """
    Create 3D trajectory plot showing platform movement and reference objects.

    Args:
        mocap_data (dict): Dictionary containing motion capture data.
        figsize (tuple, optional): Figure size as (width, height) in inches. Defaults to (10, 8).

    Returns:
        fig (matplotlib.figure.Figure): The created figure object.
        ax (matplotlib.axes.Axes): The axes object containing the plot.
    """
    platform_pos = mocap_data['platform_pos']
    ref_obj1 = mocap_data['ref_obj1']
    ref_obj2 = mocap_data['ref_obj2']
    
    # Check if we have valid platform position data
    if len(platform_pos) == 0:
        raise ValueError("No platform position data available for 3D trajectory plot")
    
    # Extract coordinates
    x = platform_pos[:, 0]
    y = platform_pos[:, 1]
    z = platform_pos[:, 2]
    
    # Create 3D plot
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot trajectory
    ax.plot(x, y, z, marker='o', linestyle='-', color='blue', markersize=4, linewidth=1)
    
    # Plot reference objects
    ax.scatter(ref_obj1[0], ref_obj1[1], ref_obj1[2], c='orange', marker='o', s=100, label='Object 1')
    ax.scatter(ref_obj2[0], ref_obj2[1], ref_obj2[2], c='red', marker='o', s=100, label='Object 2')
    
    # Plot start and end points (only if we have data)
    if len(x) > 0:
        ax.scatter(x[0], y[0], z[0], color='green', s=100, label='Start Point', marker='^')
        ax.scatter(x[-1], y[-1], z[-1], color='red', s=100, label='End Point', marker='X')
    
    # Set labels and title
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.set_zlabel('Z Coordinate')
    ax.set_title('3D Trajectory Map')
    ax.grid(True)
    ax.legend()
    
    # Set equal aspect ratio
    max_range = np.max([x.max()-x.min(), y.max()-y.min(), z.max()-z.min()])
    mid_x = (x.max() + x.min()) * 0.5
    mid_y = (y.max() + y.min()) * 0.5
    mid_z = (z.max() + z.min()) * 0.5
    
    ax.set_xlim(mid_x - max_range * 0.5, mid_x + max_range * 0.5)
    ax.set_ylim(mid_y - max_range * 0.5, mid_y + max_range * 0.5)
    ax.set_zlim(mid_z - max_range * 0.5, mid_z + max_range * 0.5)
    
    return fig, ax

def create_coordinates_vs_time_plot(mocap_data, figsize=(12, 6)):
    """
    Create X, Y, and Z coordinates vs time plot.

    Args:
        mocap_data (dict): Dictionary containing motion capture data.
        figsize (tuple, optional): Figure size as (width, height) in inches. Defaults to (12, 6).

    Returns:
        fig (matplotlib.figure.Figure): The created figure object.
        ax (matplotlib.axes.Axes): The axes object containing the plot.
    """
    timestamps = mocap_data['timestamps']
    platform_pos = mocap_data['platform_pos']
    
    # Check if we have valid platform position data
    if len(platform_pos) == 0:
        raise ValueError("No platform position data available for coordinates vs time plot")
    
    # Extract coordinates
    x = platform_pos[:, 0]
    y = platform_pos[:, 1]
    z = platform_pos[:, 2]
    
    # Create plot
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot X, Y, and Z vs Time
    ax.plot(timestamps, x, label='X Coordinate', color='blue', linestyle='-', marker='o', markersize=3)
    ax.plot(timestamps, y, label='Y Coordinate', color='green', linestyle='-', marker='x', markersize=3)
    ax.plot(timestamps, z, label='Z Coordinate', color='red', linestyle='-', marker='s', markersize=3)
    
    # Set labels and title
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Coordinate Value')
    ax.set_title('X, Y, and Z Coordinates vs. Time')
    ax.grid(True)
    ax.legend()
    
    return fig, ax

def save_processed_data(radar_data, mocap_data, radar_output_filename, mocap_output_filename):
    """
    Save processed data to files.

    Args:
        radar_data (dict): Dictionary containing processed radar data.
        mocap_data (dict): Dictionary containing motion capture data.
        radar_filename (str): Base filename for the processed radar data.
        mocap_output_filename (str): Output filename for the mocap data pickle file.
    """
    radar_dict = {
        'timestamps': radar_data['timestamps'],
        'range_bins': radar_data['range_bins'].tolist(),
        'scan_data': radar_data['scan_data'].tolist()  # Original data, not dB
    }
    
    # Prepare mocap data
    mocap_dict = {
        'timestamps': mocap_data['timestamps'],
        'platform_pos': mocap_data['platform_pos'],
        'ref_obj1': mocap_data['ref_obj1'],
        'ref_obj2': mocap_data['ref_obj2']
    }
    
    # Save files
    with open(radar_output_filename + '.pkl', 'wb') as f:
        pickle.dump(radar_dict, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"\nProcessed radar data saved to new file '{radar_output_filename}.pkl'")
    
    with open(mocap_output_filename + '.pkl', 'wb') as f:
        pickle.dump(mocap_dict, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Motion capture data saved to new file '{mocap_output_filename}.pkl'")

def preview_radar_cut(radar_data, start_bin):
    """
    Preview radar data with a specific start bin cut without modifying the original data.
    
    Args:
        radar_data (dict): Original radar data dictionary.
        start_bin (int): Starting range bin to preview.
            
    Returns:
        preview_data (dict): Preview of processed radar data with the specified cut.
    """
    range_bins = np.array(radar_data['range_bins'])
    scan_data = np.array(radar_data['scan_data'])
    
    # Ensure start_bin is within valid range
    start_bin = max(0, min(start_bin, len(range_bins) - 1))
    
    # Process preview data
    preview_range_bins = range_bins[start_bin:]
    preview_scan_data = scan_data[:, start_bin:]
    preview_range_bins_rescaled = preview_range_bins - preview_range_bins[0]
    preview_scan_data_db = np.log10(np.abs(preview_scan_data)) * 20

    return {
        'timestamps': radar_data['timestamps'],
        'range_bins': preview_range_bins_rescaled,
        'scan_data': preview_scan_data_db
    }

def interactive_radar_cut(radar_data, mocap_data, num_ticks=10):
    """
    Interactive loop for adjusting radar start bin with preview plots.
    
    Args:
        radar_data (dict): Original radar data dictionary.
        mocap_data (dict): Motion capture data for overlay.
        num_ticks (int, optional): Number of ticks on axes. Defaults to 10.
            
    Returns:
        final_start_bin (int): Final confirmed start bin value.
    """
    
    current_start_bin = 0
    max_bin = len(radar_data['range_bins']) - 1
    
    print(f"\nAdjusting range offset through interactive start bin cutting")
    print(f"Available range: 0 to {max_bin}")
    print(f"Use the slider to adjust the start bin, then click 'Confirm' or 'Quit'")
    
    # Create the main figure with subplots
    fig = plt.figure(figsize=(15, 10))
    ax_main = plt.subplot2grid((5, 4), (0, 0), colspan=4, rowspan=4)
    
    # Create slider and button areas
    ax_slider = plt.subplot2grid((5, 4), (4, 1), colspan=2)
    ax_confirm = plt.subplot2grid((5, 4), (4, 0))
    ax_quit = plt.subplot2grid((5, 4), (4, 3))
    
    # Initial preview data
    preview_data = preview_radar_cut(radar_data, current_start_bin)
    timestamps = preview_data['timestamps']
    range_bins = preview_data['range_bins']
    scan_data = preview_data['scan_data']
    
    # Display the data as an image and add colorbar
    im = ax_main.imshow(scan_data, aspect='auto', cmap='viridis', interpolation='nearest')
    cbar = plt.colorbar(im, ax=ax_main)
    cbar.set_label('dB')
    
    # Set labels and title
    ax_main.set_xlabel('Range (m)')
    ax_main.set_title(f'Range-Time Intensity Plot with Distance Overlay')
    
    # Set up fixed tick positions
    num_ticks = 10
    x_tick_positions = np.linspace(0, len(range_bins) - 1, num_ticks).astype(int)
    
    # Set initial tick positions and labels
    ax_main.set_xticks(x_tick_positions)
    x_tick_labels = np.linspace(0, range_bins[-1], num_ticks)
    ax_main.set_xticklabels(np.round(x_tick_labels, 2), rotation=45)
    
    # Add distance overlay
    add_distance_overlay(ax_main, mocap_data, timestamps)
    
    # Create slider
    slider = Slider(
        ax_slider, 'Start Bin', 0, max_bin,
        valinit=current_start_bin, valstep=1
    )
    
    # Create buttons
    confirm_button = Button(ax_confirm, 'Confirm', color='lightgreen', hovercolor='green')
    quit_button = Button(ax_quit, 'Quit', color='lightcoral', hovercolor='red')
    
    # Variables to store the result
    result = {'start_bin': None, 'confirmed': False}
    
    def update(val):
        """Update the plot when slider changes."""
        nonlocal current_start_bin, preview_data, range_bins, scan_data
        
        current_start_bin = int(val)
        
        # Update preview, plot, and image data
        preview_data = preview_radar_cut(radar_data, current_start_bin)
        range_bins = preview_data['range_bins']
        scan_data = preview_data['scan_data']
        im.set_array(scan_data)
        
        # Update tick labels nad title
        x_tick_labels = np.linspace(0, range_bins[-1], num_ticks)
        ax_main.set_xticklabels(np.round(x_tick_labels, 2), rotation=45)
        ax_main.set_title(f'Range-Time Intensity Plot with Distance Overlay')
    
        # Clear all lines and legend
        for line in ax_main.lines:
            line.remove()
        
        # Redraw distance overlay
        add_distance_overlay(ax_main, mocap_data, timestamps)
        
        fig.canvas.draw_idle()
    
    def confirm(event):
        """Handle confirm button click."""
        result['start_bin'] = current_start_bin
        result['confirmed'] = True
        plt.close(fig)
    
    def quit_app(event):
        """Handle quit button click."""
        result['confirmed'] = False
        plt.close(fig)
    
    # Connect the slider and buttons
    slider.on_changed(update)
    confirm_button.on_clicked(confirm)
    quit_button.on_clicked(quit_app)
    
    # Show the plot
    plt.tight_layout()
    plt.show()
    
    # Return the result
    if result['confirmed']:
        print(f"Confirmed start bin: {result['start_bin']}")
        return result['start_bin']
    else:
        print("Exiting without processing radar data.")
        return None

def parse_args(args):
    """
    Input argument parser.

    Args:
        args (list): Input arguments as taken from command line execution via sys.argv[1:].

    Returns:
        parsed_args (namespace): Parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Motion capture and radar data processor')
    parser.add_argument('radar_file', 
                        help='Path and name of pickle file containing radar data')
    parser.add_argument('mocap_file',
                        help='Path and name of CSV file containing motion capture data')
    parser.add_argument('--platform-name', type=str, required=True,
                        help='name for drone/radar platform columns in CSV (required)')
    parser.add_argument('--corner-right-name', type=str, required=True,
                        help='name for right corner reflector columns in CSV (required)')
    parser.add_argument('--corner-left-name', type=str, required=True,
                        help='name for left corner reflector columns in CSV (required)')
    parser.add_argument('--start-bin', type=int, default=0,
                        help='Starting range bin to cut from radar data (default: 0)')
    parser.add_argument('--save-plots', action='store_true',
                        help='Save all plots to PNG files')
    parser.add_argument('--save-data', action='store_true',
                        help='Save processed data to pickle file')
    parser.add_argument('--radar-output-name', type=str, default=None,
                        help='Output filename name for saved radar files')
    parser.add_argument('--mocap-output-name', type=str, default=None,
                        help='Output filename name for saved mocap files')
    parser.add_argument('--skip-check', action='store_true',
                        help='Skip the check gate and proceed directly to radar processing')
    
    parsed_args = parser.parse_args(args)

    # Check if files are accessible
    is_valid_file(parser, parsed_args.radar_file, 'r')
    is_valid_file(parser, parsed_args.mocap_file, 'r')

    # Set default output name if save is requested but no name specified
    if (parsed_args.save_plots or parsed_args.save_data) and parsed_args.radar_output_name is None:
        radar_path = Path(parsed_args.radar_file)
        parsed_args.radar_output_name = radar_path.stem + '_processed'
    if (parsed_args.save_plots or parsed_args.save_data) and parsed_args.mocap_output_name is None:
        mocap_path = Path(parsed_args.mocap_file)
        parsed_args.mocap_output_name = mocap_path.stem

    return parsed_args

def main(args):
    """
    Main function to process motion capture and radar data.

    Args:
        args (list): Input arguments as taken from command line execution via sys.argv[1:].

    Returns:
        combined_data (dict): Dictionary containing both processed radar and motion capture data.
    """
    # Parse input arguments
    parsed_args = parse_args(args)
    
    # Load motion capture data first
    print(f"Loading motion capture data from '{parsed_args.mocap_file}'...")
    print(f"Using column names - Platform: {parsed_args.platform_name}, "
          f"Right Corner: {parsed_args.corner_right_name}, "
          f"Left Corner: {parsed_args.corner_left_name}")
    
    # Prompt for coordinate swap
    swap_coords = None
    swap_input = None
    while True:
        swap_input = input("Do you want to swap the coordinate order to (z, x, y)? (y/n): ").strip().lower()
        if swap_input in ['y', 'yes']:
            swap_coords = (2, 0, 1)
            print("Coordinate order swapped to (z, x, y).")
            break
        elif swap_input in ['n', 'no']:
            swap_coords = (0, 1, 2)
            print("Coordinate order left as is.")
            break
        else:
            print("Please enter 'y' for yes or 'n' for no.")

    mocap_data = load_mocap_csv(
        parsed_args.mocap_file,
        platform_name=parsed_args.platform_name,
        corner_right_name=parsed_args.corner_right_name,
        corner_left_name=parsed_args.corner_left_name,
        swap_coords=swap_coords
    )

    # Create motion capture plots first
    print("Showing motion capture plots...")
    
    # Coordinates vs time plot
    coord_fig, coord_ax = create_coordinates_vs_time_plot(mocap_data)
    if parsed_args.save_plots:
        coord_filename = f"{parsed_args.mocap_output_name}_coordinates.png"
        print(f"Saving coordinates plot to '{coord_filename}'...")
        coord_fig.savefig(coord_filename, dpi=300, bbox_inches='tight')
    
    # 3D trajectory plot
    traj_fig, traj_ax = create_3d_trajectory_plot(mocap_data)
    if parsed_args.save_plots:
        traj_filename = f"{parsed_args.mocap_output_name}_trajectory.png"
        print(f"Saving trajectory plot to '{traj_filename}'...")
        traj_fig.savefig(traj_filename, dpi=300, bbox_inches='tight')
    
    # Check gate
    if not parsed_args.skip_check:
        print("Please review the motion capture data and plots. Close the plots to proceed.")
        print("\n" + "="*60)
        print("Motion capture data processing completed!")
        print("="*60)
        
        # Display only motion capture plots
        plt.show()
        
        while True:
            proceed = input("\nDo you want to proceed with radar data processing? (y/n): ").lower().strip()
            if proceed in ['y', 'yes']:
                print("Proceeding with radar data processing...")
                break
            elif proceed in ['n', 'no']:
                print("Radar data processing skipped. Exiting...")
                return {'mocap_data': mocap_data, 'radar_data': None}
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    elif parsed_args.skip_check:
        print("Skipping check gate - proceeding directly to radar processing...")
    
    # Load radar data
    print(f"Loading radar data from '{parsed_args.radar_file}'...")
    radar_data = load_radar_data(parsed_args.radar_file)
    
    # Distance plot
    print("Showing distance plot...")
    dist_fig, dist_ax = create_distance_plot(mocap_data, radar_data)
    if parsed_args.save_plots:
        dist_filename = f"{parsed_args.radar_output_name}_distance.png"
        print(f"Saving distance plot to '{dist_filename}'...")
        dist_fig.savefig(dist_filename, dpi=300, bbox_inches='tight')
        plt.show()
        
    # Interactive radar data cutting
    final_start_bin = interactive_radar_cut(radar_data, mocap_data)
    if final_start_bin is None:
        return {'mocap_data': mocap_data, 'radar_data': None}

    # Process radar data with final confirmed start bin
    print(f"Processing radar data with final start bin: {final_start_bin}")
    processed_radar = process_radar_data(radar_data, final_start_bin)
    
    # RTI plot with distance overlay
    print("Showing final RTI plot with distance overlay...")
    rti_fig, rti_ax = create_rti_plot(processed_radar, mocap_data)
    if parsed_args.save_plots:
        rti_filename = f"{parsed_args.radar_output_name}_rti_with_overlay.png"
        print(f"Saving RTI plot with overlay to '{rti_filename}'...")
        rti_fig.savefig(rti_filename, dpi=300, bbox_inches='tight')
    
    # Save processed data if requested
    if parsed_args.save_data:
        save_processed_data(processed_radar, mocap_data, 
                          radar_output_filename=parsed_args.radar_output_name,
                          mocap_output_filename=parsed_args.mocap_output_name)
    
    # Display plots
    print("\n" + "="*60)
    print("All processing completed!")
    print("="*60)
    plt.show()

    # --- Logging setup ---
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / f"data_processor_{timestamp}.log"
    with open(log_file, "a") as logf:
        logf.write(f"[Parameters]\n")
        logf.write(pprint.pformat(vars(parsed_args)) + "\n")
        logf.write(f"\nRadar file: {parsed_args.radar_file}\n")
        logf.write(f"Range start_bin where data was cut: {final_start_bin}\n")
        logf.write(f"\n[Radar Data]\n")
        logf.write(f"  range_bins shape: {radar_data['range_bins'].shape}\n")
        logf.write(f"  scan_data shape: {radar_data['scan_data'].shape}\n")
        logf.write(f"  timestamps shape: {radar_data['timestamps'].shape}\n")
        logf.write(f"  first timestamp: {radar_data['timestamps'][0]}\n")
        logf.write(f"  last timestamp: {radar_data['timestamps'][-1]}\n")
        logf.write("---\n")
        logf.write(f"\nMocap file: {parsed_args.mocap_file}\n")
        logf.write(f"Coordinate swap to (z, x, y): {swap_input}\n")
        logf.write(f"\n[Mocap Data]\n")
        logf.write(f"  platform_pos shape: {mocap_data['platform_pos'].shape}\n")
        logf.write(f"  timestamps shape: {mocap_data['timestamps'].shape}\n")
        logf.write(f"  first timestamp: {mocap_data['timestamps'][0]}\n")
        logf.write(f"  last timestamp: {mocap_data['timestamps'][-1]}\n")
        logf.write(f"  ref_obj1: {mocap_data['ref_obj1']}\n")
        logf.write(f"  ref_obj2: {mocap_data['ref_obj2']}\n")
        logf.write("---\n")
    print(f"[LOG] Data log saved to {log_file}")
    # --- End logging ---

if __name__ == "__main__":
    """Standard Python alias for command line execution."""
    main(sys.argv[1:]) 