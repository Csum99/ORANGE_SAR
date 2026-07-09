# 4. Collection Day — Operating the PulsON 440

**Prerequisite: you passed [the gate](02_testing_with_simulated_data.md).**

The radar is controlled with `pulson440/control.py` (which starts up using the session
sequence YOU wrote).

```bash
cd pulson440
python control.py [mode] [options] [output_file]
```

## Modes (pick exactly one)

| Flag | Mode | Use when |
|---|---|---|
| `-q` | Quick look | Sanity check — is the radar alive and seeing returns? |
| `-c` | Collect | The real thing — record scans to a file |
| `-v` | Visual | Stream to a realtime display (staff-run) |

## Options

| Flag | Meaning |
|---|---|
| `-n N` | Number of scans to collect (omit for continuous until Ctrl-C) |
| `-i I` | Interval between scans |
| `-s FILE` | Settings file (default: `settings.yml` — TAs manage this) |
| `--host_ip / --radar_ip / ...` | Network overrides (defaults are correct for course hardware) |

## Typical collection day sequence

```bash
# 1. Sanity check — expect log lines showing a connection and a scan
python control.py -q

# 2. Real collection: name your file with your team and run number!
python control.py -c -n 1000 team3_run1.prd

# 3. IMMEDIATELY check what you recorded (uses your unpack.py ranging math):
python unpack.py team3_run1.prd -v --keep_clutter
python display_rti.py team3_run1.pkl
```

The RTI (Range-Time Intensity) plot from step 3 is your "did we get good data?" check —
**do it before the drone lands for the day**. You should see bright streaks that move in
range as the drone moves. If it's blank or garbage, tell a TA immediately and re-fly;
five minutes of checking saves a wasted flight.

Ctrl-C during a collect stops the radar cleanly (the code handles it).

## Etiquette

- One team commands the radar at a time.
- Never edit `settings.yml` without a TA.
- Write down for each run: filename, what was in the scene, anything weird.
