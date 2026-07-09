# 3. Pipeline TODOs

Every tool you personally run in the data pipeline has a small piece for you to write,
marked `STUDENT TODO (PIPELINE)` in the code. They're short — the point is that when
you run the pipeline on your flight data, it's running on *your* code the whole way.

| File | What you write | Size | Same idea as |
|---|---|---|---|
| `mocap/utils.py` → `distance_to_object` | Distance from every drone position to a reflector | 1 line | Backprojection Part 1, Step 4 |
| `mocap/utils.py` → `distances_to_bin_indices` | Nearest range bin for each distance | 2 lines | Backprojection Part 1, Step 5 |
| `pulson440/unpack.py` | Time-of-flight → range-bin axis (how radar measures distance) | 4 lines | — |
| `pulson440/control.py` | The radar session startup sequence | 3 lines | — |

Do them in that order — the two utils functions are concepts you already implemented
in Part 1.

## Testing them (no radar needed)

Each TODO block includes a quick test. From the module's folder, in a Python shell:

```python
# mocap/
>>> import numpy as np
>>> from utils import distance_to_object, distances_to_bin_indices
>>> distance_to_object(np.array([[0, 0, 0]]), np.array([3, 4, 0]))
array([5.])
>>> distances_to_bin_indices(np.array([0.0, 1.0, 2.0]), np.array([1.1]))
array([1])
```

`unpack.py` has an in-code sanity check: with the default radar config, the bin spacing
`drange_bins` should come out to about **9 mm**. `control.py` can only truly run against
the radar — a TA will review it before collection day.

## Why these must be done before collection day

The pipeline tools call these functions. If they still `raise NotImplementedError`,
**the pipeline will crash on your real flight data** — with everyone waiting on you.
