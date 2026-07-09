# UAS-SAR Course Code (2026 Student Edition)

Software for the UAS-SAR course: fly a drone with an ultra-wideband radar, collect data,
and turn it into synthetic aperture radar (SAR) images.

Based on the MIT BWSI UAS-SAR gold standard code (MIT License — see LICENSE), adapted
into a student assignment edition.

## Where to start

**Read the [course documentation](docs/README.md)** — it walks you through everything
in order, with exact commands: setup, the backprojection assignment, testing on
simulated data, and the real-data pipeline.

**The one rule:** your backprojection must pass on simulated data
(`python check_backprojection.py`) before you touch the PulsON 440 radar.

## Modules

| Folder | What it is | Status |
|-------------------|---------------------------------------------------------|------------------|
| `backprojection/` | SAR image formation + data simulator | **YOU implement the algorithms** |
| `pulson440/` | PulsON 440 radar control, unpacking, realtime displays | given, working |
| `mocap/` | Motion-capture + radar preprocessing and time alignment | given, working |
| `common/` | Shared helper functions and constants | given, working |

Each module has its own README and `pip_requirements.txt`.
