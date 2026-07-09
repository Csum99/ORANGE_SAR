#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Manual alignment of motion capture and radar data for non-stationary radar starts."""

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

from utils import (
    load_radar_data,
    load_mocap_data,
    process_radar_data,
    plot_calibration_verification,
    save_processed_data,
    select_closest_mocap_to_radar,
    find_movement_start_end,
    interactive_mocap_movement_detection
)
from common.helper_functions import is_valid_file


def interactive_alignment_adjustment(scan_data, platform_pos, radar_times, mocap_times, range_bins, ref_obj1, ref_obj2, initial_lag=0):
    """Interactive alignment adjustment using keyboard controls.
    
    Args:
        scan_data (ndarray): Radar scan data
        platform_pos (ndarray): Platform positions
        range_bins (ndarray): Range bin distances
        ref_obj1, ref_obj2 (ndarray): Reference object positions
        initial_lag (int): Initial lag value
    
    Returns:
        tuple: (final_platform_pos, final_lag, confirmed)
    """
    current_lag = initial_lag
    confirmed = False
    
    print("\nInteractive Alignment Adjustment")
    print("================================")
    print("Use UP/DOWN arrow keys to adjust alignment")
    print("Use SHIFT+UP/DOWN arrow keys to adjust alignment in larger steps")
    print("Press ENTER to confirm")
    print("Press ESC to cancel")
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Create static RTI plot
    im = ax.imshow(scan_data, aspect='auto', interpolation='nearest')
    plt.colorbar(im, ax=ax)
    
    # Initialize reference lines
    # Use radar data length as the base time axis
    radar_length = scan_data.shape[0]
    y_indices = np.arange(radar_length)
    
    def clamp_lag(lag):
        max_pos = min(len(radar_times)-1, len(platform_pos)-1)
        max_neg = -min(len(mocap_times)-1, len(platform_pos)-1)
        if lag > max_pos:
            print(f"[Warning] Lag clamped to max positive: {max_pos}")
            return max_pos
        if lag < max_neg:
            print(f"[Warning] Lag clamped to max negative: {max_neg}")
            return max_neg
        return lag

    def get_aligned_positions(lag):
        """Helper function to get aligned positions with proper resampling"""
        lag = clamp_lag(lag)
        if lag > 0:
            # Mocap starts later
            radar_times_aligned = radar_times[lag:]
            mocap_times_aligned = mocap_times[:len(radar_times_aligned)]
        else:
            # Mocap starts earlier
            mocap_times_aligned = mocap_times[-lag:]
            radar_times_aligned = radar_times[:len(mocap_times_aligned)]
        
        # Reset times to start at 0
        radar_times_aligned = radar_times_aligned - radar_times_aligned[0]
        mocap_times_aligned = mocap_times_aligned - mocap_times_aligned[0]
        
        # Get properly resampled positions
        if lag > 0:
            platform_pos_trimmed = platform_pos[:len(radar_times_aligned)]
        else:
            platform_pos_trimmed = platform_pos[-lag:]
            
        aligned_pos = select_closest_mocap_to_radar(
            radar_times_aligned, 
            mocap_times_aligned, 
            platform_pos_trimmed
        )
        
        # Pad or trim to match radar length
        if len(aligned_pos) < radar_length:
            aligned_pos = np.pad(aligned_pos, ((0, radar_length - len(aligned_pos)), (0, 0)), mode='edge')
        else:
            aligned_pos = aligned_pos[:radar_length]
            
        return aligned_pos
    
    # Calculate initial trajectories
    shifted_pos = get_aligned_positions(current_lag)
    dist_obj1 = np.linalg.norm(shifted_pos - ref_obj1, axis=1)
    dist_obj2 = np.linalg.norm(shifted_pos - ref_obj2, axis=1)
    bins_obj1 = np.searchsorted(range_bins, dist_obj1)
    bins_obj2 = np.searchsorted(range_bins, dist_obj2)
    
    line1, = ax.plot(bins_obj1, y_indices, 'r-', linewidth=2, 
                     label=f'Ref Obj 1 (lag: {current_lag})')
    line2, = ax.plot(bins_obj2, y_indices, 'b-', linewidth=2, 
                     label=f'Ref Obj 2')
    
    ax.set_title(f'Alignment Adjustment (Current lag: {current_lag})')
    ax.set_xlabel('Range Bin')
    ax.set_ylabel('Time Index')
    ax.legend()
    
    def update_plot():
        nonlocal shifted_pos, current_lag
        current_lag = clamp_lag(current_lag)
        shifted_pos = get_aligned_positions(current_lag)
        
        # Compute new trajectories
        dist_obj1 = np.linalg.norm(shifted_pos - ref_obj1, axis=1)
        dist_obj2 = np.linalg.norm(shifted_pos - ref_obj2, axis=1)
        bins_obj1 = np.searchsorted(range_bins, dist_obj1)
        bins_obj2 = np.searchsorted(range_bins, dist_obj2)
        
        # Update only the line data
        line1.set_xdata(bins_obj1)
        line1.set_ydata(y_indices)
        line2.set_xdata(bins_obj2)
        line2.set_ydata(y_indices)
        
        # Update title and legend
        ax.set_title(f'Alignment Adjustment (Current lag: {current_lag})')
        line1.set_label(f'Ref Obj 1 (lag: {current_lag})')
        ax.legend()
        
        fig.canvas.draw_idle()
    
    def on_key(event):
        nonlocal current_lag, confirmed
        if event.key == 'up':
            current_lag += 5
            update_plot()
        elif event.key == 'down':
            current_lag -= 5
            update_plot()
        elif event.key == 'shift+up':
            current_lag += 50
            update_plot()
        elif event.key == 'shift+down':
            current_lag -= 50
            update_plot()
        elif event.key == 'enter':
            confirmed = True
            plt.close(fig)
        elif event.key == 'escape':
            confirmed = False
            plt.close(fig)
    
    # Connect the key press event
    fig.canvas.mpl_connect('key_press_event', on_key)
    plt.show()
    
    if confirmed:
        final_lag = clamp_lag(current_lag)
        return final_lag, True
    else:
        return None, False

