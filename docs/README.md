# UAS-SAR Course Documentation

Follow these guides **in order**. Each one tells you exactly what to type and what you
should see.

| # | Guide | What you'll do |
|---|-------|----------------|
| 0 | [Setup](00_setup.md) | Get the code running on your machine |
| 1 | [The Backprojection Assignment](01_backprojection_assignment.md) | Write the SAR imaging algorithm (Parts 1–3) |
| 2 | [Testing with Simulated Data](02_testing_with_simulated_data.md) | Prove your algorithm works on simulated radar data |
| 3 | [Pipeline TODOs](03_pipeline_todos.md) | Write your small pieces of the data pipeline tools |
| 4 | [Collection Day](04_collection_day.md) | Operate the PulsON 440 radar |
| 5 | [Real Data Pipeline](05_real_data_pipeline.md) | Turn your flight data into a SAR image |
| 6 | [Troubleshooting](06_troubleshooting.md) | When things go wrong |

## The One Rule

> **Your backprojection code must pass on simulated data before you touch the PulsON 440.**

The simulator gives you radar data where the right answer is *known*. Real radar data is
noisy, misaligned, and unforgiving — if your image looks wrong on real data, you need to
already know your algorithm isn't the problem. Guides 1–3 are your ticket to guide 4.

```
 Guide 1              Guide 2                 Guide 3            Guides 4-5
 write the    ──►     prove it works   ──►    write your   ──►   fly, collect,
 algorithm            on simulation           pipeline bits      image FOR REAL
                      (checker PASSED)
```
