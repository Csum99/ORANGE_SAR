#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SAR image formation via backprojection. *** STUDENT TEMPLATE ***

This formulation of backprojection assumes that the ground plane is parallel to the X-Y plane of the
coordinate system. This may require changes to the coordinate system of the platform positions.

YOUR MISSION
============
This file contains three (3) versions of the SAR backprojection algorithm, in increasing order of
sophistication. The supporting code (argument parsing, data loading, plotting) is complete and
working -- your job is to implement the algorithm cores marked with "STUDENT TODO".

    PART 1 (REQUIRED)  shift_approach()   The "textbook" version. Nested loops. Slow but clear.
    PART 2 (REQUIRED)  interp_approach()  Same math, vectorized with numpy. ~100x faster.
    PART 3 (OPTIONAL)  fourier_approach() Advanced: sub-bin alignment via phase ramps in the
                                          frequency domain. Attempt after Parts 1 and 2 pass.

Check your work at any time by running:

    python check_backprojection.py

which simulates radar data for 5 point targets at KNOWN locations and verifies that your
backprojection puts bright spots where the targets actually are.

Run on data files with, e.g.:

    python backprojection.py my_data.pkl -8 8 0.1 -8 8 0.1 -m shift -p
"""

__author__ = "Ramamurthy Bhagavatula, Michael Riedl"
__version__ = "1.0"
__maintainer__ = "Ramamurthy Bhagavatula"
__email__ = "ramamurthy.bhagavatula@ll.mit.edu"

# Update path
from ast import parse
from pathlib import Path
import sys

if Path('..//').resolve().as_posix() not in sys.path:
    sys.path.insert(0, Path('..//').resolve().as_posix())

# Import required modules and methods
import argparse
from backprojection.constants import DATA_KEYS
from common.constants import SPEED_OF_LIGHT
from common.helper_functions import deconflict_file, yes_or_no, is_valid_file, progress_bar
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from multiprocessing import shared_memory, Lock, Pool
import numpy as np
import os
import pickle
import time

# Create lock for shared memory
lock = Lock()


def shift_approach(scan_data, range_bins, platform_pos, x_vec, y_vec, z_offset=0,
                   show_progress_bar=False):
    """Backprojection using only discrete shifts.

    Args:
        scan_data (ndarray)
            M x N matrix representing M scan/pulse returns with N range bins.

        range_bins (ndarray)
            Length N vector whose i-th element is the 1-way range (m) from the radar to i-th element
            of a scan/pulse's return.

        platform_pos (ndarray)
            M x 3 matrix whose i-th row is the X-Y-Z coordinates (m) at the time of the i-th
            scan/pulse's transmission.

        x_vec (ndarray)
            Length L vector containing the X-coordinates (m) of the desired SAR image's pixel
            centers.

        y_vec (ndarray)
            Length K vector containing the Y-coordinates (m) of the desired SAR image's pixel
            centers.

        z_offset (numeric)
            Constant Z-axis position of the desired SAR image pixels, i.e., height (m) of the
            desired SAR image plane. Defaults to 0.

        show_progress_bar (bool)
            Indicates whether or not to show progress bar. Defaults to False.

    Returns:
        sar_image_complex (ndarray)
            K x L matrix containing complex-valued backprojected SAR image.
    """
    # Initialization (given)
    num_scans = scan_data.shape[0]
    num_x_coords = len(x_vec)
    num_y_coords = len(y_vec)
    sar_image_complex = np.zeros((num_y_coords, num_x_coords), dtype=np.complex128)

    # =============================================================================================
    # STUDENT TODO -- PART 1 (REQUIRED): the "shift" approach
    # =============================================================================================
    # THE BIG IDEA: A pixel of the SAR image is bright if, for EVERY scan, the radar saw a strong
    # return at exactly the distance between the radar and that pixel. So, for each pixel, we visit
    # every scan, look up the return the radar measured at the radar-to-pixel distance, and add all
    # of those returns up. Real targets add up coherently (bright); everything else cancels (dark).
    #
    # Step 1: Write a for-loop over the pixel X-coordinates.
    #         HINT: for ii in range(num_x_coords):
    #
    # Step 2: Inside it, write a for-loop over the pixel Y-coordinates (index jj).
    #
    # Step 3: Inside THAT, write a for-loop over the scans/pulses (index kk).
    #
    # Step 4: (innermost) Compute the 1-way distance between the platform position at scan kk
    #         and the current pixel, whose 3-D position is (x_vec[ii], y_vec[jj], z_offset).
    #         HINT: distance = sqrt( (x_pixel - x_platform)^2
    #                              + (y_pixel - y_platform)^2
    #                              + (z_pixel - z_platform)^2 )
    #         The platform position for scan kk is platform_pos[kk, 0], platform_pos[kk, 1],
    #         platform_pos[kk, 2]. Use np.sqrt().
    #
    # Step 5: Find WHICH range bin is closest to that distance.
    #         HINT: closest_idx = np.argmin(np.abs(one_way_range - range_bins))
    #
    # Step 6: Add that measurement to the pixel:
    #             sar_image_complex[jj, ii] += scan_data[kk, closest_idx]
    #         CAREFUL: the image is indexed [jj, ii] -- rows are Y, columns are X!
    #
    # OPTIONAL: to watch your progress on big datasets, put this inside your innermost loop
    # (requires defining `step = 0` and `start_time = time.time()` before your loops, and
    # `total_steps = num_x_coords * num_y_coords * num_scans`):
    #
    #     step += 1
    #     if show_progress_bar:
    #         progress_bar(step, total_steps, increment_name="Step",
    #                      msg="Backprojecting data via shifts", done=False,
    #                      elapsed_time=(time.time() - start_time))
    # =============================================================================================

    raise NotImplementedError("shift_approach: delete this line once you have written Part 1!")

    return sar_image_complex


def interp_approach(scan_data, range_bins, platform_pos, x_vec, y_vec, z_offset=0,
                    show_progress_bar=False, num_processes=1):
    """Backprojection using interpolated shifts.

    Args:
        scan_data (ndarray)
            M x N matrix representing M scan/pulse returns with N range bins.

        range_bins (ndarray)
            Length N vector whose i-th element is the 1-way range (m) from the radar to i-th element
            of a scan/pulse's return.

        platform_pos (ndarray)
            M x 3 matrix whose i-th row is the X-Y-Z coordinates (m) at the time of the i-th
            scan/pulse's transmission.

        x_vec (ndarray)
            Length L vector containing the X-coordinates (m) of the desired SAR image's pixel
            centers.

        y_vec (ndarray)
            Length K vector containing the Y-coordinates (m) of the desired SAR image's pixel
            centers.

        z_offset (numeric)
            Constant Z-axis position of the desired SAR image pixels, i.e., height (m) of the
            desired SAR image plane. Defaults to 0.

        show_progress_bar (bool)
            Indicates whether or not to show progress bar. Defaults to False.

        num_processes (int)
            Indicates the number of processes to use for calculations. Defaults to 1.

    Returns:
        sar_image_complex (ndarray)
            K x L matrix containing complex-valued backprojected SAR image.
    """
    # Initialization (given)
    num_scans = scan_data.shape[0]
    x_grid, y_grid = np.meshgrid(x_vec, y_vec)
    sar_image_complex = np.zeros_like(x_grid, dtype=np.complex64)

    # Single-process
    if num_processes == 1:

        # =========================================================================================
        # STUDENT TODO -- PART 2 (REQUIRED): the vectorized "interp" approach
        # =========================================================================================
        # Your Part 1 code works, but on real drone data (thousands of scans, big images) it takes
        # FOREVER, because Python loops are slow. The fix: keep only ONE loop (over scans) and make
        # numpy do all the per-pixel work in bulk with whole-array operations.
        #
        # Two upgrades over Part 1:
        #   (a) Distances for ALL pixels are computed at once using the 2-D arrays x_grid and
        #       y_grid (already made for you above with np.meshgrid).
        #   (b) Instead of snapping to the NEAREST range bin (argmin), we INTERPOLATE between the
        #       two neighboring bins with np.interp -- more accurate AND faster.
        #
        # Step 1: Write ONE for-loop over the scans.
        #         HINT: for scan_idx in range(num_scans):
        #
        # Step 2: Compute the 1-way range from the platform (at this scan) to EVERY pixel at once.
        #         Same distance formula as Part 1, but use the full arrays x_grid and y_grid
        #         instead of single values -- and NO extra loops:
        #         HINT: one_way_range_grid = np.sqrt(
        #                   (x_grid - platform_pos[scan_idx, 0]) ** 2
        #                 + (y_grid - platform_pos[scan_idx, 1]) ** 2
        #                 + (z_offset - platform_pos[scan_idx, 2]) ** 2)
        #         This produces a K x L array of distances -- one per pixel.
        #
        # Step 3: Interpolate this scan's return at every pixel's distance, and accumulate:
        #         HINT: sar_image_complex += np.interp(one_way_range_grid, range_bins,
        #                                              scan_data[scan_idx, :])
        #         np.interp handles the entire K x L array in one call.
        #
        # SPEED CHALLENGE (optional): np.sqrt is one of the slower steps. Distances and range bins
        # compare the same way whether you square-root them or not... can you eliminate np.sqrt
        # entirely? (If you compare SQUARED distances, what else must you square? Note np.interp
        # requires its 2nd argument to be increasing -- squaring keeps it increasing.)
        #
        # WHEN IT WORKS: run both methods on the same data and time them. Where does the speedup
        # come from?
        # =========================================================================================

        raise NotImplementedError("interp_approach: delete this line once you have written Part 2!")

    # Multiprocess (given) -- splits the scans across CPU cores; each worker runs
    # interp_single_scan() below, where you will port your Step 2-3 math.
    else:

        # Create blocks of shared memory for the final product (sar_image_complex), and distances (x_grid, y_grid)
        shm_sar_image_complex = shared_memory.SharedMemory(create=True, size=sar_image_complex.nbytes,
                                                           name="sar_image_complex")
        shm_array_sar_image_complex = np.ndarray(sar_image_complex.shape, sar_image_complex.dtype,
                                                 buffer=shm_sar_image_complex.buf)
        shm_array_sar_image_complex[:, :] = sar_image_complex[:, :]

        shm_x_grid = shared_memory.SharedMemory(create=True, size=x_grid.nbytes, name="x_grid")
        shm_array_x_grid = np.ndarray(x_grid.shape, dtype=x_grid.dtype, buffer=shm_x_grid.buf)
        shm_array_x_grid[:, :] = x_grid[:, :]

        shm_y_grid = shared_memory.SharedMemory(create=True, size=y_grid.nbytes, name="y_grid")
        shm_array_y_grid = np.ndarray(y_grid.shape, dtype=y_grid.dtype, buffer=shm_y_grid.buf)
        shm_array_y_grid[:, :] = y_grid[:, :]

        # Initialize multiprocess constructs
        pool = Pool(num_processes)

        # Define and launch jobs asynchronously
        jobs = []
        start_time = time.time()
        for scan_idx in range(num_scans):
            jobs.append(
                pool.apply_async(interp_single_scan,
                                 (scan_data[scan_idx], range_bins, platform_pos[scan_idx], z_offset,
                                  (len(x_vec), len(y_vec)))))

        # Wait for all jobs to finish
        [job.wait() for job in jobs]
        pool.close()
        pool.join()

        # Copy data from buffer
        sar_image_complex[:] = shm_array_sar_image_complex[:]

        # Release shared memory
        shm_sar_image_complex.close()
        shm_sar_image_complex.unlink()
        shm_x_grid.close()
        shm_x_grid.unlink()
        shm_y_grid.close()
        shm_y_grid.unlink()

        print(f"{time.time() - start_time} seconds elapsed")

    return sar_image_complex


def interp_single_scan(scan_data, range_bins, platform_pos, z_offset, dims):
    """Compute the contribution of a single scan to the SAR image using the interpolation approach.
    Used only by the multiprocess (-np > 1) mode of interp_approach.

    Args:
        scan_data (ndarray)
            Length N vector containing scan/pulse's return.

        range_bins (ndarray)
            Length N vector whose i-th element is the 1-way range (m) from the radar to i-th element
            of a scan/pulse's return.

        platform_pos (ndarray)
            Length 3 vector containing the X-Y-Z coordinate (m) of the platform at the time of the
            scan/pulse.

        z_offset (numeric)
            Constant Z-axis position of the desired SAR image pixels, i.e., height (m) of the
            desired SAR image plane.

        dims (ndarray)
            Width and height of output image. Used to load correct number of bytes from shared memory.

    """

    # Load shared memory (given)
    existing_shm = shared_memory.SharedMemory(name="sar_image_complex")
    shm_x_grid = shared_memory.SharedMemory(name="x_grid")
    shm_y_grid = shared_memory.SharedMemory(name="y_grid")

    np_array = np.ndarray((dims[0], dims[1],), dtype=np.complex64, buffer=existing_shm.buf)
    shm_array_x_grid = np.ndarray((dims[0], dims[1],), dtype=np.float64, buffer=shm_x_grid.buf)
    shm_array_y_grid = np.ndarray((dims[0], dims[1],), dtype=np.float64, buffer=shm_y_grid.buf)

    # =============================================================================================
    # STUDENT TODO -- PART 2b (do after Part 2 works): port your math to the parallel worker
    # =============================================================================================
    # This function is what each CPU core runs when you pass -np 4 (etc.) on the command line.
    # It handles ONE scan. The shared-memory plumbing above/below is done for you.
    #
    # Step 1: Compute the 1-way range grid exactly like Step 2 of Part 2, EXCEPT:
    #           - use shm_array_x_grid and shm_array_y_grid as the pixel grids, and
    #           - platform_pos here is a length-3 vector, so its coordinates are
    #             platform_pos[0], platform_pos[1], platform_pos[2] (no scan index).
    #
    # Step 2: interp = np.interp(<your range grid>, range_bins, scan_data)
    #         (scan_data here is already just this one scan's vector.)
    #
    # Step 3: Accumulate into the shared image -- MUST be wrapped in the lock so two workers
    #         don't write at the same time:
    #             lock.acquire()
    #             np_array[:] += interp
    #             lock.release()
    # =============================================================================================

    raise NotImplementedError("interp_single_scan: delete this line once you have written Part 2b!")

    # Release shared memory (given)
    existing_shm.close()
    shm_x_grid.close()
    shm_y_grid.close()


def fourier_approach(center_freq, scan_data, range_bins, platform_pos, x_vec, y_vec, z_offset=0,
                     show_progress_bar=False):
    """Backprojection using shifts implemented through linear phase ramps. Only applies to data
    simulated using simulate_sar_data.py.

    Args:
        center_freq (float)
            Center frequency of radar (Hz).

        scan_data (ndarray)
            M x N matrix representing M scan/pulse returns with N range bins.

        range_bins (ndarray)
            Length N vector whose i-th element is the 1-way range (m) from the radar to i-th element
            of a scan/pulse's return.

        platform_pos (ndarray)
            M x 3 matrix whose i-th row is the X-Y-Z coordinates (m) at the time of the i-th
            scan/pulse's transmission.

        x_vec (ndarray)
            Length L vector containing the X-coordinates (m) of the desired SAR image's pixel
            centers.

        y_vec (ndarray)
            Length K vector containing the Y-coordinates (m) of the desired SAR image's pixel
            centers.

        z_offset (numeric)
            Constant Z-axis position of the desired SAR image pixels, i.e., height (m) of the
            desired SAR image plane. Defaults to 0.

        show_progress_bar (bool)
            Indicates whether or not to show progress bar. Defaults to False.

    Returns:
        sar_image_complex (ndarray)
            K x L matrix containing complex-valued backprojected SAR image.
    """
    # Initialization (given) -- study these! You will need fast_time, ang_freq, and the grids.
    (num_scans, num_range_bins) = scan_data.shape
    num_x_coords = len(x_vec)
    num_y_coords = len(y_vec)
    fast_time = 2 * range_bins[:, np.newaxis] / SPEED_OF_LIGHT       # 2-way time of each range bin
    delta_fast_time = fast_time[1] - fast_time[0]                    # time between range bins
    ang_freq = np.transpose(2 * np.pi * np.arange(-num_range_bins / 2, num_range_bins / 2) /
                            (delta_fast_time * num_range_bins))      # FFT angular frequency axis
    x_grid, y_grid = np.meshgrid(x_vec, y_vec)
    sar_image_complex = np.zeros_like(x_grid, dtype=np.complex128)

    # =============================================================================================
    # STUDENT TODO -- PART 3 (ADVANCED / OPTIONAL): the Fourier phase-ramp approach
    # =============================================================================================
    # Attempt this only after Parts 1 and 2 pass the checker. If you get stuck, that is expected --
    # we will walk through this one together in a code-along session.
    #
    # THE BIG IDEA: Parts 1 and 2 shift each scan by whole or interpolated range bins. But the
    # Fourier shift theorem lets us delay a signal by ANY amount -- including a fraction of a
    # bin -- by multiplying its FFT by a linear phase ramp exp(1j * omega * t_shift). We also
    # demodulate by the carrier so that the phase history lines up exactly. This approach
    # processes an entire COLUMN of the image at a time.
    #
    # Structure: an outer loop over image columns (X), an inner loop over scans.
    #
    # Step 1: Loop over columns:  for ii in range(num_x_coords):
    #
    # Step 2: Make an accumulator for this column:
    #             sum_aligned_scans = np.zeros(num_y_coords, dtype=np.complex128)
    #
    # Step 3: Inner loop over scans:  for jj in range(num_scans):
    #
    # Step 4: Compute the 2-WAY time delay from the platform (scan jj) to every pixel in this
    #         column. The column's pixels have coordinates (x_grid[:, ii], y_grid[:, ii], z_offset).
    #         HINT: two_way_time = 2 * np.sqrt( (x_grid[:, ii] - platform_pos[jj, 0]) ** 2
    #                                         + (y_grid[:, ii] - platform_pos[jj, 1]) ** 2
    #                                         + (z_offset      - platform_pos[jj, 2]) ** 2
    #                                         ) / SPEED_OF_LIGHT
    #         (Note: 2-way this time, hence the factor of 2 and dividing by the speed of light.)
    #
    # Step 5: Demodulate the scan to baseband relative to each pixel's delay:
    #         HINT: demod_pulse = (scan_data[jj, :][:, np.newaxis]
    #                              * np.exp(-1j * 2 * np.pi * center_freq
    #                                       * (fast_time - two_way_time)))
    #         Broadcasting makes this an N x K array: one shifted copy per pixel in the column.
    #
    # Step 6: Apply the Fourier shift theorem to align each copy to its pixel's delay:
    #         HINT (3 sub-steps):
    #             demod_pulse_freq = np.fft.fftshift(np.fft.fft(demod_pulse, axis=0), axes=0)
    #             phase_shift = np.exp(1j * np.outer(ang_freq, two_way_time))
    #             scan_aligned = np.fft.ifft(np.fft.ifftshift(phase_shift * demod_pulse_freq,
    #                                                         axes=0), axis=0)
    #
    # Step 7: After alignment, each pixel's contribution sits in row 0. Accumulate it:
    #             sum_aligned_scans += np.transpose(scan_aligned[0])
    #
    # Step 8: (back in the OUTER loop, after the scan loop finishes) store the finished column:
    #             sar_image_complex[:, ii] = sum_aligned_scans
    # =============================================================================================

    raise NotImplementedError("fourier_approach: delete this line once you have written Part 3! "
                              "(Part 3 is optional -- use -m shift or -m interp instead.)")

    return sar_image_complex


def parse_args(args, cmd_line):
    """Input argument parser.

    Args:
        args (list)
            List of input arguments as taken from command line execution via sys.argv[1:].

        cmd_line (bool)
            Indicates whether or not method was called via command line.

    Returns:
        parsed_args (Namespace)
            Parsed arguments.
    """
    # Parse input arguments
    parser = argparse.ArgumentParser(
        description="SAR image formation via backprojection.",
        epilog=("This formulation of backprojection assumes that the ground plane is parallel to "
                "the X-Y plane of the coordinate system. This may require you to change the "
                "coordinate system of the platform positions. Output consists of backprojected SAR "
                "image and associated metadata."))
    parser.add_argument('data_file', nargs='?', type=str,
                        help=("File containing pickled data; expected content is a dictionary with "
                              "keys [scan_data, platform_pos, range_bins]"))
    parser.add_argument('x_min', type=float,
                        help=("SAR image pixels\' minimum X-coordinate (m)"))
    parser.add_argument('x_max', type=float,
                        help=("SAR image pixels\' maximum X-coordinate (m)"))
    parser.add_argument('x_res', type=float,
                        help=("SAR image pixel X-resolution (m)"))
    parser.add_argument('y_min', type=float,
                        help=("SAR image pixels\' minimum Y-coordinate (m)"))
    parser.add_argument('y_max', type=float,
                        help=("SAR image pixels\' maximum Y-coordinate (m)"))
    parser.add_argument('y_res', type=float,
                        help=("SAR image pixel Y-resolution (m)"))
    parser.add_argument('-s', '--sar_image_file', nargs='?', const=None, default=None, type=str,
                        help=("File to save/pickle SAR image to; if not specified then SAR image is "
                              "not saved; defaults to not saving it"))
    parser.add_argument('-m', '--method', nargs='?', type=str,
                        choices=('shift', 'interp', 'fourier'), default='interp', const='interp',
                        help="Backprojection method to use; defaults to \'interp\'")
    parser.add_argument('-np', '--num_processes', type=int, default=1,
                        help="Number of processes to use; defaults to 1")
    parser.add_argument('-z', '--z_offset', type=float, default=0.0,
                        help="Constant Z-axis offset of SAR image pixels (m); defaults to 0.0")
    parser.add_argument('-fc', '--center_freq', type=float,
                        help=("Center frequency (Hz) of radar; must be specified if using "
                              "\'fourier\' method"))
    parser.add_argument('-nv', '--no_visuals', action='store_true', help="Do not display SAR image")
    parser.add_argument('-p', '--progress_bar', action='store_true', help="Show progress bar")
    parsed_args = parser.parse_args(args)

    # Do some additional checks
    if parsed_args.sar_image_file:
        if os.path.exists(parsed_args.sar_image_file):
            if cmd_line:
                yes = yes_or_no(("Specified SAR image save file already exists; do you want to "
                                 "overwrite it?"))
                if not yes:
                    parsed_args.sar_image_file = deconflict_file(parsed_args.sar_image_file)
                    print(f"Overwriting \'{parsed_args.sar_image_file}\' to save SAR image...")
            else:
                parsed_args.sar_image_file = deconflict_file(parsed_args.sar_image_file)
                print(("Specified SAR image save file already exists; using "
                       f"\'{parsed_args.sar_image_file}\' to deconflict..."))
    is_valid_file(parser, parsed_args.data_file, 'r')
    is_valid_file(parser, parsed_args.sar_image_file, 'w')

    return parsed_args


def main(args, cmd_line):
    """Main execution method to perform backprojection on specified inputs.

    Args:
        args (list)
            Input arguments as taken from command line execution via sys.argv[1:].

        cmd_line (bool)
            Indicates whether or not method was called via command line.

    Returns:
        sar_image (dict)
            Contains backprojected SAR image and associated metadata; keys are [sar_image_complex,
            x_vec, y_vec, z_offset].

    Raises:
        KeyError if data dictionary loaded from file does not contain all required keys.
        TypeError if not all values in dictionary are ndarrays.
        IndexError if scan data is not a 2-D matrix.
        IndexError if range bins are not a vector.
        IndexError if platform positions are not a 2-D matrix.
        IndexError if platform positions are not explicitly 3-D X-Y-Z coordinates by shape.
        IndexError if scan data and range bins do not have compatible dimensions.
        ValueError if unknown method specified.
    """
    # Parse input arguments
    parsed_args = parse_args(args, cmd_line)

    # Load data
    with open(parsed_args.data_file, 'rb') as f:
        data = pickle.load(f)

    # Check formats and dimensionality of data
    data['scan_data'] = np.squeeze(data['scan_data'])
    data['range_bins'] = np.squeeze(data['range_bins'])
    data['platform_pos'] = np.squeeze(data['platform_pos'])
    if not all([key in data for key in DATA_KEYS]):
        raise KeyError("Loaded data dictionary does not contain all required keys!")
    elif not all([isinstance(data[key], np.ndarray) for key in DATA_KEYS]):
        raise TypeError("Loaded data dictionary values are not all numpy arrays as required!")
    elif data['scan_data'].ndim != 2:
        raise IndexError("Scan data is not a 2-D matrix!")
    elif data['range_bins'].ndim != 1:
        raise IndexError("Range bins are not a vector!")
    elif data['platform_pos'].ndim != 2:
        raise IndexError("Platform positions are not a 2-D matrix!")
    elif not any([size == 3 for size in data['platform_pos'].shape]):
        raise IndexError("Platform positions do not appear to contain 3-D X-Y-Z coordinates!")

    # Reformat data and check for consistency between dimensions
    if data['platform_pos'].shape[1] != 3:
        data['platform_pos'] = np.transpose(data['platform_pos'])
    num_scans = data['platform_pos'].shape[0]
    num_range_bins = data['range_bins'].size
    if not all([size in [num_scans, num_range_bins] for size in data['scan_data'].shape]):
        raise IndexError(("Mismatch between apparent number of scans and/or range bins represented "
                          "in data!"))
    if num_scans != data['scan_data'].shape[0]:
        data['scan_data'] = np.transpose(data['scan_data'])

    # Determine X-Y coordinates of image pixels
    x_vec = np.arange(parsed_args.x_min, parsed_args.x_max + parsed_args.x_res, parsed_args.x_res)
    y_vec = np.arange(parsed_args.y_min, parsed_args.y_max + parsed_args.y_res, parsed_args.y_res)

    # Form SAR image
    if parsed_args.method == 'shift':
        sar_image_complex = shift_approach(data['scan_data'], data['range_bins'],
                                           data['platform_pos'], x_vec, y_vec,
                                           parsed_args.z_offset, parsed_args.progress_bar)
    elif parsed_args.method == 'interp':
        sar_image_complex = interp_approach(data['scan_data'], data['range_bins'],
                                            data['platform_pos'], x_vec, y_vec,
                                            parsed_args.z_offset, parsed_args.progress_bar,
                                            parsed_args.num_processes)
    elif parsed_args.method == 'fourier':
        sar_image_complex = fourier_approach(parsed_args.center_freq, data['scan_data'],
                                             data['range_bins'], data['platform_pos'], x_vec, y_vec,
                                             parsed_args.z_offset, parsed_args.progress_bar)
    else:
        raise ValueError(f"Unknown method \'{parsed_args.method}\' specified")

    # Save image if requested
    sar_image = {'sar_image_complex': sar_image_complex, 'x_vec': x_vec, 'y_vec': y_vec,
                 'z_offset': parsed_args.z_offset}
    if parsed_args.sar_image_file:
        with open(parsed_args.sar_image_file, 'wb') as f:
            pickle.dump(sar_image, f)

    # Show SAR image with interactive dynamic-range sliders
    if not parsed_args.no_visuals:
        sar_image_db = 20 * np.log10(np.abs(sar_image_complex))
        fig, ax = plt.subplots()
        plt.subplots_adjust(left=0.25, right=0.75, bottom=0.3)
        fig.canvas.manager.set_window_title(parsed_args.data_file)
        im = ax.imshow(sar_image_db, origin='lower', cmap='viridis',
                       extent=(x_vec[0], x_vec[-1], y_vec[0], y_vec[-1]))
        plt.xlabel(f"X (m) / {sar_image_complex.shape[1]} pixels")
        plt.ylabel(f"Y (m) / {sar_image_complex.shape[0]} pixels")
        plt.colorbar(im)

        # Define initial limits based on data range
        clim_min = np.min(np.abs(sar_image_db))
        clim_max = np.max(np.abs(sar_image_db))
        im.set_clim(clim_min, clim_max)

        # Create sliders for adjusting the dynamic range
        ax_clim_min = plt.axes([0.2, 0.1, 0.6, 0.03])
        ax_clim_max = plt.axes([0.2, 0.15, 0.6, 0.03])

        slider_clim_min = Slider(ax_clim_min, 'Min', clim_min, clim_max, valinit=clim_min)
        slider_clim_max = Slider(ax_clim_max, 'Max', clim_min, clim_max, valinit=clim_max)

        # Update function to be called when slider value changes
        def update(val):
            im.set_clim(slider_clim_min.val, slider_clim_max.val)
            fig.canvas.draw_idle()

        # Connect the update function to the sliders
        slider_clim_min.on_changed(update)
        slider_clim_max.on_changed(update)

        plt.show()

    return sar_image


if __name__ == '__main__':
    """Standard Python alias for command line execution."""
    main(sys.argv[1:], True)