def align_radar_mocap_data(radar_data, mocap_data, lag=0):
    """Align radar and mocap data using manual adjustment."""

    # Interactive adjustment
    print("Starting interactive alignment adjustment...")
    final_lag, confirmed = interactive_alignment_adjustment(
        radar_data['scan_data_db'],
        mocap_data['platform_pos'],
        radar_data['timestamps'],
        mocap_data['timestamps'],
        radar_data['range_bins'],
        mocap_data['ref_obj1'],
        mocap_data['ref_obj2'],
        initial_lag=lag
    )
    
    if not confirmed:
        print("Alignment adjustment cancelled.")
        return None, None, None, None
    
    # Clamp final_lag to valid range
    max_pos = min(len(radar_data['timestamps'])-1, len(mocap_data['platform_pos'])-1)
    max_neg = -min(len(mocap_data['timestamps'])-1, len(mocap_data['platform_pos'])-1)
    if final_lag > max_pos:
        print(f"[Warning] Final lag clamped to max positive: {max_pos}")
        final_lag = max_pos
    if final_lag < max_neg:
        print(f"[Warning] Final lag clamped to max negative: {max_neg}")
        final_lag = max_neg
    # Use the adjusted lag for final alignment
    if final_lag > 0:
        scan_data_aligned = radar_data['scan_data'][final_lag:]
        radar_times_aligned = radar_data['timestamps'][final_lag:]
        mocap_times = mocap_data['timestamps'][:len(scan_data_aligned)]
        platform_pos_trimmed = mocap_data['platform_pos'][:len(scan_data_aligned)]

    else:
        mocap_times = mocap_data['timestamps'][-final_lag:]
        platform_pos_trimmed = mocap_data['platform_pos'][-final_lag:]
        scan_data_aligned = radar_data['scan_data'][:len(platform_pos_trimmed)]
        radar_times_aligned = radar_data['timestamps'][:len(platform_pos_trimmed)]

    # Ensure times start at 0
    radar_times_aligned = radar_times_aligned - radar_times_aligned[0]
    mocap_times = mocap_times - mocap_times[0]

    # Resample mocap data to match radar timestamps exactly
    platform_pos_aligned = select_closest_mocap_to_radar(
        radar_times_aligned, mocap_times, platform_pos_trimmed
    )
    
    # Ensure all arrays have the same length
    min_length = min(len(scan_data_aligned), len(platform_pos_aligned))
    scan_data_aligned = scan_data_aligned[:min_length]
    platform_pos_aligned = platform_pos_aligned[:min_length]
    radar_times_aligned = radar_times_aligned[:min_length]

    return scan_data_aligned, platform_pos_aligned, radar_times_aligned, final_lag

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
    Main function to process motion capture and radar data for manual alignment.

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
    
    # Align radar and mocap data
    print("Aligning radar and motion capture data...")
    result = align_radar_mocap_data(radar_data, mocap_data_raw)
    
    if result is None:
        print("Alignment cancelled. Exiting...")
        return None
        
    scan_data_aligned, platform_pos_aligned, radar_times_aligned, lag = result

    # Interactive motion capture movement detection
    if not parsed_args.skip_interactive:
        print("Running interactive motion capture movement detection...")
        velocity_threshold, window_size, start_index, end_index, confirmed = interactive_mocap_movement_detection(
            platform_pos_aligned, radar_times_aligned, initial_velocity_threshold=parsed_args.velocity_threshold, initial_window=parsed_args.window_size
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
    
    # Trim aligned data based on movement detection
    platform_pos_trimmed = platform_pos_aligned[start_index:end_index]
    radar_times_trimmed = radar_times_aligned[start_index:end_index]
    scan_data_trimmed = scan_data_aligned[start_index:end_index]
    radar_times_trimmed -= radar_times_trimmed[0]

    # Show calibration verification plot
    print("Showing calibration verification plot...")
    calib_fig, calib_ax = plot_calibration_verification(
        radar_data['scan_data_db'][start_index:end_index], platform_pos_trimmed, radar_times_trimmed,
        radar_data['range_bins'], mocap_data_raw['ref_obj1'], mocap_data_raw['ref_obj2']
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
    
    # --- Logging setup ---
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = logs_dir / f"calibration_manual_{timestamp}.log"
    with open(log_file, "a") as logf:
        logf.write("[Parameters]\n")
        logf.write(pprint.pformat(vars(parsed_args)) + "\n")
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

    # After alignment (lag)
    with open(log_file, "a") as logf:
        logf.write(f"\n[Alignment Parameters]\n")
        logf.write(f"  lag: {lag}\n")
        logf.write("---\n")

    # After interactive/cmdline movement detection and before trimming
    with open(log_file, "a") as logf:
        logf.write(f"\n[Cutting Indices/Parameters]\n")
        logf.write(f"  start_index: {start_index}\n")
        logf.write(f"  end_index: {end_index}\n")
        logf.write(f"  velocity_threshold: {velocity_threshold}\n")
        logf.write(f"  window_size: {window_size}\n")
        logf.write("---\n")

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
        'scan_data': scan_data_aligned,
        'platform_pos': platform_pos_aligned,
        'times': radar_times_aligned,
        'range_bins': radar_data['range_bins']
    }


if __name__ == "__main__":
    """Standard Python alias for command line execution."""
    main(sys.argv[1:]) 