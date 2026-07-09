# 1. The Backprojection Assignment

Open `backprojection/backprojection.py`. Three functions are yours to write, in order:

| Part | Function | Required? | What it teaches |
|------|--------------------|-----------|-----------------|
| 1 | `shift_approach` | **YES** | What SAR imaging *is* (nested loops) |
| 2 | `interp_approach` | **YES** | Vectorization — same math, ~100x faster |
| 2b | `interp_single_scan` | **YES** | Porting your code to a multiprocess worker |
| 3 | `fourier_approach` | Optional | Sub-bin alignment via the FFT shift theorem |

Every TODO block has numbered step-by-step hints. Everything else in the file
(argument parsing, data loading, plotting) is complete — don't modify it.

## Workflow for each part

1. Read the TODO block's "BIG IDEA" and steps.
2. Write your code where the block indicates.
3. Delete the `raise NotImplementedError(...)` line.
4. Check it:

```bash
cd backprojection
python check_backprojection.py shift     # after Part 1
python check_backprojection.py interp    # after Part 2
python check_backprojection.py fourier   # after Part 3 (optional)
python check_backprojection.py           # all of them
python check_backprojection.py --plot    # also SHOW your SAR images
```

**What the checker does:** simulates radar data for 5 point targets at known positions
(an "X" pattern), runs YOUR code on it, and verifies bright spots appear at — and only
at — the true target locations.

**What passing looks like:**

```
--- Checking 'shift' approach ------------------------------
    [ok] bright spot found at target (-5.0, -5.0)
    ...
    [ok] brightest pixel (+5.00, +5.00) is on a target
    -> shift: PASSED  (2.31 s)
```

Note the time. After Part 2 passes, compare its time to Part 1's. That difference is
why Part 2 exists.

## Part 3 (fourier) notes

- Attempt it only after Parts 1 and 2 pass.
- Its checker run takes about a minute — that's normal.
- If it defeats you, that's expected: we'll build it together in a code-along session.
  Come with your attempt and your questions.

## Running backprojection directly (what the checker wraps)

```bash
python backprojection.py <data.pkl> <x_min> <x_max> <x_res> <y_min> <y_max> <y_res> [options]
```

| Argument / flag | Meaning |
|---|---|
| `data.pkl` | Pickled dict with `scan_data`, `platform_pos`, `range_bins` |
| `x_min x_max x_res` | Image X extent and pixel size (meters) |
| `y_min y_max y_res` | Image Y extent and pixel size (meters) |
| `-m {shift,interp,fourier}` | Which of YOUR implementations to use (default: interp) |
| `-np N` | Number of processes (interp only; exercises your Part 2b) |
| `-z Z` | Height of the image plane in meters (default 0) |
| `-fc HZ` | Radar center frequency — **required for `-m fourier`** |
| `-s FILE.pkl` | Save the resulting SAR image |
| `-p` | Show a progress bar |
| `-nv` | Don't display the image window |

Example:

```bash
python backprojection.py sim_data.pkl -8 8 0.1 -8 8 0.1 -m shift -p
```

The image window has **Min/Max sliders** — drag them to adjust brightness contrast.
A "blank" image is often just a bad contrast range, not a broken algorithm.
