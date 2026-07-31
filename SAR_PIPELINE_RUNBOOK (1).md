# SAR Backprojection Pipeline — Handoff Run Sheet

Full chain: **unpack → process → calibrate → backproject.**

---

## How to use this sheet

Anything in **angle brackets** — like `<RADAR_PKL>` or `<MOCAP_CSV>` — is a
**placeholder you replace with your own filename or value**, brackets included.
Delete the `<>` and type your actual file name in its place.

**Example.** If your radar pickle is named `mydata.pkl` and your mocap CSV is
`walk3.csv`, then this line from step 2:

```bash
    ../pulson440/<RADAR_PKL> \
    ../pulson440/<MOCAP_CSV> \
```

becomes:

```bash
    ../pulson440/mydata.pkl \
    ../pulson440/walk3.csv \
```

Rules:
- Replace **every** `<...>` in a command before running it — the shell won't do it for you.
- **Quote** any path with parentheses or spaces: `"../pulson440/walk (3).csv"`.
- Tab-complete filenames instead of typing them, to avoid typos.
- The **Example** column in the table below shows a real value for each placeholder.

---

## Per-run values (fill these in)

| Placeholder | What it is | Example |
|---|---|---|
| `<RADAR_PRD>` | Raw radar file | `sar_26_images_30_242.prd` |
| `<RADAR_PKL>` | Unpacked radar pickle | `sar_26_images_30_242.pkl` |
| `<MOCAP_CSV>` | OptiTrack export (quote if `()`) | `"SyracuseSAR(walking)_002.csv"` |
| `<MOCAP_PKL>` | Processed mocap pickle (from step 2) | `"SyracuseSAR(walking)_002.pkl"` |
| `<PLATFORM>` | Radar/drone rigid-body name in CSV | `Drone` / `radar` / `RADAR` |
| `<CORNER_R>` | Right reflector name | `Cal2` |
| `<CORNER_L>` | Left reflector name | `Cal1` |
| `<RUN_NAME>` | Calibration output name | `run_0` |
| `<XMIN> <XMAX> <XRES>` | X grid (m) | `-4 4 0.02` |
| `<YMIN> <YMAX> <YRES>` | Y grid (m) | `-4 4 0.02` |

Asset names change every capture — verify before step 2 (see bottom section).

---

## 0. Activate env (once per terminal)

```bash
cd ~/Downloads/ORANGE_SAR/mocap
source ../pulson440/sar_venv/bin/activate
```

---

## 1. Unpack radar

```bash
cd ~/Downloads/ORANGE_SAR/pulson440
python unpack.py <RADAR_PRD> -v
```

CHANGE:
- Add `--keep_clutter` to keep static returns; omit to remove them (omit for moving targets).
- If `.prd` is elsewhere: prefix its path, then `mv <RADAR_PKL> ../<folder>/`.
- If `.pkl` came pre-made from MIT (keys `data`/`headers`): convert it first — see bottom.

---

## 2. Process

```bash
cd ~/Downloads/ORANGE_SAR/mocap
python data_processor.py \
    ../pulson440/<RADAR_PKL> \
    ../pulson440/<MOCAP_CSV> \
    --platform-name <PLATFORM> \
    --corner-right-name <CORNER_R> \
    --corner-left-name <CORNER_L> \
    --save-plots --save-data
```

PROMPTS:
- `swap to (z, x, y)?` → **y**
- close the trajectory plots
- `proceed with radar processing?` → **y**
- RTI plot: slide **start Bin** onto the returns → **Confirm**

OUT: writes `<MOCAP_PKL>` into `mocap/`.

---

## 3. Calibrate

```bash
python calibration_auto.py \
    ../pulson440/<RADAR_PKL> \
    <MOCAP_PKL> \
    --sigma 0.3 --save-data --output-name <RUN_NAME>
```

CHANGE / PROMPTS:
- `Which reflector? (1 or 2)` → try **1**; if image is poor, re-run with **2**.
- close first verification plot
- wait through X-axis movement plot — **do NOT close/kill it**
- velocity GUI: leave sliders default → **Confirm**
  (title `End` must show a real frame, not `-1 / 0.00 s`; if it does, lower the threshold)
- close the calibration-verification RTI

CHANGE (optional): `--sigma 0.5` or `0.2` if alignment is poor.

OUT: writes `<RUN_NAME>.pkl` into `backprojection/`. **Requires `--save-data` or nothing saves.**

---

## 4. Backproject

```bash
cd ../backprojection
python backprojection.py <RUN_NAME>.pkl \
    <XMIN> <XMAX> <XRES> \
    <YMIN> <YMAX> <YRES> \
    -m interp -p
```

