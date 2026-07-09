# 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `NotImplementedError: ... delete this line once implemented!` | You ran code containing a TODO you haven't done | That's your assignment talking — see the TODO block right above that line |
| `ImportError` / `ModuleNotFoundError` | Packages not installed, or venv not active | `source venv/bin/activate`, then `pip install -r pip_requirements.txt` in the module folder |
| Checker: "Image is all zeros" | Not accumulating into the image | Use `+=`, not `=`, when adding scan contributions |
| Checker: "brightest pixel is ... from the nearest target" | Swapped axes or coordinates | Image is indexed `[jj, ii]` = [Y, X]; check your distance formula uses pixel minus platform for each axis |
| Checker: bright spots at ~50% | Partially right math | Compare your formula to the hint character by character; check `z_offset` is included |
| SAR image window looks blank | Contrast, not code | Drag the Min/Max sliders — the data range of real collects is huge |
| Image sim hangs at a prompt | It's waiting for you | Type `y` at `Proceed with SAR simulation of image? (y/n):` |
| Image sim is very slow | Too many scatterers | Raise `downsampling_factor` in the params file, use `-t 4` |
| `-m fourier` gives a shifted/garbage image on real data | Known limitation | The fourier method assumes the range axis starts at 0 — it's for simulated data (and glory), use `-m interp` for real collects |
| `-m shift` on real data takes forever | It's supposed to | That's the lesson — use `-m interp`, optionally `-np 4` |
| `unpack.py` output PNG is blank | Radar recorded nothing / bad collect | Check antenna connections; re-run `control.py -q`; tell a TA |
| `calibration_auto.py` alignment is garbage | Noisy collect or bad reflector choice | Try the other reflector (prompt 1 vs 2), adjust `--sigma`, or fall back to `calibration_manual.py` |
| Stuck > 20 minutes | — | Ask. Radar time is scarcer than TA time. |
