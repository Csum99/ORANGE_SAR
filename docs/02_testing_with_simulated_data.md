# 2. Testing with Simulated Data

**This is the gate before the radar.** `simulate_sar_data.py` produces exactly the same
data format the real pipeline produces — but with targets at positions *you chose*, so
you know what the image should look like.

## How to run the simulator

```bash
cd backprojection
python simulate_sar_data.py <params.yml> <output.pkl> [options]
```

| Argument / flag | Meaning |
|---|---|
| `params.yml` | Simulation parameters file (see anatomy below) |
| `output.pkl` | Where to save the simulated data |
| `-p` | Show a progress bar |
| `-t N` | Use N threads (image sims are slow; use 4+) |
| `-r` | Return data instead of only saving (for calling from Python) |

For image simulations it will ask `Proceed with SAR simulation of image? (y/n):` — type `y`.

## Level 1: point targets (start here)

```bash
python simulate_sar_data.py params/scatterers_example.yml points.pkl -p
python backprojection.py points.pkl -8 8 0.1 -8 8 0.1 -m shift -p
```

You should see 5 bright dots in an X pattern (the positions listed under
`scatterer_pos` in the params file). Then run the same data through `-m interp` and
confirm the image looks identical but computes far faster.

## Level 2: image targets

The simulator can turn a picture into a field of thousands of tiny radar targets:

```bash
python simulate_sar_data.py params/monalisa.yml monalisa.pkl -p -t 4
python backprojection.py monalisa.pkl -8 8 0.05 -8 8 0.05 -m interp -p
```

If the Mona Lisa emerges from your radar math, your backprojection works. (Image sims
take a while — that's what `-t 4` and the progress bar are for. Use `-m interp`, not
shift, unless you enjoy waiting.)

## Level 3: bring your own image

1. Drop a PNG/JPG into `backprojection/images/`.
2. Copy `params/monalisa.yml` to `params/myimage.yml` and change `source_image` to your
   file. Raise `downsampling_factor` if the sim is too slow.
3. Simulate and reconstruct it, same commands as Level 2.

## Anatomy of a params file

```yaml
sim_type: 'point'            # 'point', 'image', or 'image_misaligned'
center_freq: 4062500000      # radar carrier (Hz) — matches the real PulsON 440
bandwidth: 2437500000        # (Hz) — sets range resolution
scan_rate: 25                # pulses per second
duration: 8                  # flight time (s) — more time = bigger aperture = sharper
range_min: 3                 # (m) closest range recorded
range_max: 50                # (m) farthest range recorded
platform_init_pos: [-20, -15, 5]   # drone start [X, Y, Z] (m)
platform_vel: [5, 0, 0]            # drone velocity [X, Y, Z] (m/s)
scatterer_pos:               # point targets [X, Y, Z] (point mode)
  - [-5, -5, 0]
scatterer_RCS: [10000]       # how strongly each target reflects
source_image: './images/monalisa.jpg'   # (image mode)
downsampling_factor: 20      # bigger = fewer scatterers = faster sim
add_noise: False             # turn on to make life realistic
noise_magnitude: 4
```

Experiments worth doing: shorten `duration` (image gets blurrier — why?), turn on
`add_noise`, move the flight path closer/farther.

## The gate, explicitly

Before collection day you must be able to show a TA:

- [ ] `python check_backprojection.py` → shift **PASSED**, interp **PASSED**
- [ ] A reconstructed image sim (Level 2 or 3)
- [ ] Your Pipeline TODOs done (next guide)
