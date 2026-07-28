# UAS-SAR Lab: From Raw Data to a Readable Image

This lab has two parts:

- **Part 1 — Run the pipeline.** Take a raw radar recording and its motion-capture
  track, align them with the interactive sliders, and form a SAR image. This is the
  mechanics: how raw data becomes an image.
- **Part 2 — Make it readable.** A raw SAR image is technically correct but visually
  useless. You'll take pre-processed scenes and tune the **display parameters** until a
  hidden target — a smiley face, and the letters **"BW"** — appears.

By the end you'll run the whole chain yourself and know *which parameter to change, and
why,* to pull a target out of the noise.

## Contents

- [Setup](#setup)
- [Getting the data files](#getting-the-data-files)
- **Part 1 — Running the pipeline**
  - [1.1 Unpack the radar](#11-unpack-the-radar)
  - [1.2 Preprocess + the Start-Bin slider](#12-preprocess--the-start-bin-slider)
  - [1.3 Calibrate + the Velocity-Threshold GUI](#13-calibrate--the-velocity-threshold-gui)
  - [1.4 Backprojection](#14-backprojection)
- **Part 2 — Tuning the display**
  - [2.1 The two practice scenes](#21-the-two-practice-scenes)
  - [2.2 The parameters, and what each does](#22-the-parameters-and-what-each-does)
  - [2.3 Recommended recipes](#23-recommended-recipes)
- [Command reference](#command-reference)
- [Troubleshooting](#troubleshooting)

---

## Setup

All commands are run **from your repo root** (the folder with `pulson440/`, `mocap/`,
`backprojection/` in it). Paths are written relative to there.

**Make a virtual environment and install the requirements** (once):

```bash
python -m venv sar_venv

# activate it:
source sar_venv/bin/activate        # macOS / Linux
# sar_venv\Scripts\activate           # Windows (PowerShell)

pip install -r pip_requirements.txt
pip install imageio scikit-image
```

> [!IMPORTANT]
> Use this **same environment for every step.** The pipeline passes `.pkl` files
> between stages; mixing Python/numpy versions causes
> `ModuleNotFoundError: No module named 'numpy._core'`. If you open a new terminal,
> re-activate the venv first.

Confirm you're set up:

```bash
python -c "import numpy; print(numpy.__version__)"
```

> [!TIP]
> Don't paste multi-line commands out of a PDF — line-wrapping breaks them silently.
> Copy from this file. The `\` at line-ends are real continuations; keep them, with
> nothing after the backslash.

---

## Getting the data files

Download all four files from the shared Drive folder:

**https://drive.google.com/drive/folders/1Cpt36vHLuSOBXd7muWbPHfcXgfFuhJ7Q**

Make a folder called `mit_final_data/` at your repo root and put all four in it:

| File | Used in | What it is |
|---|---|---|
| `orangeworks_mit_data7.prd` | Part 1 | Raw radar recording |
| `orangeworks_walktest1.csv` | Part 1 | Matching motion-capture track |
| `run_0_mit_example_test.pkl` | Part 2 | The **smiley** scene (pre-processed) |
| `run_0_GOOD_ONE.pkl` | Part 2 | The **BW** scene (pre-processed) |

```bash
mkdir -p mit_final_data
# move the four downloaded files into mit_final_data/
```

---

# Part 1 — Running the pipeline

You'll run this on **`orangeworks_mit_data7`** (raw radar) paired with
**`orangeworks_walktest1`** (motion capture) — recorded together during a flight over a
corner-reflector scene.

## 1.1 Unpack the radar

The `.prd` is a raw binary log. Turn it into an array:

```bash
cd pulson440
python unpack.py ../mit_final_data/orangeworks_mit_data7.prd -v --keep_clutter
mv orangeworks_mit_data7.pkl ../mit_final_data/
```

**Produces** `orangeworks_mit_data7.pkl` (+ a `.png`/`.gif` preview). Look at the
`.png` — you should see moving streaks. Move the `.pkl` into `mit_final_data/`.

> [!TIP]
> Press <kbd>Enter</kbd> at the `Press [enter] to continue` prompt **before** closing
> any preview window. Closing first throws a harmless `_tkinter.TclError` at exit; the
> files are written fine.

## 1.2 Preprocess + the Start-Bin slider

```bash
cd ../mocap
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
> CSV**. For this collection they're `Radar`, `Corner_Refl_1`, `Corner_Refl_2`.

**The prompts:**

1. `Do you want to swap the coordinate order to (z, x, y)?` -> **`y`**
   (the mocap and radar use different axis conventions).
2. Two figures — **X/Y/Z vs Time** and **3D Trajectory**. Sanity check, not errors: the
   platform should sweep ~5 m along one axis while the other two stay flat, and the 3D
   view should be a straight track with the reflectors as fixed dots. Close both.
3. `Do you want to proceed with radar data processing?` -> **`y`**
4. The **Start-Bin slider** opens.

### Using the Start-Bin slider

The plot is a **Range-Time Intensity (RTI)** heatmap — radar range across, time down —
with two colored curves showing where the mocap says each reflector should be.

**Your job:** slide **Start Bin** until the two curves lie *on top of* the bright
streaks in the heatmap. The curves are the prediction; the heatmap is what the radar
actually saw. Line them up, then press **Confirm**.

- It doesn't need to be perfect — the next stage does fine alignment. Just get the
  curves onto the bright features.
- If they drift off, back the slider off until they sit back on.

**Produces** `orangeworks_walktest1.pkl` in `mocap/`. Leave it there — the next step
reads it locally.

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

1. `Which reflector to use for alignment? (1 or 2):` -> **`1`** (left) or **`2`** (right).
2. A **2D MoCap Template** figure — close it.
3. A few minutes of computation. **It looks frozen. Let it run.**
4. The **Velocity-Threshold GUI** opens (below).
5. A **Calibration Verification** RTI — both reflector curves should sit on real
   returns (bright features, not empty noise). That confirms alignment worked. Close it.

**Produces** `run_0.pkl` in `backprojection/`.

> [!NOTE]
> If automatic alignment gives garbage, `calibration_manual.py` takes the same
> arguments and lets you set the alignment by hand.

### Using the Velocity-Threshold GUI

This picks the frames where the platform was moving — the synthetic aperture. The plot
is **delta-X velocity vs frame**: red dashed threshold lines, orange Start/End markers.

**Read the title bar** — `Start: N, End: N`. `-1` means *not found*. You want both to be
real frame numbers.

1. The trace is flat (still), then a wide band (moving), then flat (stopped). Start
   should sit at the ramp-up, End at the settle-down.
2. **If both are already real numbers at the defaults** — just **Confirm**.
3. **If End shows `-1`** (motion runs to the end of the recording) — drag **Window
   Size** up to ~40, and nudge **Velocity Threshold** up if needed, until End becomes a
   real frame.

| Slider | What it does | Typical |
|---|---|---|
| **Velocity Threshold** | Height of the red lines = "is it moving?" cutoff | ~0.0005 |
| **Window Size** | Smooths jitter so sustained motion stands out | 14-40 |

> [!WARNING]
> Never confirm with **Start: -1** — it crashes the next step
> (`IndexError: index 0 is out of bounds`). A `-1` **End** is fine (it means "run to the
> last frame").

## 1.4 Backprojection

Form the image:

```bash
cd ../backprojection
python backprojection.py run_0.pkl -2.5 2.5 0.01 -1.5 2.7 0.01 -m interp -p -s sar_img.pkl
```

The six numbers are `x_min x_max x_res y_min y_max y_res` in metres — the image grid.
`-m interp` is strongly recommended (real collects have thousands of scans; `-m shift`
takes forever). `-s sar_img.pkl` saves the result.

You now have a SAR image — but **it will look washed out or noisy.** That's normal.
Making it readable is Part 2.

> [!TIP]
> This is your own image, start to finish. It's rougher than the polished scenes in
> Part 2 (shorter flight, fewer pulses), but you built it from raw data yourself.

---

# Part 2 — Tuning the display

A raw SAR image packs a huge brightness range into a picture where everything looks the
same. The scene *is* in the data — you just have to set the display so a human eye can
see it. This part teaches the parameters using two scenes with clear hidden targets.

## 2.1 The two practice scenes

These are **pre-processed** collections — already unpacked, aligned, and calibrated — so
you skip straight to backprojection and focus on the display. (You practiced the full
pipeline in Part 1.)

| File | Hidden target |
|---|---|
| `run_0_mit_example_test.pkl` | a **smiley face** (easier — start here) |
| `run_0_GOOD_ONE.pkl` | the letters **"BW"** |

Copy them where backprojection can reach them, then image one:

```bash
cp ../mit_final_data/run_0_mit_example_test.pkl .
python backprojection.py run_0_mit_example_test.pkl -2.5 2.5 0.01 -1.5 2.7 0.01 -m interp -p -s smiley_img.pkl
```

At the default display it won't look like much. Now you'll tune it.

To re-display a saved image with your own settings, use a short Python snippet. Save
this as `show.py`, change the marked values, and re-run it:

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

```bash
python show.py
```

Change a value, run again, look. That loop is the whole skill.

## 2.2 The parameters, and what each does

### dB scaling — always do this first

**What:** `db = 20*np.log10(m + 1)` converts raw magnitude to decibels.

**Why:** raw SAR magnitude spans ~7 orders of magnitude. One bright scatterer would
saturate the whole image and everything else would be black. dB compresses that range so
weak and strong returns are both visible. **Always display in dB, never raw magnitude.**

### vmin / vmax — contrast (the biggest lever)

**What:** the brightness floor and ceiling. Anything below `vmin` shows as the darkest
color; anything above `vmax` as the brightest. Setting them by *percentile* adapts to
each image automatically.

**Why:** this is what pulls a target out of the background.

- **Raise `vmin`** (e.g. `80` -> `85` -> `90` percentile) to **darken the background** so
  only the strongest scatterers — the target — remain. Usually the single most
  effective change.
- **Lower `vmax`** slightly (e.g. `99.7` -> `99`) to brighten mid-level features if the
  image is too dark.

**Try:** start at `vmin=80`, step it up, and watch the target emerge as the clutter
fades. Too high erases real signal; too low is a muddy wash.

### colormap — how intensities map to color

**What:** the `cmap` value.

**Why:** `viridis` (default green) maps everything to similar greens, so a target blends
in. Maps with more color separation make bright targets *pop*.

| `cmap` | Look | Use it when |
|---|---|---|
| `turbo` | blue-green-red rainbow | **best for finding a target** — strong returns go red/yellow, background stays blue |
| `hot` | black-red-yellow-white | clean, target bright on dark |
| `inferno` | dark-orange-yellow | like hot, softer |
| `gray` | grayscale | classic SAR look, good for reports |
| `viridis` | green field | matches some reference images |

**Try:** switch `cmap='viridis'` to `cmap='turbo'` — the difference is immediate.

### Cropping / zooming — frame the target

**What:** change the backprojection **bounds** (`x_min x_max y_min y_max`) to image a
smaller region, or change the plot's axis limits.

**Why:** if the target sits in one part of the scene, imaging the whole area wastes
resolution and includes distracting clutter. Tightening the bounds around the target
gives a bigger, cleaner picture.

- To image a tighter region, change the backprojection command's bounds, e.g.
  `-1.5 1.5 0.01 0 2 0.01`.
- Smaller `x_res`/`y_res` (e.g. `0.005`) = finer pixels = sharper but slower.

> [!NOTE]
> **Advanced (optional):** if one very bright corner reflector hogs the color scale and
> hides everything else, you can dim it before display by scaling down its pixels
> (multiply that corner's values by ~0.15). A trick, not a required step — only reach
> for it if a single blob is washing out the rest.

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

Compare against `ref_smiley.png` and `ref_BW.png`. The targets are **constellations of
bright scatterers** — each corner-reflector can is one dot, and you read the face/letters
by connecting them. They won't be painted-on crisp; that's the nature of SAR at this
resolution. Once you've traced it once, you'll see it instantly every time after.

---

## Command reference

```bash
# --- SETUP (once) ---
python -m venv sar_venv
source sar_venv/bin/activate            # Windows: sar_venv\Scripts\activate
pip install -r pip_requirements.txt
pip install imageio scikit-image
mkdir -p mit_final_data                 # put the 4 downloaded files here

# --- PART 1: pipeline on data7 + walktest ---
cd pulson440
python unpack.py ../mit_final_data/orangeworks_mit_data7.prd -v --keep_clutter
mv orangeworks_mit_data7.pkl ../mit_final_data/

cd ../mocap
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

cd ../backprojection
python backprojection.py run_0.pkl -2.5 2.5 0.01 -1.5 2.7 0.01 -m interp -p -s sar_img.pkl

# --- PART 2: tune the display on the ready-made scenes ---
cp ../mit_final_data/run_0_mit_example_test.pkl .
cp ../mit_final_data/run_0_GOOD_ONE.pkl .
python backprojection.py run_0_mit_example_test.pkl -2.5 2.5 0.01 -1.5 2.7 0.01 -m interp -p -s smiley_img.pkl
python backprojection.py run_0_GOOD_ONE.pkl        -2.5 2.5 0.01 -1.5 2.7 0.01 -m interp -p -s bw_img.pkl
# then edit show.py (cmap / vmin / vmax) and run: python show.py
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `platform-name: command not found` | Command broke across lines | One line, or `\` continuations |
| `Unknown option --save-data` | Same line-break issue | Same |
| `ModuleNotFoundError: numpy._core` | Mixed environments between steps | Use one venv; re-activate it |
| `ModuleNotFoundError: imageio` / `skimage` | Missing packages | `pip install imageio scikit-image` |
| Start-Bin curves float off the heatmap | Slider not aligned | Slide until curves sit on bright features |
| Velocity GUI: `End: -1` | Motion runs to the end | Window Size -> 40; or accept (-1 End is OK) |
| `IndexError: index 0 is out of bounds` | Confirmed with `Start: -1` | Adjust sliders until Start is real |
| Image all one color / washed out | Display range wrong | Set `vmin`/`vmax` by percentile (2.2) |
| Target invisible in green field | `viridis`, low contrast | `cmap='turbo'`, raise `vmin` to 85-90 |

**Harmless warnings:** `_tkinter.TclError: can't invoke "destroy"` (window closed during
shutdown), `RuntimeWarning: divide by zero in log10` (zeros -> -inf in dB, handled),
`UserWarning: Pandas requires ... numexpr` (old optional deps).
