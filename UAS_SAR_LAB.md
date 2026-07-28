# UAS-SAR Lab: From Raw Data to a Readable Image

In this lab you'll learn the full Synthetic Aperture Radar workflow in two parts:

- **Part 1 — Run the pipeline.** Take a raw radar recording and its motion-capture
  track, align them (using the interactive sliders), and form a SAR image. This is
  the mechanics: how raw data becomes an image.
- **Part 2 — Make it readable.** A raw SAR image is technically correct but visually
  useless. You'll take clean pre-processed scenes and learn to **tune the display
  parameters** until a hidden target — a smiley face, and the letters "BW" — appears.

By the end you'll be able to run the whole chain yourself and know *which parameter to
change, and why,* to pull a target out of the noise.

## Contents

- [Setup](#setup)
- **Part 1 — Running the pipeline**
  - [1.1 Unpack the radar](#11-unpack-the-radar)
  - [1.2 Preprocess + the Start-Bin slider](#12-preprocess--the-start-bin-slider)
  - [1.3 Calibrate + the Velocity-Threshold GUI](#13-calibrate--the-velocity-threshold-gui)
  - [1.4 Backprojection](#14-backprojection)
- **Part 2 — Tuning the display**
  - [2.1 The two practice scenes](#21-the-two-practice-scenes)
  - [2.2 The parameters, and what each one does](#22-the-parameters-and-what-each-one-does)
  - [2.3 Recommended recipes](#23-recommended-recipes)
- [Command reference](#command-reference)
- [Troubleshooting](#troubleshooting)

---

## Setup

> [!IMPORTANT]
> Use **one Python environment for the whole lab.** Files are passed between stages as
> `.pkl`, and a pickle written under numpy 2.x can't be read under numpy 1.x
> (`ModuleNotFoundError: No module named 'numpy._core'`). Activate the project
> environment and confirm numpy 2.x:

```bash
source ~/Downloads/bruh-main/venv/bin/activate
which python
python -c "import numpy; print(numpy.__version__)"   # want 2.x
```

If `which python` shows an Anaconda path, run `conda deactivate`, then re-source.

<details>
<summary><b>First-time package install</b></summary>

```bash
cd mocap/
pip install -r pip_requirements.txt
pip install imageio scikit-image
```

</details>

> [!TIP]
> Don't paste multi-line commands out of a PDF — wrapping breaks them silently. Copy
> from this file. The `\` at line-ends are real continuations; keep them, with nothing
> after the backslash.

---

# Part 1 — Running the pipeline

You'll run this on **`orangeworks_mit_data7`** (raw radar) paired with
**`orangeworks_walktest1`** (motion capture). These were recorded together during a
flight over a corner-reflector scene.

## 1.1 Unpack the radar

The `.prd` is a raw binary log. Turn it into an array:

```bash
cd pulson440/
python unpack.py ../mit_final_data/orangeworks_mit_data7.prd -v --keep_clutter
mv orangeworks_mit_data7.pkl ../mit_final_data/
```

> [!TIP]
> Press <kbd>Enter</kbd> at the `Press [enter] to continue` prompt **before** closing
> any preview window. Closing first throws a harmless `_tkinter.TclError` at exit; the
> files are written fine.

## 1.2 Preprocess + the Start-Bin slider

```bash
cd ../mocap/
python data_processor.py \
    ../mit_final_data/orangeworks_mit_data7.pkl \
    ../mit_final_data/orangeworks_walktest1.csv \
    --platform-name "Radar" \
    --corner-right-name "Corner_Refl_2" \
    --corner-left-name "Corner_Refl_1" \
    --save-plots --save-data
```

> [!NOTE]
> The `--platform-name` / `--corner-*` values must match the **rigid-body names in the
> CSV**. Here they're `Radar`, `Corner_Refl_1`, `Corner_Refl_2`. To check any CSV:
> ```bash
> sed -n '4p' yourfile.csv | tr ',' '\n' | grep -v '^$' | sort -u
> ```

**The prompts:**

1. `Do you want to swap the coordinate order to (z, x, y)?` → **`y`**
2. Two figures — **X/Y/Z vs Time** and **3D Trajectory**. Sanity check, not errors: the
   platform should sweep ~5 m along one axis while the others stay flat, and the 3D
   view should be a straight track. Close both.
3. `Do you want to proceed with radar data processing?` → **`y`**
4. The **Start-Bin slider** opens.

### Using the Start-Bin slider

The plot is a **Range-Time Intensity (RTI)** heatmap — radar range across, time down —
with two colored curves showing where the mocap says each reflector should be.

**Your job:** slide **Start Bin** until the two curves lie *on top of* the bright
streaks in the heatmap. The curves are the prediction; the heatmap is what the radar
actually saw. Line them up, then press **Confirm**.

- Doesn't need to be perfect — the next stage does fine alignment. Just get the curves
  onto the bright features.
- If they drift off, back the slider off until they sit back on.

## 1.3 Calibrate + the Velocity-Threshold GUI

```bash
python calibration_auto.py \
    ../mit_final_data/orangeworks_mit_data7.pkl \
    orangeworks_walktest1.pkl \
    --sigma 0.3 --save-data
```

> [!IMPORTANT]
> `--save-data` is **required.** Without it the script runs the whole session and exits
> without writing `run_0.pkl`.

**The prompts:**

1. `Which reflector to use for alignment? (1 or 2):` → **`1`**
2. A **2D MoCap Template** figure — close it.
3. A few minutes of computation. **Looks frozen. Let it run.**
4. The **Velocity-Threshold GUI** opens (below).
5. A **Calibration Verification** RTI — both reflector curves should sit on real
   returns. That confirms alignment worked. Close it.

Output: `run_0.pkl` in `backprojection/`.

### Using the Velocity-Threshold GUI

This picks the frames where the platform was moving — the synthetic aperture. The plot
is **ΔX velocity vs frame**: red dashed threshold lines, orange Start/End markers.

**Read the title bar** — `Start: N, End: N`. `-1` means *not found*. You want both to
be real frame numbers.

1. The trace is flat (still), then a wide band (moving), then flat (stopped). Start
   should sit at the ramp-up, End at the settle-down.
2. **If both are already real numbers at the defaults** — just **Confirm**.
3. **If End shows `-1`** — drag **Window Size** up to ~40, and nudge **Velocity
   Threshold** up if needed, until End becomes a real frame.

> [!WARNING]
> Never confirm with **Start: -1** — it crashes the next stage. A `-1` **End** is fine.

## 1.4 Backprojection

Form the image:

```bash
cd ../backprojection/
python backprojection.py run_0.pkl -2.5 2.5 0.01 -1.5 2.7 0.01 -p -s sar_img.pkl
```

The six numbers are `x_min x_max x_res y_min y_max y_res` in metres — the image grid.
`-s sar_img.pkl` saves the result.

You now have a SAR image. **It will look washed out or noisy** — that's normal and
expected. Making it *readable* is Part 2.

> [!TIP]
> This is your own image, start to finish. It's rougher than the polished scenes in
> Part 2 (shorter flight, fewer pulses), but you built it from raw data yourself.

---

# Part 2 — Tuning the display

A raw SAR image packs a huge brightness range into a picture where everything looks
the same. The scene *is* in the data — you just have to set the display so a human eye
can see it. This part teaches the parameters, one at a time, using two scenes that have
clear targets hidden in them.

## 2.1 The two practice scenes

These are **pre-processed** collections — already unpacked, aligned, and calibrated,
so you skip straight to backprojection and focus on the display. (Their raw recordings
aren't part of this lab; you practiced the pipeline in Part 1.)

| File | Hidden target |
|---|---|
| `run_0_mit_example_test.pkl` | a **smiley face** (easier — start here) |
| `run_0_GOOD_ONE.pkl` | the letters **"BW"** |

Backproject one just like in Part 1:

```bash
python backprojection.py run_0_mit_example_test.pkl -2.5 2.5 0.01 -1.5 2.7 0.01 -p -s smiley_img.pkl
```

At the default display it won't look like much. Now you'll tune it.

To re-display a saved image with your own settings, run a short Python snippet. Here's
the template — you'll change the marked values and re-run it:

```python
import pickle, numpy as np, matplotlib.pyplot as plt

d = pickle.load(open('smiley_img.pkl', 'rb'))       # <- your saved image
m = np.abs(d['sar_image_complex'])
x, y = d['x_vec'], d['y_vec']

db = 20*np.log10(m + 1)                              # dB scaling (see 2.2)

plt.figure(figsize=(11, 9))
plt.imshow(db, origin='lower',
           cmap='turbo',                             # <- COLORMAP (2.2)
           extent=[x[0], x[-1], y[0], y[-1]],
           vmin=np.percentile(db, 80),               # <- VMIN (2.2)
           vmax=np.percentile(db, 99.7))             # <- VMAX (2.2)
plt.colorbar(label='dB')
plt.xlabel('X (m)'); plt.ylabel('Y (m)')
plt.show()
```

Save it as `show.py`, change a value, run `python show.py`, look, repeat.

## 2.2 The parameters, and what each one does

### dB scaling — always do this first

**What:** `db = 20*np.log10(m + 1)` converts raw magnitude to decibels.

**Why:** raw SAR magnitude spans ~7 orders of magnitude. One bright scatterer would
saturate the whole image and everything else would be black. dB compresses that range
so weak and strong returns are both visible. **Always display in dB, never raw
magnitude.**

### vmin / vmax — contrast (the biggest lever)

**What:** the brightness floor and ceiling. Anything below `vmin` shows as the darkest
color; anything above `vmax` as the brightest. Setting them by *percentile* adapts to
each image automatically.

**Why:** this is what pulls a target out of the background.

- **Raise `vmin`** (e.g. `80` → `85` → `90` percentile) to **darken the background** so
  only the strong scatterers — the target — remain visible. This is usually the single
  most effective change.
- **Lower `vmax`** slightly (e.g. `99.7` → `99`) to brighten mid-level features if the
  image is too dark.

**Try:** start at `vmin=80`, and step it up. Watch the smiley/letters emerge as the
clutter fades. Too high and you erase real signal; too low and it's a muddy wash.

### colormap — how intensities map to color

**What:** the `cmap` value. Different maps make structure easier or harder to see.

**Why:** `viridis` (the default green) maps everything to similar-looking greens, so a
target blends in. Maps with more color separation make bright targets *pop*.

| `cmap` | Look | Use it when |
|---|---|---|
| `turbo` | blue→green→red rainbow | **best for finding a target** — strong returns go red/yellow, background stays blue |
| `hot` | black→red→yellow→white | clean look, target bright on dark |
| `inferno` | dark→orange→yellow | like hot, softer |
| `gray` | grayscale | classic SAR look, good for reports |
| `viridis` | green field | matches some reference images |

**Try:** switch `cmap='viridis'` to `cmap='turbo'` and the difference is immediate.

### Cropping / zooming — frame the target

**What:** change the backprojection **bounds** (`x_min x_max y_min y_max`) to image a
smaller region, or change the plot's axis limits to zoom in.

**Why:** if the target sits in one part of the scene, imaging the whole area wastes
resolution and includes distracting clutter. Tightening the bounds around the target
gives a bigger, cleaner picture of it.

- To image a tighter region, change the backprojection command's bounds, e.g.
  `-1.5 1.5 0.01 0 2 0.01` instead of `-2.5 2.5 0.01 -1.5 2.7 0.01`.
- Smaller `x_res`/`y_res` (e.g. `0.005`) = finer pixels = sharper but slower.

> [!NOTE]
> **Advanced (optional):** if one very bright corner reflector dominates the color
> scale and hides everything else, you can dim it before display by scaling down its
> pixels — e.g. multiply the values in that corner by 0.15. This is a trick, not a
> required step; only reach for it if a single blob is washing out the rest.

## 2.3 Recommended recipes

Starting points that reveal each target. Tune from here.

**Smiley** (`run_0_mit_example_test.pkl`):
```
bounds:  -2.5 2.5 0.01 -1.5 2.7 0.01
cmap:    turbo
vmin:    80th percentile
vmax:    99.7th percentile
```

**BW** (`run_0_GOOD_ONE.pkl`):
```
bounds:  -2.5 2.5 0.01 -1.5 2.7 0.01
cmap:    turbo
vmin:    85th percentile   (push to 90 for less clutter)
vmax:    99.7th percentile
```

Compare against `ref_smiley.png` and `ref_BW.png` (included). Note the targets are
**constellations of bright scatterers** — each corner-reflector can is one dot, and you
read the face/letters by connecting them. They won't be painted-on crisp; that's the
nature of SAR at this resolution.

---

## Command reference

```bash
# 0. environment (numpy 2.x)
source ~/Downloads/bruh-main/venv/bin/activate

# --- PART 1: run the pipeline on data7 + walktest ---
cd ~/2025_UAS_SAR/pulson440/
python unpack.py ../mit_final_data/orangeworks_mit_data7.prd -v --keep_clutter
mv orangeworks_mit_data7.pkl ../mit_final_data/

cd ../mocap/
python data_processor.py \
    ../mit_final_data/orangeworks_mit_data7.pkl \
    ../mit_final_data/orangeworks_walktest1.csv \
    --platform-name "Radar" \
    --corner-right-name "Corner_Refl_2" \
    --corner-left-name "Corner_Refl_1" \
    --save-plots --save-data

python calibration_auto.py \
    ../mit_final_data/orangeworks_mit_data7.pkl \
    orangeworks_walktest1.pkl \
    --sigma 0.3 --save-data

cd ../backprojection/
python backprojection.py run_0.pkl -2.5 2.5 0.01 -1.5 2.7 0.01 -p -s sar_img.pkl

# --- PART 2: tune the display on the ready-made scenes ---
python backprojection.py run_0_mit_example_test.pkl -2.5 2.5 0.01 -1.5 2.7 0.01 -p -s smiley_img.pkl
python backprojection.py run_0_GOOD_ONE.pkl        -2.5 2.5 0.01 -1.5 2.7 0.01 -p -s bw_img.pkl
# then edit show.py (cmap / vmin / vmax) and run: python show.py
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `platform-name: command not found` | Command broke across lines | One line, or `\` continuations |
| `Unknown option --save-data` | Same line-break issue | Same |
| `ModuleNotFoundError: numpy._core` | Mixed numpy versions between stages | Use one env; activate the venv |
| `ModuleNotFoundError: imageio` / `skimage` | Missing packages | `pip install imageio scikit-image` |
| Start-Bin curves float off the heatmap | Slider not aligned | Slide until curves sit on bright features |
| Velocity GUI: `End: -1` | Motion runs to the end | Window Size → 40; or accept (–1 End is OK) |
| `IndexError: index 0 is out of bounds` | Confirmed with `Start: -1` | Adjust sliders until Start is real |
| Image all one color / washed out | Display range wrong | Set `vmin`/`vmax` by percentile (2.2) |
| Target invisible in green field | `viridis`, low contrast | `cmap='turbo'`, raise `vmin` to 85–90 |

**Harmless warnings:** `_tkinter.TclError: can't invoke "destroy"` (window closed
during shutdown), `RuntimeWarning: divide by zero in log10` (zeros → −inf in dB,
handled), `UserWarning: Pandas requires ... numexpr` (old optional deps).
