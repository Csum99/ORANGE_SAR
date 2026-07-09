#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Self-check for the student backprojection implementations.

Run from the backprojection/ folder:

    python check_backprojection.py            # checks all three approaches
    python check_backprojection.py shift      # checks only one approach
    python check_backprojection.py --plot     # also displays your SAR images

What it does:
    1. Simulates radar data for 5 point targets at KNOWN positions (an "X" pattern).
    2. Runs each of your backprojection implementations on that data.
    3. Verifies that your SAR image is bright at every target location and that the
       brightest pixel in the whole image lands on a target.

An approach that still contains its `raise NotImplementedError` line is reported as
"NOT IMPLEMENTED YET" and skipped -- that is expected until you write it.
"""

# Update path
from pathlib import Path
import sys

if Path("..//").resolve().as_posix() not in sys.path:
    sys.path.insert(0, Path("..//").resolve().as_posix())

import argparse
import time
import numpy as np

from backprojection import backprojection as bp
from backprojection.simulate_sar_data import read_sim_params, simulate_data

PARAMS_FILE = "params/selfcheck_point_scatterers.yml"

# Image grid used for the check
GRID_MIN, GRID_MAX, GRID_RES = -7.0, 7.0, 0.25

# A target counts as "found" if a bright spot is within this distance of it (meters)
POSITION_TOLERANCE = 3 * GRID_RES

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"


def check_image(sar_image_complex, x_vec, y_vec, scatterer_pos):
    """Verify bright spots appear at (and only at) the known target positions.

    Returns:
        (passed, messages) -- bool and list of human-readable result strings.
    """
    messages = []
    passed = True
    magnitude = np.abs(sar_image_complex)
    global_max = magnitude.max()

    if not np.isfinite(magnitude).all():
        return False, ["    Image contains NaN or Inf values -- check your math."]
    if global_max == 0:
        return False, ["    Image is all zeros -- are you accumulating into sar_image_complex?"]

    # Check 1: every target location should be bright (comparable to the global max)
    for (sx, sy, sz) in scatterer_pos:
        window = (np.abs(x_vec[np.newaxis, :] - sx) <= POSITION_TOLERANCE) & \
                 (np.abs(y_vec[:, np.newaxis] - sy) <= POSITION_TOLERANCE)
        local_max = magnitude[window].max()
        if local_max >= 0.5 * global_max:
            messages.append(f"    {GREEN}[ok]{RESET} bright spot found at target "
                            f"({sx:+.1f}, {sy:+.1f})")
        else:
            passed = False
            messages.append(f"    {RED}[X ]{RESET} NO bright spot at target ({sx:+.1f}, {sy:+.1f}) "
                            f"(brightness there is only {100 * local_max / global_max:.0f}% of max)")

    # Check 2: the brightest pixel of the whole image should be AT one of the targets
    peak_jj, peak_ii = np.unravel_index(np.argmax(magnitude), magnitude.shape)
    peak_xy = np.array([x_vec[peak_ii], y_vec[peak_jj]])
    dist_to_targets = np.linalg.norm(np.array(scatterer_pos)[:, :2] - peak_xy, axis=1)
    if dist_to_targets.min() <= POSITION_TOLERANCE:
        messages.append(f"    {GREEN}[ok]{RESET} brightest pixel "
                        f"({peak_xy[0]:+.2f}, {peak_xy[1]:+.2f}) is on a target")
    else:
        passed = False
        messages.append(f"    {RED}[X ]{RESET} brightest pixel is at "
                        f"({peak_xy[0]:+.2f}, {peak_xy[1]:+.2f}), which is "
                        f"{dist_to_targets.min():.2f} m from the nearest target")
        messages.append("         HINTS: image is indexed [jj, ii] = [Y, X] -- did you swap them? "
                        "Did you mix up pixel and platform coordinates in the distance formula?")

    return passed, messages


def run_check(name, func, sim_data, x_vec, y_vec, scatterer_pos, plot):
    """Run one backprojection approach and check its output. Returns 'pass'/'fail'/'todo'."""
    print(f"\n--- Checking '{name}' approach " + "-" * (40 - len(name)))
    if name == "fourier":
        print("    (heads up: this one takes about a minute)")
    try:
        start = time.time()
        sar_image_complex = func()
        elapsed = time.time() - start
    except NotImplementedError:
        print(f"    {YELLOW}NOT IMPLEMENTED YET{RESET} -- skipping. "
              "(Delete the NotImplementedError line once you write it.)")
        return "todo"
    except Exception as err:
        print(f"    {RED}CRASHED{RESET} with {type(err).__name__}: {err}")
        return "fail"

    passed, messages = check_image(sar_image_complex, x_vec, y_vec, scatterer_pos)
    for msg in messages:
        print(msg)
    verdict = f"{GREEN}PASSED{RESET}" if passed else f"{RED}FAILED{RESET}"
    print(f"    -> {name}: {verdict}  ({elapsed:.2f} s)")

    if plot:
        import matplotlib.pyplot as plt
        plt.figure()
        plt.imshow(20 * np.log10(np.abs(sar_image_complex) + 1e-12), origin='lower', cmap='gray',
                   extent=(x_vec[0], x_vec[-1], y_vec[0], y_vec[-1]))
        plt.scatter([s[0] for s in scatterer_pos], [s[1] for s in scatterer_pos],
                    facecolors='none', edgecolors='r', s=200, label='true targets')
        plt.title(f"'{name}' approach (dB)")
        plt.xlabel("X (m)")
        plt.ylabel("Y (m)")
        plt.legend()

    return "pass" if passed else "fail"


def main():
    parser = argparse.ArgumentParser(description="Self-check for backprojection implementations.")
    parser.add_argument('approach', nargs='?', choices=('shift', 'interp', 'fourier'),
                        help="Check only this approach; defaults to checking all three.")
    parser.add_argument('--plot', action='store_true', help="Display the resulting SAR images.")
    args = parser.parse_args()

    print("Simulating radar data for 5 point targets (this is given, working code)...")
    sim_params = read_sim_params(PARAMS_FILE)
    sim_data = simulate_data(sim_params, show_progress_bar=False)
    scatterer_pos = sim_params['scatterer_pos']

    x_vec = np.arange(GRID_MIN, GRID_MAX + GRID_RES, GRID_RES)
    y_vec = np.arange(GRID_MIN, GRID_MAX + GRID_RES, GRID_RES)
    common = (sim_data['scan_data'], sim_data['range_bins'], sim_data['platform_pos'],
              x_vec, y_vec)

    approaches = {
        'shift': lambda: bp.shift_approach(*common),
        'interp': lambda: bp.interp_approach(*common),
        'fourier': lambda: bp.fourier_approach(sim_params['center_freq'], *common),
    }
    selected = [args.approach] if args.approach else list(approaches)

    results = {name: run_check(name, approaches[name], sim_data, x_vec, y_vec,
                               scatterer_pos, args.plot)
               for name in selected}

    print("\n" + "=" * 60)
    print("SUMMARY")
    labels = {"pass": f"{GREEN}PASSED{RESET}", "fail": f"{RED}FAILED{RESET}",
              "todo": f"{YELLOW}not implemented yet{RESET}"}
    for name, result in results.items():
        note = "  (optional)" if name == 'fourier' else ""
        print(f"    {name:<8s} {labels[result]}{note}")
    print("=" * 60)

    if args.plot:
        import matplotlib.pyplot as plt
        plt.show()

    # Exit code ignores the optional fourier part unless it was explicitly requested
    required = [r for n, r in results.items() if n != 'fourier' or args.approach == 'fourier']
    sys.exit(0 if all(r != "fail" for r in required) else 1)


if __name__ == "__main__":
    main()