CHANGE:
- `-m interp` fast (default) · `-m shift` slow check · `-m fourier` sim data only
- `-z <H>` image-plane height (m), default 0 — set to reflector height if defocused
- `-s image.pkl` to save the image
- grid: center `<XMIN..YMAX>` on the reflectors; shrink + lower `<XRES>/<YRES>` (e.g. `0.01`) for a sharper final
- in the window: drag **Min** up to suppress background

---

## Find asset names (before step 2)

```bash
python3 -c "
import pandas as pd, numpy as np
csv = pd.read_csv('../pulson440/<MOCAP_CSV>', skiprows=3, low_memory=False)
df = csv.iloc[1:]
df.columns = [f'{df.columns[i]}_{df.iloc[0,i]}_{df.iloc[1,i]}' for i in range(len(df.columns))]
data = df.iloc[3:].reset_index(drop=True)
bases = sorted(set(c[:-len('.4_Position_X')] for c in df.columns if c.endswith('.4_Position_X')))
for b in bases:
    cols=[f'{b}.4_Position_X',f'{b}.5_Position_Y',f'{b}.6_Position_Z']
    if all(c in data.columns for c in cols):
        sub=data[cols].apply(pd.to_numeric,errors='coerce').dropna()
        tr=(sub.max()-sub.min()).values if len(sub) else [0,0,0]
        print(f'{b:14s} valid={len(sub):5d} travel=({tr[0]:.2f},{tr[1]:.2f},{tr[2]:.2f}) {\"MOVES\" if max(tr)>0.5 else \"still\"}')
"
```

- **MOVES** = `<PLATFORM>`
- two **still** `Cal` assets = `<CORNER_L>` / `<CORNER_R>`
- ignore `Unlabeled ####` and default `RigidBody`

---

## Convert MIT-format pickle (only if keys are `data`/`headers`)

```bash
cd ~/Downloads/ORANGE_SAR/pulson440
python3 << 'PYEOF'
import pickle, numpy as np, sys
from pathlib import Path
sys.path.insert(0, Path('..').resolve().as_posix())
from common.constants import SPEED_OF_LIGHT
from pulson440.constants import T_BIN, DT_0

SRC = "<MIT_PKL>"          # e.g. practice_data(1).pkl
OUT = "<CONVERTED_PKL>"    # e.g. practice_converted.pkl

d = pickle.load(open(SRC, "rb"))
data = np.array(d["data"], dtype=float)
headers = d["headers"]
timestamps = np.array([h["timestamp"] for h in headers], float)
h0 = headers[0]; n = int(h0["num_samples_total"]); scan_start = float(h0["scan_start"])
start_range = SPEED_OF_LIGHT * (scan_start*1e-12 - (DT_0*1e-9)/2)
drange = SPEED_OF_LIGHT * (T_BIN*1e-9) / 2
range_bins = start_range + drange * np.arange(n)
print("drange_bins (expect ~0.009):", round(drange, 6))
pickle.dump({"timestamps": timestamps, "range_bins": range_bins, "scan_data": data}, open(OUT, "wb"))
print("wrote", OUT)
PYEOF
```

Use `<CONVERTED_PKL>` in place of `<RADAR_PKL>` from step 2 on.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `No data found after processing CSV` | Unlabeled-marker cloud; use patched `data_processor.py` (drops rows only on platform cols). |
| `Platform columns not found: X...` | Wrong asset name — run "Find asset names". |
| `bash: syntax error near '('` | Quote CSV paths with `()`. |
| `~` path "does not exist" | `~` doesn't expand in quotes — use full `/home/...`. |
| `KeyError: ['timestamps','range_bins','scan_data']` | MIT-format pickle — convert it. |
| `run_*.pkl does not exist` | Missing `--save-data` on calibration — re-run with it. |
| Image = arcs / no focused points | Aperture too short/gappy or clutter-dominated. Longer straighter walk, keep radar markers visible, try `-z` at reflector height, tighten grid on reflectors, unpack without `--keep_clutter`. |

---

## Sanity check calibrated file (optional)

```bash
python3 -c "
import pickle, numpy as np
d = pickle.load(open('<RUN_NAME>.pkl','rb'))
for k in d: print(k, np.array(d[k]).shape)
p = np.array(d['platform_pos'])
print('platform travel:', (p.max(0)-p.min(0)).round(3))
"
```

`platform travel` should be a few meters on one axis. `[0 0 0]` = timestamps didn't align; re-check calibration.
