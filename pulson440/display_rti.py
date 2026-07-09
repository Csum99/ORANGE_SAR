#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Standalone radar RTI (Range-Time Intensity) display script for more detailed figures."""

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
import pickle
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
from common.constants import SPEED_OF_LIGHT
from common.helper_functions import is_valid_file


def load_pickle_data(filename):
    """Load radar data from pickle file.

    Args:
        filename (str)
            Path and name of pickle file containing radar data.

    Returns:
        data (dict)
            Dictionary containing radar data with keys:
            - 'timestamps': Array of timestamps for each scan
            - 'range_bins': Array of range bin values
            - 'scan_data': 2D array of radar scan data
            - Other keys are ignored for the RTI display

    Raises:
        FileNotFoundError: If the pickle file doesn't exist
        pickle.UnpicklingError: If the file is not a valid pickle file
    """
    try:
        with open(filename, 'rb') as f:
            data = pickle.load(f)
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"Pickle file '{filename}' not found")
    except pickle.UnpicklingError:
        raise pickle.UnpicklingError(f"File '{filename}' is not a valid pickle file")


def calculate_range_axis(range_bins):
    """Calculate range axis values from range bins.

    Args:
        range_bins (ndarray)
            Array of range bin indices.
    
    Returns:
        range_axis (ndarray)
            Array of range values in meters.
    """
    return np.linspace(0, range_bins[-1], len(range_bins))


def calculate_time_axis(timestamps, num_ticks=10):
    """Calculate time axis values from timestamps.

    Args:
        timestamps (ndarray)
            Array of timestamps in milliseconds.
        num_ticks (int, optional)
            Number of ticks to display on time axis. Defaults to 10.

    Returns:
        time_axis (ndarray)
            Array of time values in seconds.
    """
    # Convert from milliseconds to seconds
    total_time_seconds = (timestamps[-1] - timestamps[0]) / 1000
    return np.linspace(0, total_time_seconds, num_ticks)


def create_rti_plot(db_data, range_axis, time_axis, figsize=(10, 8), num_ticks=10, cmap='viridis'):
    """Create and display Range-Time Intensity (RTI) plot.

    Args:
        db_data (ndarray)
            2D array of radar data in decibel scale.
        range_axis (ndarray)
            Array of range values in meters.
        time_axis (ndarray)
            Array of time values in seconds.
        figsize (tuple, optional)
            Figure size as (width, height) in inches. Defaults to (10, 8).
        cmap (str, optional)
            Colormap for the plot. Defaults to 'viridis'.

    Returns:
        fig (matplotlib.figure.Figure)
            The created figure object.
        ax (matplotlib.axes.Axes)
            The axes object containing the plot.
    """
    # Create the RTI plot
    fig, ax = plt.subplots(figsize=figsize)
    
    # Display the data as an image
    im = ax.imshow(db_data, aspect='auto', cmap=cmap, interpolation='nearest')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('dB')
    
    # Set labels and title
    ax.set_ylabel('Time (s)')
    ax.set_xlabel('Range (m)')
    ax.set_title('Range-Time Intensity Plot')
    
    # Range axis ticks
    tick_positions = np.linspace(0, len(range_axis) - 1, num_ticks).astype(int)
    tick_labels = range_axis[tick_positions]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(np.round(tick_labels, 2), rotation=45)
    
    # Time axis ticks
    y_tick_positions = np.linspace(0, len(db_data) - 1, num_ticks).astype(int)
    y_tick_labels = time_axis
    ax.set_yticks(y_tick_positions)
    ax.set_yticklabels(np.round(y_tick_labels, 2))
    
    return fig, ax


def parse_args(args):
    """Input argument parser.

    Args:
        args (list)
            Input arguments as taken from command line execution via sys.argv[1:].

    Returns:
        parsed_args (namespace)
            Parsed arguments.
    """
    parser = argparse.ArgumentParser(description='PulsON 440 radar RTI display')
    parser.add_argument('pickle_filename', 
                        help='Path and name of pickle file containing radar data')
    parser.add_argument('--save', action='store_true',
                        help='Save the RTI plot to a PNG file')
    parser.add_argument('--output', type=str, default=None,
                        help='Output filename for saved plot (defaults to pickle_filename_rti.png)')
    parsed_args = parser.parse_args(args)

    # Check if files are accessible
    is_valid_file(parser, parsed_args.pickle_filename, 'r')

    # Set default output filename if save is requested but no output specified
    if parsed_args.save and parsed_args.output is None:
        pickle_path = Path(parsed_args.pickle_filename)
        parsed_args.output = f"{pickle_path.stem}_rti.png"

    return parsed_args


def main(args):
    """Main function to load and display RTI plot from pickle data.

    Args:
        args (list)
            Input arguments as taken from command line execution via sys.argv[1:].

    Returns:
        data (dict)
            Loaded radar data dictionary.
    """
    # Parse input arguments
    parsed_args = parse_args(args)
    
    # Load data from pickle file
    print(f"Loading data from '{parsed_args.pickle_filename}'...")
    data = load_pickle_data(parsed_args.pickle_filename)
    
    # Extract data components
    timestamps = np.array(data['timestamps'])
    range_bins = np.array(data['range_bins'])
    scan_data = np.array(data['scan_data'])
    
    # Convert to decibel scale
    db_transformed = np.log10(np.abs(scan_data)) * 20

    # Print data information
    print(f"Timestamps shape: {timestamps.shape}")
    print(f"Range bins shape: {range_bins.shape}")
    print(f"Scan data shape: {scan_data.shape}")
    print(f"DB data range: [{np.min(db_transformed):.2f}, {np.max(db_transformed):.2f}] dB")
    
    # Calculate axis values
    range_axis = calculate_range_axis(range_bins)
    time_axis = calculate_time_axis(timestamps)
    
    # Create and display RTI plot
    print("Creating RTI plot...")
    fig, ax = create_rti_plot(db_transformed, range_axis, time_axis)
    
    # Save plot if requested
    if parsed_args.save:
        print(f"Saving plot to '{parsed_args.output}'...")
        plt.savefig(parsed_args.output, dpi=300, bbox_inches='tight')
    
    # Display the plot
    plt.show()
    
    return data


if __name__ == "__main__":
    """Standard Python alias for command line execution."""
    main(sys.argv[1:])