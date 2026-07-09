# 5. Real Data Pipeline — Flight Data to SAR Image

You have: a raw radar file (e.g. `collect_4.prd`) and a motion-capture CSV
(e.g. `mocap_data_004.csv`). Four steps turn them into a SAR image.

Suggested layout: put both raw files in a data folder (e.g. `mit_data/`) at the repo root.

## Step 1 — Unpack the raw radar file

```bash
cd pulson440
python unpack.py ../mit_data/collect_4.prd -v --keep_clutter
```

| Flag | Meaning |
|---|---|
| `-v` | Visualize: also produce a `.png` RTI plot and `.gif` |
| `--keep_clutter` | Keep stationary background returns (needed for alignment later) |
| `--num_pulses_per_cpi N` | Advanced: pulse integration (leave default) |
| `-d` | Delete the raw file after unpacking (don't) |

**Produces:** `collect_4.pkl`, `collect_4.png`, `collect_4.gif` in `pulson440/`.
Look at the `.png` — you should see moving streaks. Then move `collect_4.pkl` into
`mit_data/`.

## Step 2 — Preprocess radar + motion capture

```bash
cd ../mocap
python data_processor.py ../mit_data/collect_4.pkl ../mit_data/mocap_data_004.csv \
    --platform-name Radar --corner-right-name Corner_R --corner-left-name Corner_L \
    --save-plots --save-data
```

| Flag | Meaning |
|---|---|
| `--platform-name` | Radar/drone's column name in the mocap CSV (**required**) |
| `--corner-right-name`, `--corner-left-name` | Reflector column names in the CSV (**required**) |
| `--start-bin N` | Cut radar data before this range bin (default 0) |
| `--save-plots` / `--save-data` | Write PNGs / the processed `.pkl` |
| `--radar-output-name`, `--mocap-output-name` | Custom output filenames |
| `--skip-check` | Skip the confirm gate (leave off) |

**Interactive prompts, in order:**

1. `Do you want to swap the coordinate order to (z, x, y)?` → type **`y`**
   (the mocap system and radar use different axis conventions). Plots of the radar and
   reflector positions appear — sanity-check they look like your room setup.
2. `Do you want to proceed with radar data processing? (y/n):` → type **`y`**.
3. An RTI image appears with an interactive **Start Bin** slider: drag until the
   red/orange curves (predicted reflector distance — computed by YOUR
   `distance_to_object`!) lie on top of the bright streaks in the image. Press
   **Confirm**.

**Produces:** `mocap_data_004.pkl` in `mocap/` — move it to `mit_data/`.

## Step 3 — Time-align radar and mocap

```bash
python calibration_auto.py ../mit_data/collect_4.pkl ../mit_data/mocap_data_004.pkl --sigma 0.3
```

| Flag | Meaning |
|---|---|
| `--sigma S` | Gaussian width for the alignment template (default 0.5; 0.3 worked well last year) |
| `--velocity-threshold V` | Movement-detection threshold (default 0.0005) |
| `--window-size N` | Sustained-movement window (default 14) |
| `--output-name NAME` | Output filename (default `run_0`) |
| `--save-plots` / `--save-data` | Write PNGs / output pickle |
| `--skip-interactive` | Skip the threshold GUI (leave off) |

**Interactive prompts, in order:**

1. `Which reflector to use for alignment? (1 or 2):` → **1** = left reflector,
   **2** = right.
2. An alignment plot appears — close it, then **wait**: the program spends a few
   minutes computing (do not kill it).
3. A GUI with a **velocity threshold** slider appears: pick a threshold that cleanly
   separates "moving" from "still", press **Confirm**.

**Produces:** `run_0.pkl` in `backprojection/`.

If automatic alignment gives garbage, `calibration_manual.py` takes the same arguments
and lets you set the alignment by hand.

## Step 4 — Backprojection (YOUR algorithm's big moment)

```bash
cd ../backprojection
python backprojection.py run_0.pkl -1.7 1.5 0.01 -1.2 2.7 0.01 -m interp -p
```

Those six numbers are the image frame in meters (x_min x_max x_res y_min y_max y_res) —
start with a frame around where your targets were and tune. Use the Min/Max sliders on
the image window to bring out the scene. `-m interp` (or `-m interp -np 4`) is strongly
recommended — real collects have thousands of scans and `-m shift` will take ages
(now you know why Part 2 exists).

Save your result for submission:

```bash
python backprojection.py run_0.pkl -1.7 1.5 0.01 -1.2 2.7 0.01 -m interp -p -s team3_final.pkl
```
